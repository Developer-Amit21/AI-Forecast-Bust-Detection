from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.inference.pipeline import ForecastBustPipeline


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate clearly labelled synthetic forecast/observation records")
    parser.add_argument("--cycles", type=int, default=180); parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    data = ForecastBustPipeline().generate_synthetic(args.cycles, args.seed)
    print(f"Wrote {len(data):,} SYNTHETIC records to data/synthetic/synthetic_verified.csv")
