import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Environment
    ENV: str = os.getenv("ENV", "development")
    IS_PROD: bool = ENV == "production"
    DEBUG: bool = not IS_PROD

    # URLs
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://127.0.0.1:3000")

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = f"{BACKEND_URL}/auth/oauth/google/callback"

    # CORS
    ALLOWED_ORIGINS: list = [
        FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    # Security
    REFRESH_COOKIE_NAME: str = "aurum_refresh_token"
    REFRESH_COOKIE_PATH: str = "/auth/refresh"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/aurumcap_dev")

settings = Settings()