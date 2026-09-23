from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.inference.pipeline import ForecastBustPipeline


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train calibrated forecast-bust models with a temporal holdout")
    parser.add_argument("--force", action="store_true", help="Retrain even if a checkpoint exists")
    args = parser.parse_args()
    bundle, metrics = ForecastBustPipeline().train(force=args.force)
    print(json.dumps({"model": bundle.metadata, "metrics": metrics.get("overall", {})}, indent=2))
