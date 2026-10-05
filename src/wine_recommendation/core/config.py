from __future__ import annotations

import os
from dataclasses import dataclass


def _bool_env(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://wine:wine@localhost:5432/wine"
    )
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    parser_timeout: float = float(os.getenv("PARSER_TIMEOUT", "15"))
    parser_user_agent: str = os.getenv("PARSER_USER_AGENT", "WineRecommendationMVP/0.1")
    parser_enabled: bool = _bool_env("PARSER_ENABLED")
    mock_json_data: str = os.getenv("MOCK_JSON_DATA", "")
    rating_weight: float = float(os.getenv("RANKING_RATING_WEIGHT", "0.55"))
    price_weight: float = float(os.getenv("RANKING_PRICE_WEIGHT", "0.25"))
    popularity_weight: float = float(os.getenv("RANKING_POPULARITY_WEIGHT", "0.20"))
    preference_boost: float = float(os.getenv("RANKING_PREFERENCE_BOOST", "0.05"))
    ml_personalization_weight: float = float(os.getenv("ML_PERSONALIZATION_WEIGHT", "0.65"))
    ml_train_on_startup: bool = _bool_env("ML_TRAIN_ON_STARTUP")


settings = Settings()
