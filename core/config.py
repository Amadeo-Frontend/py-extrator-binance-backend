from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    NEON_DATABASE_URL: str
    SECRET_KEY: str = "changeme"

settings = Settings()
