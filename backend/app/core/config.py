"""
Configuration settings for the NWP Forecast Bust Detection & Confidence System.
"""
from pathlib import Path
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "AeroCast BustSentinel"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Regional Grid: South Asia / Indian Domain (5°N - 38°N, 65°E - 100°E)
    LAT_MIN: float = 5.0
    LAT_MAX: float = 38.0
    LON_MIN: float = 65.0
    LON_MAX: float = 100.0
    RESOLUTION_DEG: float = 1.0  # 34 lats x 36 lons = 1,224 points
    
    # Temporal Lead Times
    MIN_LEAD_DAY: int = 1
    MAX_LEAD_DAY: int = 10
    
    # Meteorological Channels
    CHANNELS: list[str] = ["pwat", "z500", "mslp", "vort850", "precip"]
    CHANNEL_NAMES: dict[str, str] = {
        "pwat": "Precipitable Water (kg/m²)",
        "z500": "500 hPa Geopotential Height (gpm)",
        "mslp": "Mean Sea Level Pressure (hPa)",
        "vort850": "850 hPa Relative Vorticity (10⁻⁵ s⁻¹)",
        "precip": "24h Accumulated Rainfall (mm)"
    }
    
    # Normalization constants (approximate climatological mean and std)
    NORM_PARAMS: dict[str, dict[str, float]] = {
        "pwat": {"mean": 38.0, "std": 15.0},
        "z500": {"mean": 5820.0, "std": 65.0},
        "mslp": {"mean": 1008.0, "std": 6.5},
        "vort850": {"mean": 2.5, "std": 5.0},
        "precip": {"mean": 15.0, "std": 25.0}
    }
    
    # Operational Bust Thresholds
    RAIN_BUST_THRESHOLD_MM: float = 45.0
    HIGH_BUST_RISK_THRESHOLD: float = 0.65
    WATCH_BUST_RISK_THRESHOLD: float = 0.35
    LOW_CONFIDENCE_THRESHOLD: float = 0.40
    
    # File Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    MODEL_WEIGHTS_PATH: Path = DATA_DIR / "model_weights.pt"
    
    # Scenarios available out-of-the-box
    SCENARIOS: dict[str, str] = {
        "western_disturbance": "Western Disturbance Mid-Latitude Trough Deepening",
        "monsoon_depression": "North Bay of Bengal Monsoon Depression Track Divergence",
        "monsoon_break": "Monsoon Break Phase Foothills Shift & Central Drought",
        "climatology": "Quiescent Active Monsoon Baseline"
    }

settings = Settings()
