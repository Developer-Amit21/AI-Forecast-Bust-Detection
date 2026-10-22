"""
Tests for Explainability Engine (Captum Integrated Gradients).
"""
import pytest
import torch
from backend.ml.model import SpatioTemporalBustUNet
from backend.ml.explainability import WeatherXAI

def test_explainability_attribution():
    model = SpatioTemporalBustUNet(in_channels=5, base_channels=16)
    xai = WeatherXAI(model=model, device=torch.device("cpu"))
    
    x_tensor = torch.randn(1, 5, 34, 36)
    lead_day = 4
    lat_idx, lon_idx = 15, 18
    
    result = xai.attribute_coordinate(
        x_tensor=x_tensor,
        lead_day=lead_day,
        lat_idx=lat_idx,
        lon_idx=lon_idx,
        n_steps=5
    )
    
    assert "variable_attributions" in result
    assert "primary_driver" in result
    assert "meteorological_briefing" in result
    assert len(result["variable_attributions"]) == 5
    
    # Check percentages roughly sum to 100%
    total_pct = sum(v["percentage"] for v in result["variable_attributions"].values())
    assert 99.0 <= total_pct <= 101.0
