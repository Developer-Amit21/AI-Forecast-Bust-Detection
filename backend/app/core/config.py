from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    data_mode: str = os.getenv("DATA_MODE", "synthetic")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./aerobust.db")
    cors_origins: tuple[str, ...] = tuple(
        value.strip()
        for value in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
        if value.strip()
    )
    model_dir: str = os.getenv("MODEL_DIR", "models/checkpoints")
    model_version: str = os.getenv("MODEL_VERSION", "synthetic_bust_v1")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    port: int = int(os.getenv("PORT", "8000"))


settings = Settings()
