import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.inference.pipeline import ForecastBustPipeline

if __name__ == "__main__":
    features, thresholds = ForecastBustPipeline().prepare_features()
    print("Fitted historical training thresholds:")
    print(thresholds.to_string(index=False)); print(f"Labelled {len(features):,} records.")
