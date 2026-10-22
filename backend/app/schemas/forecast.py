"""
Pydantic Schemas for NWP Forecast Bust Detection API.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Coordinate(BaseModel):
    lat: float
    lon: float

class DailyRiskSummary(BaseModel):
    lead_day: int
    mean_confidence: float
    max_bust_probability: float
    high_bust_cells_pct: float
    active_alert_zones: int
    primary_threat: str

class ForecastSummaryResponse(BaseModel):
    scenario: str
    scenario_description: str
    peak_risk_day: int
    mean_10day_confidence: float
    total_active_alerts: int
    critical_subdivisions: List[str]
    timeline: List[DailyRiskSummary]

class AlertZoneProperties(BaseModel):
    alert_id: str
    severity: str  # 'CRITICAL', 'WARNING', 'WATCH'
    lead_day: int
    max_bust_prob: float
    mean_confidence: float
    area_sq_km: float
    primary_driver: str
    subdivision: str
    center_lat: float
    center_lon: float

class GeoJSONGeometry(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[List[float]]]

class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: GeoJSONGeometry
    properties: AlertZoneProperties

class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]

class GridForecastResponse(BaseModel):
    scenario: str
    lead_day: int
    bounds: Dict[str, float]
    lats: List[float]
    lons: List[float]
    confidence_grid: List[List[float]]
    bust_prob_grid: List[List[float]]
    precip_grid: List[List[float]]
    mslp_grid: List[List[float]]
    z500_grid: List[List[float]]
    vort850_grid: List[List[float]]
    pwat_grid: List[List[float]]
    alert_zones: GeoJSONFeatureCollection

class VariableAttribution(BaseModel):
    name: str
    percentage: float
    importance_score: float

class ExplainForecastResponse(BaseModel):
    lead_day: int
    coordinate: Coordinate
    subdivision: str
    confidence: float
    bust_probability: float
    primary_driver: str
    primary_driver_pct: float
    secondary_driver: str
    secondary_driver_pct: float
    meteorological_briefing: str
    variable_attributions: Dict[str, VariableAttribution]
    spatial_saliency: Optional[List[List[float]]] = None

class ScenarioInfo(BaseModel):
    id: str
    name: str
    description: str
    primary_driver: str
