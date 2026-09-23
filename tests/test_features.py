from ml.features.engineering import FEATURE_COLUMNS, build_feature_table
from ml.inference.pipeline import ForecastBustPipeline


def test_features_exclude_current_observation_and_error():
    raw = ForecastBustPipeline().generate_synthetic(cycles=8, seed=8)
    features, _ = ForecastBustPipeline().prepare_features(raw)
    assert set(FEATURE_COLUMNS).isdisjoint({"observation_value", "absolute_error", "signed_error", "bust_binary"})
    assert set(FEATURE_COLUMNS).issubset(features.columns)
