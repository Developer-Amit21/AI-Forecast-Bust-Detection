"""
Integration tests for FastAPI REST Endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_scenarios_list(client):
    response = client.get("/api/v1/forecast/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) >= 3
    ids = [s["id"] for s in scenarios]
    assert "western_disturbance" in ids
    assert "monsoon_depression" in ids

def test_forecast_summary(client):
    response = client.get("/api/v1/forecast/summary?scenario=western_disturbance")
    assert response.status_code == 200
    data = response.json()
    assert data["scenario"] == "western_disturbance"
    assert len(data["timeline"]) == 10
    assert "peak_risk_day" in data
    assert 0.0 <= data["mean_10day_confidence"] <= 1.0

def test_forecast_grid(client):
    response = client.get("/api/v1/forecast/grid?scenario=monsoon_depression&lead_day=4")
    assert response.status_code == 200
    data = response.json()
    assert data["lead_day"] == 4
    assert len(data["confidence_grid"]) == 34
    assert len(data["confidence_grid"][0]) == 36
    assert data["alert_zones"]["type"] == "FeatureCollection"

def test_forecast_explain(client):
    response = client.get("/api/v1/forecast/explain?scenario=western_disturbance&lead_day=5&lat=30.0&lon=74.0")
    assert response.status_code == 200
    data = response.json()
    assert data["lead_day"] == 5
    assert "primary_driver" in data
    assert "variable_attributions" in data
    assert len(data["variable_attributions"]) == 5
    assert "meteorological_briefing" in data
