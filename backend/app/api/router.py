from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.database.database import get_session
from backend.app.schemas.api import IngestRequest, PredictionRequest, TrainRequest
from backend.app.services.prediction_store import store_predictions
from ml.inference.pipeline import ForecastBustPipeline
from ml.preprocessing.validation import DataValidationError, validate_weather_frame

router = APIRouter(prefix="/api")
root_router = APIRouter()
pipeline = ForecastBustPipeline(model_dir=settings.model_dir)


def _records(frame: pd.DataFrame) -> list[dict]:
    """Use pandas' ISO-aware JSON conversion so FastAPI only receives JSON primitives."""
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def _latest(variable: str | None = None, lead_day: int | None = None) -> pd.DataFrame:
    try: return pipeline.region_predictions(variable, lead_day)
    except (ValueError, FileNotFoundError) as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "data_mode": settings.data_mode, "model_available": (Path(settings.model_dir) / "forecast_bust_bundle.joblib").exists()}


@router.get("/forecast/latest")
def latest(variable: str | None = Query(None), lead_day: int | None = Query(None, ge=1, le=10)) -> dict:
    return {"data_mode": "synthetic", "source_status": "SYNTHETIC — development only", "predictions": _records(_latest(variable, lead_day))}


@root_router.get("/forecast/latest")
def latest_root(variable: str | None = Query(None), lead_day: int | None = Query(None, ge=1, le=10)) -> dict:
    return latest(variable=variable, lead_day=lead_day)


@router.get("/forecast/confidence")
def confidence(variable: str = "precipitation", lead_day: int = Query(5, ge=1, le=10)) -> dict:
    records = _latest(variable, lead_day)[["region_id", "region_name", "lead_day", "confidence_score", "risk_level", "data_mode"]]
    return {"predictions": _records(records)}


@root_router.get("/forecast/confidence")
def confidence_root(variable: str = "precipitation", lead_day: int = Query(5, ge=1, le=10)) -> dict:
    return confidence(variable=variable, lead_day=lead_day)


@router.get("/forecast/bust-probability")
def bust_probability(variable: str = "precipitation", lead_day: int = Query(5, ge=1, le=10)) -> dict:
    records = _latest(variable, lead_day)[["region_id", "region_name", "lead_day", "bust_probability", "risk_level", "data_mode"]]
    return {"predictions": _records(records)}


@root_router.get("/forecast/bust-probability")
def bust_probability_root(variable: str = "precipitation", lead_day: int = Query(5, ge=1, le=10)) -> dict:
    return bust_probability(variable=variable, lead_day=lead_day)


@router.get("/forecast/error")
def forecast_error(variable: str = "precipitation", lead_day: int = Query(5, ge=1, le=10)) -> dict:
    records = _latest(variable, lead_day)[["region_id", "region_name", "lead_day", "expected_error", "data_mode"]]
    return {"predictions": _records(records)}


@root_router.get("/forecast/error")
def forecast_error_root(variable: str = "precipitation", lead_day: int = Query(5, ge=1, le=10)) -> dict:
    return forecast_error(variable=variable, lead_day=lead_day)


@router.get("/regions")
def regions(variable: str = "precipitation", lead_day: int = Query(5, ge=1, le=10), session: Session = Depends(get_session)) -> dict:
    records = _latest(variable, lead_day)
    bundle, _ = pipeline.train()
    stored = store_predictions(session, records, bundle.metadata)
    return {"stored": stored, "regions": _records(records)}


@root_router.get("/regions")
def regions_root(variable: str = "precipitation", lead_day: int = Query(5, ge=1, le=10), session: Session = Depends(get_session)) -> dict:
    return regions(variable=variable, lead_day=lead_day, session=session)


@router.get("/regions/{region_id}")
def region(region_id: str, variable: str = "precipitation", lead_day: int = Query(5, ge=1, le=10)) -> dict:
    records = _latest(variable, lead_day)
    selected = records[records.region_id == region_id]
    if selected.empty: raise HTTPException(status_code=404, detail="Region not found")
    return _records(selected)[0]


@root_router.get("/regions/{region_id}")
def region_root(region_id: str, variable: str = "precipitation", lead_day: int = Query(5, ge=1, le=10)) -> dict:
    return region(region_id=region_id, variable=variable, lead_day=lead_day)


@router.get("/explanations/{region_id}")
def explanation(region_id: str, variable: str = "precipitation", lead_day: int = Query(5, ge=1, le=10)) -> dict:
    try: return pipeline.explanation(region_id, variable, lead_day)
    except ValueError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc


@root_router.get("/explanations/{region_id}")
def explanation_root(region_id: str, variable: str = "precipitation", lead_day: int = Query(5, ge=1, le=10)) -> dict:
    return explanation(region_id=region_id, variable=variable, lead_day=lead_day)


@router.get("/model/info")
def model_info() -> dict:
    try:
        bundle, _ = pipeline.train()
        return {**bundle.metadata, "metrics": pipeline.load_metrics().get("overall", {})}
    except (ValueError, FileNotFoundError) as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/predict")
def predict(request: PredictionRequest) -> dict:
    try: return pipeline.predict_request(request.model_dump(mode="json"))
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/data/ingest")
def ingest(request: IngestRequest) -> dict:
    try:
        records = validate_weather_frame(pd.DataFrame(request.records), require_observation=False)
    except DataValidationError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    destination = Path("data/interim/ingested_forecasts.csv")
    destination.parent.mkdir(parents=True, exist_ok=True)
    records.to_csv(destination, index=False)
    return {"status": "accepted", "records": len(records), "data_mode": sorted(records.data_mode.unique().tolist()), "note": "Ingested data is validated and staged; training requires matched observations."}


@router.post("/model/train")
def train(request: TrainRequest) -> dict:
    try:
        bundle, metrics = pipeline.train(force=request.force)
        return {"status": "trained", "model": bundle.metadata, "metrics": metrics.get("overall", {})}
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/verification")
def verification() -> dict:
    return {"metrics": _records(pipeline.verification_summary())}


@root_router.get("/verification")
def verification_root() -> dict:
    return verification()


@router.get("/metrics")
def metrics() -> dict:
    return pipeline.load_metrics()


@root_router.get("/metrics")
def metrics_root() -> dict:
    return metrics()
