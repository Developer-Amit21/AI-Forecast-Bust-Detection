from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BustDefinition:
    mode: str = "percentile"
    percentile: float = 0.90
    absolute_thresholds: dict[str, float] | None = None
    normalized_threshold: float = 2.0


def fit_bust_thresholds(verified: pd.DataFrame, definition: BustDefinition = BustDefinition()) -> pd.DataFrame:
    if "absolute_error" not in verified: raise ValueError("Compute verification errors before fitting thresholds")
    grouping = ["variable", "lead_day"]
    if definition.mode == "percentile":
        output = verified.groupby(grouping).absolute_error.quantile(definition.percentile).rename("bust_threshold").reset_index()
    elif definition.mode == "absolute":
        values = definition.absolute_thresholds or {}
        output = verified[grouping].drop_duplicates().copy()
        output["bust_threshold"] = output.variable.map(values)
        if output.bust_threshold.isna().any(): raise ValueError("Absolute threshold missing for one or more variables")
    elif definition.mode == "normalized":
        stats = verified.groupby(grouping).absolute_error.agg(["mean", "std"]).reset_index()
        output = stats[grouping].copy()
        output["bust_threshold"] = stats["mean"] + definition.normalized_threshold * stats["std"]
    else: raise ValueError(f"Unknown bust mode: {definition.mode}")
    output["definition_mode"] = definition.mode
    return output


def apply_bust_labels(verified: pd.DataFrame, thresholds: pd.DataFrame) -> pd.DataFrame:
    data = verified.merge(thresholds[["variable", "lead_day", "bust_threshold"]], on=["variable", "lead_day"], how="left", validate="many_to_one")
    if data.bust_threshold.isna().any(): raise ValueError("No fitted bust threshold for a row")
    data["bust_binary"] = (data.absolute_error > data.bust_threshold).astype(int)
    ratio = data.absolute_error / data.bust_threshold.clip(lower=1e-6)
    data["bust_probability_target"] = ratio.clip(0, 2) / 2
    data["error_severity"] = np.select([ratio < .5, ratio < 1, ratio < 1.5], [0, 1, 2], default=3).astype(int)
    return data
