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

    # === ADMIN ===
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None

    # === CORS ===
    ALLOWED_ORIGINS: List[str] = ["*"]

    # === OUTROS ===
    SECRET_KEY: str | None = None
    NEON_DATABASE_URL: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()
