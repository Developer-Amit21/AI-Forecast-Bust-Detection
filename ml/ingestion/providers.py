from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {
    "forecast_initialization_time", "valid_time", "lead_day", "latitude", "longitude",
    "region_id", "region_name", "variable", "forecast_value", "model_identifier",
    "data_mode",
}

REGIONS = [
    ("WB", "West Bengal", 23.0, 88.3),
    ("OD", "Odisha", 20.5, 85.2),
    ("AS", "Assam", 26.1, 91.7),
    ("MH", "Maharashtra", 19.8, 75.7),
    ("KL", "Kerala", 10.4, 76.3),
    ("DL", "Delhi", 28.6, 77.2),
    ("RJ", "Rajasthan", 26.9, 73.0),
    ("TN", "Tamil Nadu", 11.1, 78.6),
]


class BaseWeatherDataProvider(ABC):
    """Provider contract; each implementation returns the common record schema."""

    @abstractmethod
    def load_forecasts(self) -> pd.DataFrame: ...

    @abstractmethod
    def load_observations(self) -> pd.DataFrame: ...


class SyntheticDataProvider(BaseWeatherDataProvider):
    """Deterministic development-only weather-like forecast/observation generator."""

    def __init__(self, cycles: int = 180, grid_points_per_region: int = 3, seed: int = 42,
                 start: str = "2024-01-01T00:00:00Z") -> None:
        self.cycles, self.grid_points_per_region, self.seed = cycles, grid_points_per_region, seed
        self.start = pd.Timestamp(start)
        self._full: pd.DataFrame | None = None

    def _generate(self) -> pd.DataFrame:
        if self._full is not None:
            return self._full.copy()
        rng = np.random.default_rng(self.seed)
        rows: list[dict] = []
        variables = ("precipitation", "temperature_2m", "wind_speed")
        cycles = pd.date_range(self.start, periods=self.cycles, freq="D", tz="UTC")
        for cycle_index, init_time in enumerate(cycles):
            seasonal = np.sin(2 * np.pi * init_time.dayofyear / 365.25)
            monsoon = float(init_time.month in (6, 7, 8, 9))
            for region_id, region_name, base_lat, base_lon in REGIONS:
                region_phase = (base_lat + base_lon) / 25
                event_seed = max(0.0, rng.normal(0.25 + 0.22 * monsoon + 0.12 * seasonal, 0.22))
                for point in range(self.grid_points_per_region):
                    lat, lon = base_lat + rng.normal(0, .22), base_lon + rng.normal(0, .22)
                    for lead_day in range(1, 11):
                        valid_time = init_time + pd.Timedelta(days=lead_day)
                        rapid_change = max(0., event_seed + rng.normal(0, .12) + .018 * lead_day)
                        ensemble_spread = .12 + .10 * lead_day + .65 * rapid_change + rng.uniform(0, .12)
                        pressure_tendency = rng.normal(0, 1.2) - 2.8 * rapid_change
                        cape = max(0., 180 + 1400 * rapid_change + 520 * monsoon + rng.normal(0, 160))
                        humidity = np.clip(45 + 28 * monsoon + 18 * rapid_change + rng.normal(0, 8), 15, 100)
                        wind_shear = max(0., 3 + 14 * rapid_change + rng.normal(0, 2))
                        for variable in variables:
                            base = self._base_value(variable, seasonal, monsoon, region_phase, rapid_change, rng)
                            true = max(0., base + rng.normal(0, self._observation_noise(variable)))
                            error_scale = self._error_scale(variable, lead_day, rapid_change, ensemble_spread)
                            signed_error = rng.normal(0, error_scale) + self._systematic_bias(variable, rapid_change)
                            forecast = max(0., true + signed_error) if variable != "temperature_2m" else true + signed_error
                            rows.append({
                                "forecast_initialization_time": init_time,
                                "valid_time": valid_time,
                                "lead_day": lead_day, "latitude": round(lat, 4), "longitude": round(lon, 4),
                                "region_id": region_id, "region_name": region_name, "variable": variable,
                                "forecast_value": forecast, "observation_value": true,
                                "ensemble_spread": ensemble_spread, "pressure_tendency": pressure_tendency,
                                "cape": cape, "humidity": humidity, "wind_shear": wind_shear,
                                "rapid_change_index": rapid_change, "data_quality": float(rng.uniform(.88, 1.0)),
                                "model_identifier": "synthetic_nwp_v1", "ensemble_member": None,
                                "data_mode": "synthetic",
                            })
        self._full = pd.DataFrame(rows)
        return self._full.copy()

    @staticmethod
    def _base_value(variable: str, seasonal: float, monsoon: float, phase: float, event: float,
                    rng: np.random.Generator) -> float:
        if variable == "precipitation":
            return max(0., 3 + 15 * monsoon + 26 * event + 4 * np.sin(phase) + rng.gamma(1.2, 2))
        if variable == "temperature_2m":
            return 27 + 7 * seasonal - 3 * monsoon + .9 * np.sin(phase) + 1.2 * event
        return max(0., 3.5 + 2 * seasonal + 5 * event + rng.normal(0, .6))

    @staticmethod
    def _observation_noise(variable: str) -> float:
        return {"precipitation": 2.5, "temperature_2m": .6, "wind_speed": .5}[variable]

    @staticmethod
    def _error_scale(variable: str, lead: int, event: float, spread: float) -> float:
        multiplier = {"precipitation": 2.8, "temperature_2m": .28, "wind_speed": .42}[variable]
        return multiplier * (1 + .16 * lead + 1.25 * event + .25 * spread)

    @staticmethod
    def _systematic_bias(variable: str, event: float) -> float:
        return {"precipitation": -2.0 * event, "temperature_2m": .18 * event, "wind_speed": .25 * event}[variable]

    def load_forecasts(self) -> pd.DataFrame:
        return self._generate().drop(columns=["observation_value"])

    def load_observations(self) -> pd.DataFrame:
        output = self._generate()[["valid_time", "latitude", "longitude", "region_id", "variable", "observation_value", "data_mode"]]
        return output.copy()

    def full_verified_data(self) -> pd.DataFrame:
        return self._generate()


def load_tabular_source(path: str | Path, required: Iterable[str] = REQUIRED_COLUMNS) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path)
    elif path.suffix.lower() in {".parquet", ".pq"}:
        frame = pd.read_parquet(path)
    else:
        raise ValueError("Only CSV and Parquet are accepted by the tabular provider")
    missing = set(required).difference(frame.columns)
    if missing:
        raise ValueError(f"Source does not meet common schema; missing: {sorted(missing)}")
    return frame


class NetCDFDataProvider(BaseWeatherDataProvider):
    def __init__(self, path: str | Path) -> None: self.path = Path(path)
    def load_forecasts(self) -> pd.DataFrame:
        try:
            import xarray as xr
        except ImportError as exc:
            raise RuntimeError("NetCDF support requires xarray and netCDF4") from exc
        raise NotImplementedError("Map variable names/units to the common schema before using a NetCDF source")
    def load_observations(self) -> pd.DataFrame: raise NotImplementedError


class GRIBDataProvider(BaseWeatherDataProvider):
    def __init__(self, path: str | Path) -> None: self.path = Path(path)
    def load_forecasts(self) -> pd.DataFrame:
        try:
            import cfgrib  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("GRIB support requires cfgrib and eccodes") from exc
        raise NotImplementedError("Map GRIB fields/units to the common schema before using a GRIB source")
    def load_observations(self) -> pd.DataFrame: raise NotImplementedError
