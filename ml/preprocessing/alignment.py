from __future__ import annotations

import pandas as pd


def align_forecasts_observations(forecasts: pd.DataFrame, observations: pd.DataFrame) -> pd.DataFrame:
    """Inner join on valid time/location/variable; never fills unavailable observations."""
    keys = ["valid_time", "latitude", "longitude", "region_id", "variable", "data_mode"]
    observation_columns = keys + ["observation_value"]
    missing = set(observation_columns).difference(observations.columns)
    if missing: raise ValueError(f"Observation records missing {sorted(missing)}")
    aligned = forecasts.merge(observations[observation_columns], on=keys, how="inner", validate="many_to_one")
    if aligned.empty: raise ValueError("No forecast/observation rows align on time, position, and variable")
    return aligned
