from ml.inference.pipeline import ForecastBustPipeline
from ml.models.training import train_model_bundle


def test_model_bundle_predicts_probabilities():
    pipeline = ForecastBustPipeline(data_dir="data/synthetic")
    data = pipeline.generate_synthetic(cycles=32, seed=11)
    features, _ = pipeline.prepare_features(data)
    bundle, _, test = train_model_bundle(features, test_fraction=.25)
    errors, probabilities = bundle.predict(test.head(8))
    assert (errors >= 0).all()
    assert ((probabilities >= 0) & (probabilities <= 1)).all()
