from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ml.evaluation.metrics import evaluate_predictions
from ml.explainability.explainer import explain_prediction, global_feature_importance
from ml.features.engineering import build_feature_table
from ml.ingestion.providers import SyntheticDataProvider
from ml.labeling.bust import BustDefinition, apply_bust_labels, fit_bust_thresholds
from ml.models.training import ModelBundle, load_model_bundle, save_model_bundle, temporal_split, train_model_bundle
from ml.preprocessing.validation import validate_weather_frame
from ml.verification.metrics import add_error_columns, summarize_verification


class ForecastBustPipeline:
    def __init__(self, model_dir: str | Path = "models/checkpoints", data_dir: str | Path = "data/synthetic") -> None:
        self.model_dir, self.data_dir = Path(model_dir), Path(data_dir)

    @property
    def data_path(self) -> Path: return self.data_dir / "synthetic_verified.csv"

    @property
    def metrics_path(self) -> Path: return self.model_dir.parent / "metadata" / "evaluation.json"

    def generate_synthetic(self, cycles: int = 180, seed: int = 42) -> pd.DataFrame:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        data = SyntheticDataProvider(cycles=cycles, seed=seed).full_verified_data()
        validate_weather_frame(data, require_observation=True)
        data.to_csv(self.data_path, index=False)
        return data

    def load_verified(self) -> pd.DataFrame:
        if not self.data_path.exists(): return self.generate_synthetic()
        data = pd.read_csv(self.data_path)
        return validate_weather_frame(data, require_observation=True)

    def prepare_features(self, data: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        verified = add_error_columns(data if data is not None else self.load_verified())
        # Fit fixed thresholds exclusively from the earlier temporal training period.
        raw_train, _ = temporal_split(verified)
        thresholds = fit_bust_thresholds(raw_train, BustDefinition(percentile=.90))
        labelled = apply_bust_labels(verified, thresholds)
        return build_feature_table(labelled), thresholds

    def train(self, force: bool = False) -> tuple[ModelBundle, dict[str, Any]]:
        model_path = self.model_dir / "forecast_bust_bundle.joblib"
        if model_path.exists() and not force:
            bundle = load_model_bundle(self.model_dir)
            return bundle, self.load_metrics()
        features, thresholds = self.prepare_features()
        bundle, _, test = train_model_bundle(features)
        predicted_error, probability = bundle.predict(test)
        results = test.copy()
        results["predicted_error"], results["bust_probability"] = predicted_error, probability
        evaluation = evaluate_predictions(results)
        evaluation["bust_thresholds"] = thresholds.to_dict(orient="records")
        evaluation["global_feature_importance"] = global_feature_importance(bundle)
        save_model_bundle(bundle, self.model_dir)
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        self.metrics_path.write_text(json.dumps(evaluation, indent=2, default=str), encoding="utf-8")
        return bundle, evaluation

    def load_metrics(self) -> dict[str, Any]:
        if not self.metrics_path.exists(): return {}
        return json.loads(self.metrics_path.read_text(encoding="utf-8"))

    def predict_latest(self, variable: str | None = None, lead_day: int | None = None) -> pd.DataFrame:
        bundle, _ = self.train()
        features, _ = self.prepare_features()
        latest_cycle = features.forecast_initialization_time.max()
        selected = features[features.forecast_initialization_time == latest_cycle].copy()
        if variable: selected = selected[selected.variable == variable]
        if lead_day: selected = selected[selected.lead_day == lead_day]
        if selected.empty: raise ValueError("No records match selected variable and lead day")
        expected_error, probability = bundle.predict(selected)
        selected["expected_error"] = expected_error
        selected["bust_probability"] = probability
        reliability = (1 - (selected.historical_mae / selected.bust_threshold.clip(lower=1e-6))).clip(0, 1).fillna(.5)
        calibration_quality = 1 - min(1, self.load_metrics().get("overall", {}).get("brier_score", .25) / .25)
        selected["confidence_score"] = 100 * (.55 * (1 - probability) + .25 * reliability + .15 * selected.data_quality + .05 * calibration_quality)
        selected["confidence_score"] = selected.confidence_score.clip(0, 100)
        selected["risk_level"] = pd.cut(selected.bust_probability, bins=[-0.01, .25, .5, .75, 1.0], labels=["LOW", "MODERATE", "HIGH", "SEVERE"]).astype(str)
        selected["model_version"] = bundle.metadata["model_version"]
        selected["prediction_timestamp"] = pd.Timestamp.now(tz="UTC")
        selected["source_status"] = "SYNTHETIC — development only"
        return selected

    def region_predictions(self, variable: str | None = None, lead_day: int | None = None) -> pd.DataFrame:
        predictions = self.predict_latest(variable, lead_day)
        aggregation = predictions.groupby(["region_id", "region_name", "variable", "lead_day"], as_index=False).agg(
            latitude=("latitude", "mean"), longitude=("longitude", "mean"), expected_error=("expected_error", "mean"),
            bust_probability=("bust_probability", "mean"), confidence_score=("confidence_score", "mean"),
            data_quality=("data_quality", "mean"), forecast_initialization_time=("forecast_initialization_time", "first"),
            model_version=("model_version", "first"), data_mode=("data_mode", "first"), source_status=("source_status", "first"),
        )
        aggregation["risk_level"] = pd.cut(aggregation.bust_probability, bins=[-0.01, .25, .5, .75, 1.0], labels=["LOW", "MODERATE", "HIGH", "SEVERE"]).astype(str)
        aggregation["error_prone"] = aggregation.bust_probability >= .5
        return aggregation

    def explanation(self, region_id: str, variable: str = "precipitation", lead_day: int = 5) -> dict[str, Any]:
        bundle, _ = self.train()
        features, _ = self.prepare_features()
        latest = features[(features.forecast_initialization_time == features.forecast_initialization_time.max()) & (features.region_id == region_id) & (features.variable == variable) & (features.lead_day == lead_day)]
        if latest.empty: raise ValueError("No prediction is available for this region/variable/lead day")
        result = explain_prediction(bundle, latest.iloc[[0]])
        result.update({"region_id": region_id, "variable": variable, "lead_day": lead_day, "data_mode": "synthetic"})
        return result

    def verification_summary(self) -> pd.DataFrame:
        return summarize_verification(self.load_verified())

    def predict_request(self, record: dict[str, Any]) -> dict[str, Any]:
        """Score a schema-validated single forecast; no observation/error fields are accepted."""
        bundle, _ = self.train()
        if record["data_mode"] != bundle.metadata["data_mode"]:
            raise ValueError("This model was trained on synthetic data and cannot score real-data requests")
        frame = pd.DataFrame([{**record, "model_identifier": "api_submission", "ensemble_member": None}])
        features = build_feature_table(frame)
        expected_error, probability = bundle.predict(features)
        calibration_quality = 1 - min(1, self.load_metrics().get("overall", {}).get("brier_score", .25) / .25)
        confidence = 100 * (.55 * (1 - probability[0]) + .25 * .5 + .15 * record["data_quality"] + .05 * calibration_quality)
        output = {"expected_error": float(expected_error[0]), "bust_probability": float(probability[0]), "confidence_score": float(min(100, max(0, confidence))), "model_version": bundle.metadata["model_version"], "data_mode": record["data_mode"], "source_status": "SYNTHETIC — development only"}
        output["risk_level"] = "SEVERE" if output["bust_probability"] >= .75 else "HIGH" if output["bust_probability"] >= .5 else "MODERATE" if output["bust_probability"] >= .25 else "LOW"
        return output


def bootstrap_demo(force: bool = False) -> dict[str, Any]:
    pipeline = ForecastBustPipeline()
    if force or not pipeline.data_path.exists(): pipeline.generate_synthetic()
    _, metrics = pipeline.train(force=force)
    output = pipeline.region_predictions(variable="precipitation", lead_day=5)
    return {"metrics": metrics, "sample_predictions": output.to_dict(orient="records")}
