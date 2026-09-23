import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.inference.pipeline import ForecastBustPipeline
from ml.preprocessing.validation import validate_weather_frame

if __name__ == "__main__":
    frame = validate_weather_frame(ForecastBustPipeline().load_verified(), require_observation=True)
    print(f"Validated {len(frame):,} records; common schema is ready for verification.")
