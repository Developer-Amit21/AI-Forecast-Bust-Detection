"""
Tests for SpatioTemporalBustUNet Architecture and Gradient Flow.
"""
import pytest
import torch
from backend.ml.model import SpatioTemporalBustUNet

def test_model_forward_shape():
    model = SpatioTemporalBustUNet(in_channels=5, base_channels=16)
    model.eval()
    
    B, C, H, W = 2, 5, 34, 36
    x = torch.randn(B, C, H, W)
    lead_day = torch.tensor([3, 7])
    
    with torch.no_grad():
        conf, bust_prob = model(x, lead_day)
        
    assert conf.shape == (B, 1, H, W)
    assert bust_prob.shape == (B, 1, H, W)
    
    # Values bounded in [0, 1]
    assert (conf >= 0.0).all() and (conf <= 1.0).all()
    assert (bust_prob >= 0.0).all() and (bust_prob <= 1.0).all()

def test_model_backward_pass():
    model = SpatioTemporalBustUNet(in_channels=5, base_channels=16)
    model.train()
    
    x = torch.randn(2, 5, 34, 36, requires_grad=True)
    lead_day = torch.tensor([1, 5])
    
    conf, bust = model(x, lead_day)
    target = torch.ones_like(bust)
    loss = torch.nn.functional.binary_cross_entropy(bust, target)
    loss.backward()
    
    assert x.grad is not None
    assert not torch.isnan(x.grad).any()
