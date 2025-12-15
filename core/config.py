# core/config.py
from pydantic_settings import BaseSettings
from typing import List
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
    ALLOWED_ORIGINS: List[str] = ["*"]

    # === SEGURANÇA ===
    SECRET_KEY: str | None = None

    # === DATABASE ===
    NEON_DATABASE_URL: str | None = None

    # === ADMIN SEED ===
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None

    class Config:
        env_file = ".env"

        @classmethod
        def parse_env_var(cls, field_name: str, raw_value: str):
            """
            Permite usar:
            ALLOWED_ORIGINS=*
            ou
            ALLOWED_ORIGINS=["https://site.com"]
            """
            if field_name == "ALLOWED_ORIGINS":
                if raw_value == "*":
                    return ["*"]
                try:
                    return json.loads(raw_value)
                except Exception:
                    return [raw_value]

            return raw_value


settings = Settings()
