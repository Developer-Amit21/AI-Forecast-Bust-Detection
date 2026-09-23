import pandas as pd

from ml.verification.metrics import add_error_columns, summarize_verification


def test_error_metrics_are_correct():
    frame = pd.DataFrame({"forecast_value": [1., 3.], "observation_value": [2., 1.], "variable": ["temperature_2m"] * 2, "lead_day": [1, 1]})
    checked = add_error_columns(frame)
    assert checked.absolute_error.tolist() == [1., 2.]
    assert summarize_verification(checked).iloc[0].mae == 1.5
