from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # === BINANCE ===
    BINANCE_API_KEY: str | None = None
    BINANCE_API_SECRET: str | None = None

    # === POLYGON ===
    POLYGON_API_KEY: str | None = None

    # === ALPHA VANTAGE ===
    ALPHA_VANTAGE_API_KEY: str | None = None

    # === TRADINGVIEW ===
    TV_USERNAME: str | None = None
    TV_PASSWORD: str | None = None

    # === CORS ===
    ALLOWED_ORIGINS: List[str] = ["*"]

    # === AUTH / SECURITY ===
    SECRET_KEY: str
    NEON_DATABASE_URL: str

    # === ADMIN SEED ===
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None

    class Config:
        env_file = ".env"


# 🔥 ESTA LINHA É O QUE ESTAVA FALTANDO
settings = Settings()
