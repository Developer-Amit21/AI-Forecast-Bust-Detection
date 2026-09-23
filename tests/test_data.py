from ml.ingestion.providers import SyntheticDataProvider
from ml.preprocessing.validation import validate_weather_frame


def test_synthetic_data_meets_common_schema():
    data = SyntheticDataProvider(cycles=8, seed=7).full_verified_data()
    validated = validate_weather_frame(data, require_observation=True)
    assert len(validated) == 8 * 8 * 3 * 10 * 3
    assert set(validated.data_mode) == {"synthetic"}
