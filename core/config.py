from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    api_key_binance: str | None = None
    api_secret_binance: str | None = None

    api_key_polygon: str | None = None
    api_key_alphavantage: str | None = None

    jwt_secret: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
