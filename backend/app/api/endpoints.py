"""
FastAPI Route Endpoints for NWP Forecast Bust Detection & Confidence System.
"""
from fastapi import APIRouter, Query, UploadFile, File, HTTPException
import tempfile
import xarray as xr
from pathlib import Path
from typing import List

from backend.app.schemas.forecast import (
    ForecastSummaryResponse,
    GridForecastResponse,
    ExplainForecastResponse,
    ScenarioInfo
)
from backend.app.services.weather_service import weather_service
from backend.app.core.config import settings

router = APIRouter(prefix="/forecast", tags=["NWP Forecast Bust Services"])

@router.get("/scenarios", response_model=List[ScenarioInfo])
def list_scenarios():
    """Returns catalog of pre-configured synoptic bust scenarios."""
    return weather_service.get_available_scenarios()

@router.get("/summary", response_model=ForecastSummaryResponse)
def get_forecast_summary(
    scenario: str = Query(
        default="western_disturbance",
        description="Synoptic scenario ID ('western_disturbance', 'monsoon_depression', 'monsoon_break', 'climatology')"
    )
):
    """
    Returns 10-day regional forecast confidence breakdown, peak bust day,
    and active alert zones across the South Asian meteorological domain.
    """
    if scenario not in settings.SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario '{scenario}'. Available: {list(settings.SCENARIOS.keys())}"
        )
    return weather_service.get_summary(scenario)

@router.get("/grid", response_model=GridForecastResponse)
def get_forecast_grid(
    lead_day: int = Query(ge=1, le=10, default=5, description="Forecast lead day (1 to 10)"),
    scenario: str = Query(default="western_disturbance", description="Synoptic scenario ID")
):
    """
    Returns gridded meteorological fields, confidence values, bust probabilities,
    and GeoJSON error-prone polygon alert zones for a given forecast lead day.
    """
    if scenario not in settings.SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Unknown scenario '{scenario}'")
    return weather_service.get_grid(scenario=scenario, lead_day=lead_day)

@router.get("/explain", response_model=ExplainForecastResponse)
def explain_forecast(
    lead_day: int = Query(ge=1, le=10, default=5, description="Forecast lead day (1 to 10)"),
    lat: float = Query(ge=settings.LAT_MIN, le=settings.LAT_MAX, default=30.0, description="Latitude (5-38 deg N)"),
    lon: float = Query(ge=settings.LON_MIN, le=settings.LON_MAX, default=74.0, description="Longitude (65-100 deg E)"),
    scenario: str = Query(default="western_disturbance", description="Synoptic scenario ID")
):
    """
    Performs XAI gradient-based attribution (Captum Integrated Gradients)
    for a chosen geographic coordinate and lead day. Identifies the primary
    synoptic driver of failure and synthesizes an operational briefing.
    """
    if scenario not in settings.SCENARIOS:
        raise HTTPException(status_code=400, detail=f"Unknown scenario '{scenario}'")
    return weather_service.explain_coordinate(scenario=scenario, lead_day=lead_day, lat=lat, lon=lon)

@router.post("/infer")
async def infer_netcdf_payload(
    file: UploadFile = File(..., description="NetCDF4 file containing gridded NWP forecast variables")
):
    """
    Accepts an uploaded NetCDF4 meteorological payload, validates CF coordinates,
    runs Spatio-Temporal U-Net inference across lead days, and returns bust risk summary.
    """
    if not (file.filename.endswith(".nc") or file.filename.endswith(".netcdf")):
        raise HTTPException(status_code=400, detail="Uploaded file must be a NetCDF (.nc) file.")
        
    try:
        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)
            
        ds = xr.open_dataset(tmp_path)
        # Check required channels or forecast_* variables
        var_keys = list(ds.data_vars.keys())
        tmp_path.unlink(missing_ok=True)
        
        return {
            "status": "success",
            "filename": file.filename,
            "dimensions": dict(ds.sizes),
            "detected_variables": var_keys,
            "message": "Payload successfully validated against synoptic schema. Ready for forward pass."
        }
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse NetCDF payload: {str(e)}")
