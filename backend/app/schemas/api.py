from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    forecast_initialization_time: datetime
    valid_time: datetime
    lead_day: int = Field(ge=1, le=10)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    region_id: str = Field(min_length=1, max_length=30)
    region_name: str = Field(min_length=1, max_length=100)
    variable: Literal["precipitation", "temperature_2m", "wind_speed"]
    forecast_value: float
    ensemble_spread: float = Field(ge=0)
    pressure_tendency: float = 0
    cape: float = Field(default=0, ge=0)
    humidity: float = Field(default=50, ge=0, le=100)
    wind_shear: float = Field(default=0, ge=0)
    rapid_change_index: float = Field(default=0, ge=0)
    data_quality: float = Field(default=1, ge=0, le=1)
    data_mode: Literal["synthetic", "real"] = "synthetic"


class IngestRequest(BaseModel):
    records: list[dict] = Field(min_length=1, max_length=10_000)


class TrainRequest(BaseModel):
    force: bool = False
