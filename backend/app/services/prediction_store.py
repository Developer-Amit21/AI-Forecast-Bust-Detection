from __future__ import annotations

import json

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import BustPrediction, ModelVersion, Region


def store_predictions(session: Session, predictions: pd.DataFrame, model_metadata: dict) -> int:
    version = model_metadata["model_version"]
    if session.get(ModelVersion, version) is None:
        session.add(ModelVersion(version=version, trained_period=model_metadata["training_period"], feature_version=model_metadata["feature_version"], data_mode=model_metadata["data_mode"], metadata_json=json.dumps(model_metadata)))
    count = 0
    for row in predictions.to_dict(orient="records"):
        if session.get(Region, row["region_id"]) is None:
            session.add(Region(region_id=row["region_id"], name=row["region_name"], geometry_geojson=None))
        existing = session.scalar(select(BustPrediction).where(BustPrediction.region_id == row["region_id"], BustPrediction.variable == row["variable"], BustPrediction.lead_day == int(row["lead_day"]), BustPrediction.forecast_cycle == pd.Timestamp(row["forecast_initialization_time"]).to_pydatetime(), BustPrediction.model_version == version))
        if existing is None:
            session.add(BustPrediction(region_id=row["region_id"], variable=row["variable"], lead_day=int(row["lead_day"]), forecast_cycle=pd.Timestamp(row["forecast_initialization_time"]).to_pydatetime(), expected_error=float(row["expected_error"]), bust_probability=float(row["bust_probability"]), confidence_score=float(row["confidence_score"]), risk_level=str(row["risk_level"]), model_version=version, data_mode=row["data_mode"]))
            count += 1
    session.commit()
    return count
