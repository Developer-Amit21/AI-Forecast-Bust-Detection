from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/health")
        root_response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert root_response.status_code == 200
    assert root_response.json()["status"] == "ok"


def test_root_level_forecast_routes_exist():
    with TestClient(app) as client:
        latest_response = client.get("/forecast/latest")
        regions_response = client.get("/regions")
        assert latest_response.status_code == 200
        assert regions_response.status_code == 200
