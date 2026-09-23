from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (average_precision_score, brier_score_loss, f1_score, mean_absolute_error,
                             mean_squared_error, precision_score, r2_score, recall_score, roc_auc_score)


def _safe_metric(fn, *args, **kwargs) -> float:
    try: return float(fn(*args, **kwargs))
    except ValueError: return float("nan")


def evaluate_predictions(frame: pd.DataFrame) -> dict:
    actual_error, predicted_error = frame.absolute_error, frame.predicted_error
    actual_bust, probability = frame.bust_binary.astype(int), frame.bust_probability
    classification = (probability >= .5).astype(int)
    metrics = {
        "mae": float(mean_absolute_error(actual_error, predicted_error)),
        "rmse": float(np.sqrt(mean_squared_error(actual_error, predicted_error))),
        "r2": _safe_metric(r2_score, actual_error, predicted_error),
        "bias": float((predicted_error - actual_error).mean()),
        "precision": _safe_metric(precision_score, actual_bust, classification, zero_division=0),
        "recall": _safe_metric(recall_score, actual_bust, classification, zero_division=0),
        "f1": _safe_metric(f1_score, actual_bust, classification, zero_division=0),
        "roc_auc": _safe_metric(roc_auc_score, actual_bust, probability),
        "pr_auc": _safe_metric(average_precision_score, actual_bust, probability),
        "brier_score": _safe_metric(brier_score_loss, actual_bust, probability),
    }
    by_lead = []
    for (variable, lead_day), group in frame.groupby(["variable", "lead_day"]):
        by_lead.append({"variable": variable, "lead_day": int(lead_day), "mae": float(mean_absolute_error(group.absolute_error, group.predicted_error)), "brier_score": _safe_metric(brier_score_loss, group.bust_binary, group.bust_probability)})
    return {"overall": metrics, "by_variable_lead": by_lead}
