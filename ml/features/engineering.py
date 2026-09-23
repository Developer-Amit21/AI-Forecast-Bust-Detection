from __future__ import annotations

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "lead_day", "forecast_value", "ensemble_spread", "pressure_tendency", "cape", "humidity",
    "wind_shear", "rapid_change_index", "data_quality", "month_sin", "month_cos", "monsoon_indicator",
    "historical_mae", "historical_bias", "historical_bust_frequency", "forecast_change",
    "cyclone_like_indicator", "heavy_rain_environment", "heatwave_environment",
]


def _history_features(data: pd.DataFrame, windows: int = 30) -> pd.DataFrame:
    group_cols = ["region_id", "variable", "lead_day"]
    # Shift first: a row can only use error outcomes from earlier forecast cycles.
    sorted_data = data.sort_values("forecast_initialization_time").copy()
    grouped = sorted_data.groupby(group_cols, group_keys=False)
    if "absolute_error" not in sorted_data: sorted_data["absolute_error"] = np.nan
    if "signed_error" not in sorted_data: sorted_data["signed_error"] = np.nan
    if "bust_binary" not in sorted_data: sorted_data["bust_binary"] = np.nan
    sorted_data["historical_mae"] = grouped.absolute_error.transform(lambda x: x.shift(1).rolling(windows, min_periods=3).mean())
    sorted_data["historical_bias"] = grouped.signed_error.transform(lambda x: x.shift(1).rolling(windows, min_periods=3).mean())
    sorted_data["historical_bust_frequency"] = grouped.bust_binary.transform(lambda x: x.shift(1).rolling(windows, min_periods=3).mean())
    sorted_data["forecast_change"] = grouped.forecast_value.transform(lambda x: x.diff().abs())
    return sorted_data


def build_feature_table(frame: pd.DataFrame, history_window: int = 30) -> pd.DataFrame:
    data = frame.copy()
    data["forecast_initialization_time"] = pd.to_datetime(data.forecast_initialization_time, utc=True)
    data = _history_features(data, history_window)
    month = data.forecast_initialization_time.dt.month
    data["month_sin"] = np.sin(2 * np.pi * month / 12)
    data["month_cos"] = np.cos(2 * np.pi * month / 12)
    data["monsoon_indicator"] = month.isin([6, 7, 8, 9]).astype(int)
    # Probabilistic environmental pattern flags; these are not event declarations.
    data["cyclone_like_indicator"] = np.clip((data.wind_shear / 25 + (-data.pressure_tendency).clip(lower=0) / 12 + data.humidity / 150) / 3, 0, 1)
    data["heavy_rain_environment"] = np.clip((data.cape / 2800 + data.humidity / 120 + data.rapid_change_index) / 3, 0, 1)
    data["heatwave_environment"] = ((data.variable == "temperature_2m") & (data.forecast_value > 38)).astype(int)
    # Initial cycles lack prior observations; retain but impute only model inputs later.
    return data


def model_matrix(features: pd.DataFrame) -> pd.DataFrame:
    return features[FEATURE_COLUMNS].replace([np.inf, -np.inf], np.nan).fillna(0.0)
