from ml.inference.pipeline import ForecastBustPipeline


def test_end_to_end_synthetic_pipeline(tmp_path):
    pipeline = ForecastBustPipeline(model_dir=tmp_path / "models" / "checkpoints", data_dir=tmp_path / "data")
    pipeline.generate_synthetic(cycles=48, seed=12)
    bundle, metrics = pipeline.train(force=True)
    predictions = pipeline.region_predictions("precipitation", 5)
    assert bundle.metadata["data_mode"] == "synthetic"
    assert "mae" in metrics["overall"]
    assert len(predictions) == 8
    assert predictions.confidence_score.between(0, 100).all()
