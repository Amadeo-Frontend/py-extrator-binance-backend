from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
import json

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
    ALLOWED_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    # === AUTH / DB ===
    SECRET_KEY: str | None = None
    NEON_DATABASE_URL: str | None = None

    # === ADMIN SEED ===
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
