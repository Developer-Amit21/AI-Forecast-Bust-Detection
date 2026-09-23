from __future__ import annotations

import pandas as pd

from ml.ingestion.providers import REQUIRED_COLUMNS


class DataValidationError(ValueError): pass


def validate_weather_frame(frame: pd.DataFrame, require_observation: bool = False) -> pd.DataFrame:
    required = set(REQUIRED_COLUMNS)
    if require_observation: required.add("observation_value")
    missing = required.difference(frame.columns)
    if missing: raise DataValidationError(f"Missing required columns: {sorted(missing)}")
    data = frame.copy()
    for column in ("forecast_initialization_time", "valid_time"):
        data[column] = pd.to_datetime(data[column], utc=True, errors="coerce")
    if data[["forecast_initialization_time", "valid_time"]].isna().any().any():
        raise DataValidationError("Invalid timestamps")
    if not data.latitude.between(-90, 90).all() or not data.longitude.between(-180, 180).all():
        raise DataValidationError("Coordinates must be within WGS84 bounds")
    if not data.lead_day.between(0, 10).all(): raise DataValidationError("lead_day must be 0–10")
    if (data.forecast_value.isna()).any(): raise DataValidationError("forecast_value contains missing values")
    if (data.variable == "precipitation").any() and (data.loc[data.variable == "precipitation", "forecast_value"] < 0).any():
        raise DataValidationError("Precipitation cannot be negative")
    duplicates = data.duplicated(["forecast_initialization_time", "valid_time", "latitude", "longitude", "variable"])
    if duplicates.any(): raise DataValidationError(f"Found {int(duplicates.sum())} duplicate forecast records")
    if not (data.valid_time >= data.forecast_initialization_time).all():
        raise DataValidationError("valid_time predates forecast initialization")
    expected_lead = (data.valid_time - data.forecast_initialization_time).dt.total_seconds() / 86_400
    if not ((expected_lead - data.lead_day).abs() < .01).all():
        raise DataValidationError("lead_day does not match initialization and valid time")
    return data
