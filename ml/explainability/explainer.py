from __future__ import annotations

import numpy as np
import pandas as pd

from ml.features.engineering import model_matrix
from ml.models.training import ModelBundle


def _classifier_estimator(bundle: ModelBundle):
    classifier = bundle.classifier
    return getattr(classifier, "estimator", classifier)


def global_feature_importance(bundle: ModelBundle) -> list[dict]:
    estimator = _classifier_estimator(bundle)
    values = getattr(estimator, "feature_importances_", None)
    if values is None: return [{"feature": feature, "importance": 0.0} for feature in bundle.feature_columns]
    return sorted(({"feature": feature, "importance": float(value)} for feature, value in zip(bundle.feature_columns, values)), key=lambda value: value["importance"], reverse=True)


def explain_prediction(bundle: ModelBundle, row: pd.DataFrame, top_n: int = 5) -> dict:
    values = model_matrix(row)[bundle.feature_columns]
    try:
        import shap
        estimator = _classifier_estimator(bundle)
        shap_values = shap.TreeExplainer(estimator).shap_values(values)
        if isinstance(shap_values, list): shap_values = shap_values[-1]
        contributions = np.asarray(shap_values)[0]
        method = "shap_tree"
    except Exception:
        # Transparent fallback for unavailable/incompatible SHAP installations.
        estimator = _classifier_estimator(bundle)
        weights = getattr(estimator, "feature_importances_", np.ones(len(bundle.feature_columns)))
        contributions = (values.iloc[0].to_numpy() - values.mean(axis=0).to_numpy()) * np.asarray(weights)
        method = "feature_importance_fallback"
    top = sorted(({"feature": feature, "contribution": float(score), "direction": "increases risk" if score >= 0 else "decreases risk"} for feature, score in zip(bundle.feature_columns, contributions)), key=lambda item: abs(item["contribution"]), reverse=True)[:top_n]
    return {"method": method, "disclaimer": "Feature contributions are associations with the model prediction, not physical causation.", "top_factors": top}
