from __future__ import annotations

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression


def logistic_baseline() -> LogisticRegression:
    return LogisticRegression(max_iter=500, class_weight="balanced", random_state=42)


def random_forest_baseline_classifier() -> RandomForestClassifier:
    return RandomForestClassifier(n_estimators=150, min_samples_leaf=3, class_weight="balanced", n_jobs=-1, random_state=42)


def random_forest_baseline_regressor() -> RandomForestRegressor:
    return RandomForestRegressor(n_estimators=150, min_samples_leaf=3, n_jobs=-1, random_state=42)
