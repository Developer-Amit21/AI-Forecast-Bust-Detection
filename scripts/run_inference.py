from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.inference.pipeline import ForecastBustPipeline, bootstrap_demo


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the synthetic forecast-bust inference demo")
    parser.add_argument("--bootstrap", action="store_true", help="Generate synthetic data and train before inference")
    parser.add_argument("--force", action="store_true", help="Regenerate/retrain demo artefacts")
    parser.add_argument("--variable", default="precipitation", choices=["precipitation", "temperature_2m", "wind_speed"])
    parser.add_argument("--lead-day", type=int, default=5, choices=range(1, 11))
    args = parser.parse_args()
    if args.bootstrap: bootstrap_demo(force=args.force)
    predictions = ForecastBustPipeline().region_predictions(args.variable, args.lead_day)
    print(json.dumps(predictions.to_dict(orient="records"), indent=2, default=str))
