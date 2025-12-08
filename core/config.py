from pydantic import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Origens que podem acessar sua API (CORS)
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://nextjs-extrator-binance-frontend.vercel.app",
    ]

    # URL do banco Neon (você já usa isso nos routers)
    NEON_DATABASE_URL: str | None = None

    # Chaves de APIs externas (opcionalmente centralizadas aqui)
    POLYGON_API_KEY: str | None = None
    ALPHA_VANTAGE_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"  # ignora variáveis extra


settings = Settings()

