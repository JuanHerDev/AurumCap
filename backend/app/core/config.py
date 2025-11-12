import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    ENV: str = os.getenv("ENV", "development")
    IS_PROD: bool = ENV == "production"
    DEBUG: bool = not IS_PROD

    # Backend URLs
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://127.0.0.1:3000")

    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # <-- AGREGA ESTO

    # CORS
    ALLOWED_ORIGINS = [
        FRONTEND_URL,
        "http://127.0.0.1:3000"
    ]

    # Security
    REFRESH_COOKIE_NAME = "aurum_refresh_token"
    REFRESH_COOKIE_PATH = "/auth"

settings = Settings()