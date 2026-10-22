"""
Tests for Synthetic Weather Data Generator and NetCDF pipeline.
"""
import pytest
import numpy as np
from backend.ml.data_generator import WeatherDataGenerator
from backend.app.core.config import settings

def test_data_generator_dimensions():
    gen = WeatherDataGenerator(seed=123)
    ds, meta = gen.simulate_scenario("western_disturbance")
    
    assert len(ds.coords["lead_day"]) == 10
    assert len(ds.coords["lat"]) == len(gen.lats)
    assert len(ds.coords["lon"]) == len(gen.lons)
    
    for ch in settings.CHANNELS:
        assert f"forecast_{ch}" in ds.data_vars
        assert f"truth_{ch}" in ds.data_vars
        shape = ds[f"forecast_{ch}"].shape
        assert shape == (10, len(gen.lats), len(gen.lons))

def test_physical_variable_bounds():
    gen = WeatherDataGenerator(seed=456)
    ds, _ = gen.simulate_scenario("monsoon_depression")
    
    # Precip must be >= 0
    assert np.all(ds["forecast_precip"].values >= 0.0)
    assert np.all(ds["truth_precip"].values >= 0.0)
    
    # MSLP should be realistic atmospheric pressures (970 - 1035 hPa)
    assert np.all(ds["forecast_mslp"].values >= 970.0)
    assert np.all(ds["forecast_mslp"].values <= 1035.0)
    
    # Z500 geopotential height (5200 - 6050 gpm)
    assert np.all(ds["forecast_z500"].values >= 5200.0)
    assert np.all(ds["forecast_z500"].values <= 6050.0)

def test_scenario_anomaly_injection():
    gen = WeatherDataGenerator(seed=789)
    ds_wd, meta_wd = gen.simulate_scenario("western_disturbance")
    ds_md, meta_md = gen.simulate_scenario("monsoon_depression")
    
    assert "bust_ground_truth" in ds_wd.data_vars
    assert "confidence_ground_truth" in ds_wd.data_vars
    
    # By day 6, bust mask should have positive bust cells in anomalous scenarios
    assert np.sum(ds_wd["bust_ground_truth"].values[5]) > 0
    assert np.sum(ds_md["bust_ground_truth"].values[5]) > 0
