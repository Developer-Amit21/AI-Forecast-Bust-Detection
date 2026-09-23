from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit

from ml.features.engineering import FEATURE_COLUMNS, model_matrix


@dataclass
class ModelBundle:
    regressor: Any
    classifier: Any
    feature_columns: list[str]
    metadata: dict[str, Any]

    def predict(self, features: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        matrix = model_matrix(features)[self.feature_columns]
        error = np.maximum(0, self.regressor.predict(matrix))
        probability = self.classifier.predict_proba(matrix)[:, 1]
        return error, probability


def _xgb_classifier(seed: int) -> tuple[Any, str]:
    try:
        from xgboost import XGBClassifier
        return XGBClassifier(n_estimators=180, max_depth=5, learning_rate=.06, subsample=.85,
                             colsample_bytree=.85, eval_metric="logloss", n_jobs=2, random_state=seed), "xgboost"
    except ImportError:
        return HistGradientBoostingClassifier(max_iter=180, learning_rate=.07, max_leaf_nodes=24, random_state=seed), "sklearn_fallback"


def _lightgbm_regressor(seed: int) -> tuple[Any, str]:
    try:
        from lightgbm import LGBMRegressor
        return LGBMRegressor(n_estimators=180, num_leaves=31, learning_rate=.06, subsample=.85,
                             colsample_bytree=.85, random_state=seed, n_jobs=2, verbosity=-1), "lightgbm"
    except ImportError:
        return HistGradientBoostingRegressor(max_iter=180, learning_rate=.07, max_leaf_nodes=24, random_state=seed), "sklearn_fallback"


def temporal_split(features: pd.DataFrame, test_fraction: float = .2) -> tuple[pd.DataFrame, pd.DataFrame]:
    cycles = np.sort(pd.to_datetime(features.forecast_initialization_time, utc=True).unique())
    boundary = max(1, int(len(cycles) * (1 - test_fraction)))
    train_cycles = set(cycles[:boundary])
    train = features[features.forecast_initialization_time.isin(train_cycles)].copy()
    test = features[~features.forecast_initialization_time.isin(train_cycles)].copy()
    if train.empty or test.empty: raise ValueError("Temporal split requires at least two forecast cycles")
    return train, test


def train_model_bundle(features: pd.DataFrame, model_version: str = "synthetic_bust_v1",
                       test_fraction: float = .2, seed: int = 42) -> tuple[ModelBundle, pd.DataFrame, pd.DataFrame]:
    required = {"absolute_error", "bust_binary", "forecast_initialization_time"}
    if missing := required.difference(features.columns): raise ValueError(f"Training data missing {sorted(missing)}")
    train, test = temporal_split(features, test_fraction)
    x_train, x_test = model_matrix(train), model_matrix(test)
    y_error, y_bust = train.absolute_error.astype(float), train.bust_binary.astype(int)
    if y_bust.nunique() < 2: raise ValueError("Training history does not contain both bust classes")
    base_classifier, classifier_backend = _xgb_classifier(seed)
    regressor, regressor_backend = _lightgbm_regressor(seed)
    regressor.fit(x_train, y_error)
    # Time-aware folds preserve cycle ordering during calibration.
    calibrator = CalibratedClassifierCV(base_classifier, method="sigmoid", cv=TimeSeriesSplit(n_splits=3))
    calibrator.fit(x_train, y_bust)
    metadata = {
        "model_version": model_version, "classifier_backend": classifier_backend,
        "regressor_backend": regressor_backend, "feature_version": "v1",
        "training_period": f"{train.forecast_initialization_time.min().isoformat()} → {train.forecast_initialization_time.max().isoformat()}",
        "holdout_period": f"{test.forecast_initialization_time.min().isoformat()} → {test.forecast_initialization_time.max().isoformat()}",
        "data_mode": str(features.data_mode.iloc[0]),
    }
    bundle = ModelBundle(regressor=regressor, classifier=calibrator, feature_columns=FEATURE_COLUMNS, metadata=metadata)
    return bundle, train, test


def save_model_bundle(bundle: ModelBundle, directory: str | Path = "models/checkpoints") -> Path:
    target = Path(directory); target.mkdir(parents=True, exist_ok=True)
    model_path = target / "forecast_bust_bundle.joblib"
    joblib.dump(bundle, model_path)
    metadata_path = target.parent / "metadata" / "model_metadata.json"; metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(bundle.metadata, indent=2), encoding="utf-8")
    return model_path


def load_model_bundle(directory: str | Path = "models/checkpoints") -> ModelBundle:
    path = Path(directory) / "forecast_bust_bundle.joblib"
    if not path.exists(): raise FileNotFoundError("Model unavailable. Run scripts/train_model.py first.")
    return joblib.load(path)
