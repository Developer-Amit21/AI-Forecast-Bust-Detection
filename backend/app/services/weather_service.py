"""
Weather Service: Core business logic coordinator for NWP Bust Detection.
Caches simulated scenarios, manages model inference, runs XAI queries,
and formats data for REST API endpoints.
"""
import torch
import numpy as np
import xarray as xr
from pathlib import Path
from typing import Dict, List, Any, Optional

from backend.app.core.config import settings
from backend.ml.data_generator import WeatherDataGenerator
from backend.ml.model import SpatioTemporalBustUNet, build_model
from backend.ml.explainability import WeatherXAI
from backend.app.services.polygon_generator import generate_alert_polygons, get_subdivision_name
from backend.app.schemas.forecast import (
    ForecastSummaryResponse,
    DailyRiskSummary,
    GridForecastResponse,
    ExplainForecastResponse,
    VariableAttribution,
    Coordinate,
    ScenarioInfo
)

class WeatherService:
    _instance = None

    def __init__(self):
        self.device = torch.device("cpu")
        self.generator = WeatherDataGenerator(seed=42)
        self.scenarios_cache: Dict[str, xr.Dataset] = {}
        self.scenarios_meta: Dict[str, Dict] = {}
        
        # Load or initialize model
        self.model = build_model(self.device)
        self._init_model_weights()
        self.xai = WeatherXAI(self.model, self.device)
        
        # Preload standard operational scenarios
        self._preload_scenarios()

    def _init_model_weights(self):
        if settings.MODEL_WEIGHTS_PATH.exists():
            try:
                state_dict = torch.load(settings.MODEL_WEIGHTS_PATH, map_location=self.device, weights_only=True)
                self.model.load_state_dict(state_dict)
                print(f"[WeatherService] Loaded existing model weights from {settings.MODEL_WEIGHTS_PATH}")
            except Exception as e:
                print(f"[WeatherService] Could not load weights ({e}), training inline...")
                self._quick_train()
        else:
            print("[WeatherService] No checkpoint found. Running quick training...")
            self._quick_train()
        self.model.eval()

    def _quick_train(self):
        from backend.ml.train import train_model
        train_model(epochs=6, batch_size=8, save_path=settings.MODEL_WEIGHTS_PATH, device=self.device)
        self.model.load_state_dict(torch.load(settings.MODEL_WEIGHTS_PATH, map_location=self.device, weights_only=True))

    def _preload_scenarios(self):
        for sc in settings.SCENARIOS.keys():
            nc_file = settings.DATA_DIR / f"scenario_{sc}.nc"
            if nc_file.exists():
                try:
                    ds = xr.open_dataset(nc_file)
                    self.scenarios_cache[sc] = ds
                    self.scenarios_meta[sc] = {
                        "scenario": sc,
                        "description": ds.attrs.get("description", ""),
                        "primary_driver": ds.attrs.get("primary_driver", "")
                    }
                    continue
                except Exception:
                    pass
            ds, meta = self.generator.simulate_scenario(sc)
            self.scenarios_cache[sc] = ds
            self.scenarios_meta[sc] = meta
            try:
                ds.to_netcdf(nc_file, engine="netcdf4")
            except Exception:
                pass

    def get_available_scenarios(self) -> List[ScenarioInfo]:
        return [
            ScenarioInfo(
                id=sc,
                name=settings.SCENARIOS[sc],
                description=self.scenarios_meta.get(sc, {}).get("description", ""),
                primary_driver=self.scenarios_meta.get(sc, {}).get("primary_driver", "")
            )
            for sc in settings.SCENARIOS.keys()
        ]

    def _prepare_tensor(self, ds: xr.Dataset, lead_day: int) -> torch.Tensor:
        """Extracts and normalizes the 5 channels for a lead day."""
        day_idx = lead_day - 1
        ch_arrays = []
        for ch in settings.CHANNELS:
            raw = ds[f"forecast_{ch}"].values[day_idx]
            mean = settings.NORM_PARAMS[ch]["mean"]
            std = settings.NORM_PARAMS[ch]["std"]
            norm = (raw - mean) / std
            ch_arrays.append(norm)
        x = np.stack(ch_arrays, axis=0) # (5, H, W)
        return torch.tensor(x, dtype=torch.float32).unsqueeze(0).to(self.device)

    def run_inference(self, scenario: str, lead_day: int) -> Dict[str, np.ndarray]:
        if scenario not in self.scenarios_cache:
            scenario = "western_disturbance"
        ds = self.scenarios_cache[scenario]
        day_idx = lead_day - 1
        
        x_tensor = self._prepare_tensor(ds, lead_day)
        lead_t = torch.tensor([lead_day], device=self.device)
        
        with torch.no_grad():
            conf_pred, bust_pred = self.model(x_tensor, lead_t)
            
        conf_grid = conf_pred.squeeze().cpu().numpy() # (H, W)
        bust_grid = bust_pred.squeeze().cpu().numpy() # (H, W)
        
        # Raw forecast fields for weather context
        raw_fields = {ch: ds[f"forecast_{ch}"].values[day_idx] for ch in settings.CHANNELS}
        
        return {
            "confidence": conf_grid,
            "bust_prob": bust_grid,
            "raw": raw_fields,
            "dataset": ds
        }

    def get_summary(self, scenario: str = "western_disturbance") -> ForecastSummaryResponse:
        if scenario not in self.scenarios_cache:
            scenario = "western_disturbance"
        meta = self.scenarios_meta.get(scenario, {})
        
        timeline: List[DailyRiskSummary] = []
        peak_day = 1
        max_bust_overall = 0.0
        conf_sum = 0.0
        total_alerts = 0
        critical_subdivisions_set = set()
        
        for lead in range(1, 11):
            inf = self.run_inference(scenario, lead)
            conf_grid = inf["confidence"]
            bust_grid = inf["bust_prob"]
            
            mean_c = float(np.mean(conf_grid))
            max_b = float(np.max(bust_grid))
            high_bust_pct = float(np.mean(bust_grid >= settings.HIGH_BUST_RISK_THRESHOLD) * 100.0)
            
            # Count alerts
            alert_fc = generate_alert_polygons(bust_grid, conf_grid, lead, threshold=0.50)
            n_alerts = len(alert_fc.features)
            total_alerts += n_alerts
            
            for feat in alert_fc.features:
                if feat.properties.severity in ["CRITICAL", "WARNING"]:
                    critical_subdivisions_set.add(feat.properties.subdivision)
                    
            if max_b > max_bust_overall:
                max_bust_overall = max_b
                peak_day = lead
                
            conf_sum += mean_c
            
            threat = "Nominal Ensemble Variance"
            if max_b >= 0.70:
                threat = f"Severe Bust: {meta.get('primary_driver', 'Synoptic Divergence')}"
            elif max_b >= 0.40:
                threat = "Moderate Track & Intensity Uncertainty"
                
            timeline.append(DailyRiskSummary(
                lead_day=lead,
                mean_confidence=round(mean_c, 3),
                max_bust_probability=round(max_b, 3),
                high_bust_cells_pct=round(high_bust_pct, 1),
                active_alert_zones=n_alerts,
                primary_threat=threat
            ))
            
        return ForecastSummaryResponse(
            scenario=scenario,
            scenario_description=meta.get("description", "Simulated NWP Forecast"),
            peak_risk_day=peak_day,
            mean_10day_confidence=round(conf_sum / 10.0, 3),
            total_active_alerts=total_alerts,
            critical_subdivisions=sorted(list(critical_subdivisions_set))[:6],
            timeline=timeline
        )

    def get_grid(self, scenario: str, lead_day: int) -> GridForecastResponse:
        inf = self.run_inference(scenario, lead_day)
        conf_grid = inf["confidence"]
        bust_grid = inf["bust_prob"]
        raw = inf["raw"]
        
        lats = [float(x) for x in self.generator.lats]
        lons = [float(x) for x in self.generator.lons]
        
        # Error-prone polygons
        alert_fc = generate_alert_polygons(bust_grid, conf_grid, lead_day, threshold=0.48)
        
        return GridForecastResponse(
            scenario=scenario,
            lead_day=lead_day,
            bounds={
                "lat_min": settings.LAT_MIN,
                "lat_max": settings.LAT_MAX,
                "lon_min": settings.LON_MIN,
                "lon_max": settings.LON_MAX
            },
            lats=lats,
            lons=lons,
            confidence_grid=np.round(conf_grid, 3).tolist(),
            bust_prob_grid=np.round(bust_grid, 3).tolist(),
            precip_grid=np.round(raw["precip"], 1).tolist(),
            mslp_grid=np.round(raw["mslp"], 1).tolist(),
            z500_grid=np.round(raw["z500"], 1).tolist(),
            vort850_grid=np.round(raw["vort850"], 2).tolist(),
            pwat_grid=np.round(raw["pwat"], 1).tolist(),
            alert_zones=alert_fc
        )

    def explain_coordinate(self, scenario: str, lead_day: int, lat: float, lon: float) -> ExplainForecastResponse:
        if scenario not in self.scenarios_cache:
            scenario = "western_disturbance"
        ds = self.scenarios_cache[scenario]
        
        # Find nearest grid indices
        lats = self.generator.lats
        lons = self.generator.lons
        lat_idx = int(np.argmin(np.abs(lats - lat)))
        lon_idx = int(np.argmin(np.abs(lons - lon)))
        
        # Forward pass
        x_tensor = self._prepare_tensor(ds, lead_day)
        lead_t = torch.tensor([lead_day], device=self.device)
        with torch.no_grad():
            conf_pred, bust_pred = self.model(x_tensor, lead_t)
            
        conf_val = float(conf_pred[0, 0, lat_idx, lon_idx].cpu().numpy())
        bust_val = float(bust_pred[0, 0, lat_idx, lon_idx].cpu().numpy())
        
        # Attribution calculation via XAI
        xai_result = self.xai.attribute_coordinate(
            x_tensor=x_tensor,
            lead_day=lead_day,
            lat_idx=lat_idx,
            lon_idx=lon_idx,
            target_head="bust" if bust_val >= 0.35 else "confidence",
            method="integrated_gradients",
            n_steps=12
        )
        
        subdiv = get_subdivision_name(lat, lon)
        
        attr_dict = {
            ch: VariableAttribution(
                name=info["name"],
                percentage=info["percentage"],
                importance_score=info["importance_score"]
            )
            for ch, info in xai_result["variable_attributions"].items()
        }
        
        return ExplainForecastResponse(
            lead_day=lead_day,
            coordinate=Coordinate(lat=round(float(lats[lat_idx]), 2), lon=round(float(lons[lon_idx]), 2)),
            subdivision=subdiv,
            confidence=round(conf_val, 3),
            bust_probability=round(bust_val, 3),
            primary_driver=xai_result["primary_driver"],
            primary_driver_pct=xai_result["primary_driver_pct"],
            secondary_driver=xai_result["secondary_driver"],
            secondary_driver_pct=xai_result["secondary_driver_pct"],
            meteorological_briefing=xai_result["meteorological_briefing"],
            variable_attributions=attr_dict,
            spatial_saliency=xai_result["spatial_saliency"]
        )

# Global singleton
weather_service = WeatherService()
