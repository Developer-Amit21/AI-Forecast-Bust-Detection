import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.inference.pipeline import ForecastBustPipeline
from ml.verification.metrics import add_error_columns, summarize_verification

if __name__ == "__main__":
    data = add_error_columns(ForecastBustPipeline().load_verified())
    print(summarize_verification(data).to_string(index=False))
