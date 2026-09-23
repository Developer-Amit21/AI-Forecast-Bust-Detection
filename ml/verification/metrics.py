from __future__ import annotations

import numpy as np
import pandas as pd


def add_error_columns(frame: pd.DataFrame) -> pd.DataFrame:
    if "observation_value" not in frame: raise ValueError("Verification requires observation_value")
    data = frame.copy()
    data["signed_error"] = data.forecast_value - data.observation_value
    data["absolute_error"] = data.signed_error.abs()
    denominator = data.observation_value.abs()
    data["relative_error"] = np.where(denominator >= 1e-6, data.absolute_error / denominator, np.nan)
    return data


def _categorical_metrics(group: pd.DataFrame, threshold: float) -> dict[str, float]:
    forecast_event = group.forecast_value >= threshold
    observed_event = group.observation_value >= threshold
    hits = int((forecast_event & observed_event).sum())
    false_alarms = int((forecast_event & ~observed_event).sum())
    misses = int((~forecast_event & observed_event).sum())
    return {
        "threshold": threshold,
        "csi": hits / (hits + false_alarms + misses) if hits + false_alarms + misses else np.nan,
        "pod": hits / (hits + misses) if hits + misses else np.nan,
        "far": false_alarms / (hits + false_alarms) if hits + false_alarms else np.nan,
        "miss_rate": misses / (hits + misses) if hits + misses else np.nan,
    }


def summarize_verification(frame: pd.DataFrame, group_by: list[str] | None = None,
                           precipitation_threshold: float = 20.0) -> pd.DataFrame:
    data = add_error_columns(frame) if "absolute_error" not in frame else frame.copy()
    group_by = group_by or ["variable", "lead_day"]
    rows: list[dict] = []
    for keys, group in data.groupby(group_by, dropna=False):
        keys = keys if isinstance(keys, tuple) else (keys,)
        row = dict(zip(group_by, keys))
        signed = group.signed_error
        row.update({
            "count": len(group), "mae": float(group.absolute_error.mean()),
            "rmse": float(np.sqrt(np.mean(np.square(signed)))), "bias": float(signed.mean()),
            "mean_relative_error": float(group.relative_error.mean()),
        })
        if row.get("variable") == "precipitation": row.update(_categorical_metrics(group, precipitation_threshold))
        rows.append(row)
    return pd.DataFrame(rows)
