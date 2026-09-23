from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase): pass


class ForecastRun(Base):
    __tablename__ = "forecast_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    initialization_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    model_identifier: Mapped[str] = mapped_column(String(100))
    data_mode: Mapped[str] = mapped_column(String(20))
    source_uri: Mapped[str | None] = mapped_column(String(500), nullable=True)


class ForecastValue(Base):
    __tablename__ = "forecast_values"
    id: Mapped[int] = mapped_column(primary_key=True)
    forecast_run_id: Mapped[int] = mapped_column(ForeignKey("forecast_runs.id"))
    valid_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    lead_day: Mapped[int] = mapped_column(Integer)
    latitude: Mapped[float] = mapped_column(Float); longitude: Mapped[float] = mapped_column(Float)
    variable: Mapped[str] = mapped_column(String(50)); value: Mapped[float] = mapped_column(Float)


class Observation(Base):
    __tablename__ = "observations"
    id: Mapped[int] = mapped_column(primary_key=True)
    valid_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    latitude: Mapped[float] = mapped_column(Float); longitude: Mapped[float] = mapped_column(Float)
    variable: Mapped[str] = mapped_column(String(50)); value: Mapped[float] = mapped_column(Float)
    data_mode: Mapped[str] = mapped_column(String(20))


class VerificationResult(Base):
    __tablename__ = "verification_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    forecast_value_id: Mapped[int | None] = mapped_column(ForeignKey("forecast_values.id"), nullable=True)
    metric_name: Mapped[str] = mapped_column(String(50)); metric_value: Mapped[float] = mapped_column(Float)
    region_id: Mapped[str | None] = mapped_column(String(30), nullable=True); lead_day: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Region(Base):
    __tablename__ = "regions"
    region_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    name: Mapped[str] = mapped_column(String(100)); geometry_geojson: Mapped[str | None] = mapped_column(Text, nullable=True)


class ModelVersion(Base):
    __tablename__ = "model_versions"
    version: Mapped[str] = mapped_column(String(100), primary_key=True)
    trained_period: Mapped[str] = mapped_column(String(200)); feature_version: Mapped[str] = mapped_column(String(30))
    data_mode: Mapped[str] = mapped_column(String(20)); metadata_json: Mapped[str] = mapped_column(Text)


class BustPrediction(Base):
    __tablename__ = "bust_predictions"
    __table_args__ = (UniqueConstraint("region_id", "variable", "lead_day", "forecast_cycle", "model_version", name="uq_prediction_cycle"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    region_id: Mapped[str] = mapped_column(ForeignKey("regions.region_id"), index=True)
    variable: Mapped[str] = mapped_column(String(50)); lead_day: Mapped[int] = mapped_column(Integer)
    forecast_cycle: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    expected_error: Mapped[float] = mapped_column(Float); bust_probability: Mapped[float] = mapped_column(Float)
    confidence_score: Mapped[float] = mapped_column(Float); risk_level: Mapped[str] = mapped_column(String(20))
    model_version: Mapped[str] = mapped_column(ForeignKey("model_versions.version")); data_mode: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class PredictionExplanation(Base):
    __tablename__ = "prediction_explanations"
    id: Mapped[int] = mapped_column(primary_key=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("bust_predictions.id"))
    method: Mapped[str] = mapped_column(String(100)); explanation_json: Mapped[str] = mapped_column(Text)
