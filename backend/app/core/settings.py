from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # API Keys
    COINMARKETCAP_API_KEY: str
    MASSIVE_API_KEY: str
    FINNHUB_API_KEY: str
    TWELVEDATA_API_KEY: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # App
    APP_ENV: str = "development"
    DEBUG: bool = True

    JWT_SECRET: str
    JWT_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()