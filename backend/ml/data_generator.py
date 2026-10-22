"""
Synthetic Meteorological Data Generator for Regional NWP Forecast Busts.
Simulates 10-day medium-range gridded forecasts and ground-truth observations
over the South Asian / Indian domain (5°N–38°N, 65°E–100°E).
"""
import numpy as np
import xarray as xr
from pathlib import Path
from typing import Dict, Tuple, Optional

from backend.app.core.config import settings

class WeatherDataGenerator:
    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)
        self.lats = np.arange(settings.LAT_MIN, settings.LAT_MAX + 0.1, settings.RESOLUTION_DEG)
        self.lons = np.arange(settings.LON_MIN, settings.LON_MAX + 0.1, settings.RESOLUTION_DEG)
        self.n_lat = len(self.lats)
        self.n_lon = len(self.lons)
        self.lead_days = np.arange(settings.MIN_LEAD_DAY, settings.MAX_LEAD_DAY + 1)
        self.n_leads = len(self.lead_days)
        
        # Precompute coordinate meshgrids
        self.lon_grid, self.lat_grid = np.meshgrid(self.lons, self.lats)

    def _generate_synoptic_base(self) -> Dict[str, np.ndarray]:
        """
        Generates realistic climatological baseline fields for the Indian Summer Monsoon.
        """
        # MSLP: Heat low over Pakistan/NW India (28°N, 70°E) ~ 998 hPa, Bay of Bengal ~ 1008 hPa, South Indian Ocean ~ 1014 hPa
        dist_heat_low = np.sqrt((self.lat_grid - 28.0)**2 + (self.lon_grid - 70.0)**2)
        mslp = 1012.0 - 14.0 * np.exp(- (dist_heat_low / 12.0)**2) + 0.15 * (15.0 - self.lat_grid)
        
        # Z500: Subtropical ridge around 22°N (~5880 gpm), dropping to mid-latitude westerlies at 35°N (~5640 gpm)
        z500 = 5880.0 - 7.5 * np.maximum(0, self.lat_grid - 20.0)**1.5 + 2.0 * np.sin(self.lon_grid * 0.1)
        
        # PWAT: Moist tongue along Bay of Bengal & Arabian sea (50-65 mm), dry over Tibetan plateau (<20 mm)
        pwat = 55.0 * np.exp(- np.maximum(0, self.lat_grid - 22.0) / 10.0)
        # Coastal & sea moisture enhancement
        sea_mask = (self.lat_grid < 20.0) | ((self.lon_grid > 82.0) & (self.lat_grid < 26.0))
        pwat = np.where(sea_mask, pwat + 10.0, pwat)
        pwat = np.clip(pwat, 12.0, 75.0)
        
        # VORT850: Positive cyclonic vorticity along monsoon trough (20-25°N)
        dist_trough = np.abs(self.lat_grid - 22.5 - 0.1 * (self.lon_grid - 80.0))
        vort850 = 8.0 * np.exp(- (dist_trough / 3.0)**2) - 2.0
        
        # PRECIP: Orographic Western Ghats (73-75°E, 10-18°N) and NE India / Monsoon belt
        wg_mask = (self.lon_grid >= 73.0) & (self.lon_grid <= 75.5) & (self.lat_grid >= 9.0) & (self.lat_grid <= 19.0)
        ne_mask = (self.lon_grid >= 88.0) & (self.lon_grid <= 96.0) & (self.lat_grid >= 24.0) & (self.lat_grid <= 28.0)
        
        precip = 10.0 * np.exp(- (dist_trough / 4.0)**2)
        precip = np.where(wg_mask, precip + 55.0, precip)
        precip = np.where(ne_mask, precip + 40.0, precip)
        precip = np.clip(precip, 0.0, 200.0)
        
        return {
            "pwat": pwat,
            "z500": z500,
            "mslp": mslp,
            "vort850": vort850,
            "precip": precip
        }

    def simulate_scenario(self, scenario_type: str = "western_disturbance") -> Tuple[xr.Dataset, Dict]:
        """
        Simulates 10-day forecast evolution and corresponding verification truth.
        Injects specific meteorological bust patterns.
        """
        base = self._generate_synoptic_base()
        
        forecast_data = {var: np.zeros((self.n_leads, self.n_lat, self.n_lon)) for var in settings.CHANNELS}
        truth_data = {var: np.zeros((self.n_leads, self.n_lat, self.n_lon)) for var in settings.CHANNELS}
        
        # Baseline synoptic field propagation across 10 lead days
        for day_idx, lead in enumerate(self.lead_days):
            day_factor = lead / 10.0
            smooth_noise_f = self.rng.normal(0, 0.5 * lead, (self.n_lat, self.n_lon))
            smooth_noise_t = self.rng.normal(0, 0.5 * lead, (self.n_lat, self.n_lon))
            
            for var in settings.CHANNELS:
                forecast_data[var][day_idx] = base[var] + smooth_noise_f * 0.2
                truth_data[var][day_idx] = base[var] + smooth_noise_t * 0.2

        metadata = {"scenario": scenario_type, "bust_regions": []}

        # Inject realistic bust dynamics
        if scenario_type == "western_disturbance":
            # Mid-latitude upper trough enters NW India (Day 3-7).
            # Model predicts shallow, fast-moving system; Reality produces deep cut-off low with heavy precipitation.
            for day_idx, lead in enumerate(self.lead_days):
                if lead >= 3:
                    intensity = min(1.0, (lead - 2) / 3.0)
                    center_lat = 31.0 - 0.4 * (lead - 3)
                    center_lon = 72.0 + 1.2 * (lead - 3)
                    dist = np.sqrt((self.lat_grid - center_lat)**2 + (self.lon_grid - center_lon)**2)
                    core = np.exp(- (dist / 4.0)**2)
                    
                    # Reality: Deep upper trough, intense rainfall and low pressure
                    truth_data["z500"][day_idx] -= 140.0 * intensity * core
                    truth_data["mslp"][day_idx] -= 12.0 * intensity * core
                    truth_data["vort850"][day_idx] += 16.0 * intensity * core
                    truth_data["pwat"][day_idx] += 22.0 * intensity * core
                    truth_data["precip"][day_idx] += 95.0 * intensity * core
                    
                    # Forecast: Underpredicts depth and misplaces core eastward
                    f_lon = center_lon + 3.5  # 350km phase error
                    dist_f = np.sqrt((self.lat_grid - center_lat)**2 + (self.lon_grid - f_lon)**2)
                    core_f = np.exp(- (dist_f / 5.0)**2)
                    forecast_data["z500"][day_idx] -= 45.0 * intensity * core_f
                    forecast_data["mslp"][day_idx] -= 3.0 * intensity * core_f
                    forecast_data["precip"][day_idx] += 15.0 * intensity * core_f
            
            metadata["description"] = "Intense Western Disturbance trough deepening across Northwest India (Day 4–8) severely underpredicted in precipitation and vorticity."
            metadata["primary_driver"] = "500 hPa Geopotential Height mid-latitude trough phase lag and cyclonic vorticity shear"
            metadata["bust_regions"] = ["Punjab", "Haryana", "Himachal Pradesh", "Uttarakhand", "West Uttar Pradesh"]

        elif scenario_type == "monsoon_depression":
            # Monsoon depression forms in Head Bay of Bengal (Day 1) and tracks WNW across Central India.
            # Forecast erroneously recurves the storm towards Bangladesh/Myanmar.
            for day_idx, lead in enumerate(self.lead_days):
                # Actual trajectory: from (20°N, 89°E) towards (23°N, 75°E)
                t_lat = 20.0 + 0.4 * lead
                t_lon = 89.0 - 1.8 * lead
                dist_t = np.sqrt((self.lat_grid - t_lat)**2 + (self.lon_grid - t_lon)**2)
                core_t = np.exp(- (dist_t / 3.5)**2)
                
                truth_data["mslp"][day_idx] -= 15.0 * core_t
                truth_data["vort850"][day_idx] += 18.0 * core_t
                truth_data["pwat"][day_idx] += 28.0 * core_t
                truth_data["precip"][day_idx] += 120.0 * core_t
                
                # Forecast trajectory: recurves north-east towards 23°N, 91°E by Day 4
                f_lat = 20.0 + 0.8 * lead
                f_lon = 89.0 + 0.6 * lead
                dist_f = np.sqrt((self.lat_grid - f_lat)**2 + (self.lon_grid - f_lon)**2)
                core_f = np.exp(- (dist_f / 3.5)**2)
                
                forecast_data["mslp"][day_idx] -= 12.0 * core_f
                forecast_data["vort850"][day_idx] += 14.0 * core_f
                forecast_data["pwat"][day_idx] += 20.0 * core_f
                forecast_data["precip"][day_idx] += 80.0 * core_f

            metadata["description"] = "Bay of Bengal Monsoon Depression track bifurcation: model predicted NE recurvature, ground truth tracked WNW into Central India."
            metadata["primary_driver"] = "850 hPa Wind Vorticity steering track divergence and MSLP low-pressure displacement"
            metadata["bust_regions"] = ["Odisha", "Chhattisgarh", "Vidarbha", "East Madhya Pradesh"]

        elif scenario_type == "monsoon_break":
            # Abrupt monsoon break: Trough moves to Himalayan foothills (Day 4-10)
            # Central India dries out completely; Foothills flood. Forecast predicts ongoing rain in MP/Maharashtra.
            for day_idx, lead in enumerate(self.lead_days):
                if lead >= 4:
                    prog = (lead - 3) / 7.0
                    # Foothills heavy rain injection
                    foothill_mask = (self.lat_grid >= 26.5) & (self.lat_grid <= 29.5) & (self.lon_grid >= 78.0) & (self.lon_grid <= 89.0)
                    central_mask = (self.lat_grid >= 18.0) & (self.lat_grid <= 24.0) & (self.lon_grid >= 74.0) & (self.lon_grid <= 84.0)
                    
                    truth_data["precip"][day_idx] = np.where(foothill_mask, truth_data["precip"][day_idx] + 110.0 * prog, truth_data["precip"][day_idx])
                    truth_data["precip"][day_idx] = np.where(central_mask, np.maximum(0.0, truth_data["precip"][day_idx] * 0.1), truth_data["precip"][day_idx])
                    
                    # Forecast keeps raining in Central India, underestimates foothills
                    forecast_data["precip"][day_idx] = np.where(central_mask, forecast_data["precip"][day_idx] + 45.0, forecast_data["precip"][day_idx])
                    forecast_data["precip"][day_idx] = np.where(foothill_mask, 20.0, forecast_data["precip"][day_idx])
            
            metadata["description"] = "Sudden Monsoon Break phase shift: Trough pinned to Himalayan foothills causing widespread Central India rainfall false alarms."
            metadata["primary_driver"] = "Mean Sea Level Pressure trough axis northward dislocation and Precipitable Water convergence collapse"
            metadata["bust_regions"] = ["Madhya Pradesh", "Maharashtra", "Bihar Foothills", "Sub-Himalayan West Bengal"]

        else: # climatology / normal
            for day_idx, lead in enumerate(self.lead_days):
                disp = lead * 0.08
                forecast_data["precip"][day_idx] += self.rng.normal(0, 3.0 * disp, (self.n_lat, self.n_lon))
            metadata["description"] = "Quiescent Active Monsoon baseline run with gradual, well-calibrated ensemble spread."
            metadata["primary_driver"] = "Normal chaotic boundary layer convective dispersion"
            metadata["bust_regions"] = []

        # Ensure positive physical bounds
        for day_idx in range(self.n_leads):
            for v in ["precip", "pwat"]:
                forecast_data[v][day_idx] = np.clip(forecast_data[v][day_idx], 0.0, 300.0)
                truth_data[v][day_idx] = np.clip(truth_data[v][day_idx], 0.0, 300.0)

        # Compute Ground-Truth Error, Bust Mask, and Confidence
        # Multi-variable standardized absolute error
        norm_errors = np.zeros((self.n_leads, self.n_lat, self.n_lon))
        for var in settings.CHANNELS:
            diff = np.abs(forecast_data[var] - truth_data[var])
            norm_errors += (diff / settings.NORM_PARAMS[var]["std"]) ** 2
        norm_errors = np.sqrt(norm_errors / len(settings.CHANNELS))
        
        # Ground-truth Bust criterion: precip error > 45mm OR overall synoptic error > 2.0 sigma
        precip_err = np.abs(forecast_data["precip"] - truth_data["precip"])
        bust_mask = ((precip_err >= settings.RAIN_BUST_THRESHOLD_MM) | (norm_errors >= 2.0)).astype(np.float32)
        
        # Confidence metric: 1.0 at 0 error, decaying smoothly as normalized error compounds
        confidence_grid = 1.0 / (1.0 + 0.65 * norm_errors)
        confidence_grid = np.clip(confidence_grid, 0.05, 0.98)

        # Build Xarray Dataset
        coords = {
            "lead_day": self.lead_days,
            "lat": self.lats,
            "lon": self.lons,
        }
        
        data_vars = {}
        for var in settings.CHANNELS:
            data_vars[f"forecast_{var}"] = (("lead_day", "lat", "lon"), forecast_data[var].astype(np.float32))
            data_vars[f"truth_{var}"] = (("lead_day", "lat", "lon"), truth_data[var].astype(np.float32))
        
        data_vars["bust_ground_truth"] = (("lead_day", "lat", "lon"), bust_mask)
        data_vars["confidence_ground_truth"] = (("lead_day", "lat", "lon"), confidence_grid.astype(np.float32))
        data_vars["norm_synoptic_error"] = (("lead_day", "lat", "lon"), norm_errors.astype(np.float32))
        
        ds = xr.Dataset(
            data_vars=data_vars,
            coords=coords,
            attrs={
                "title": "NWP Forecast Bust Simulation Dataset",
                "scenario": scenario_type,
                "domain": "South Asia (5N-38N, 65E-100E)",
                "resolution": f"{settings.RESOLUTION_DEG} deg",
                "primary_driver": metadata["primary_driver"],
                "description": metadata["description"],
            }
        )
        
        return ds, metadata

    def export_scenario_to_netcdf(self, scenario_type: str, output_path: Path) -> Path:
        """Saves a simulated scenario to NetCDF4 file."""
        ds, _ = self.simulate_scenario(scenario_type)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        ds.to_netcdf(output_path, engine="netcdf4")
        return output_path
