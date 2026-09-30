import os
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "FollowUpAI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Database & Cache
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/followup_db"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Authentication
    JWT_SECRET: str = "super_secret_jwt_key_change_in_production_1234567890"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Token Encryption Key (Fernet key, 32 url-safe base64-encoded bytes)
    ENCRYPTION_KEY: str = "87YkQz3t-N-mH9FvGqX1bWcR4eL0p_k5Z9xY8uV2w1A="

    # Email Integration Credentials
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/google/callback"
    BREVO_API_KEY: Optional[str] = None
    BREVO_SENDER_EMAIL: Optional[str] = "nikhilrajjatav@gmail.com"
    GMAIL_APP_PASSWORD: Optional[str] = None
    GMAIL_SENDER_EMAIL: Optional[str] = "nikhilrajjatav@gmail.com"
    EMAIL_PROVIDER: str = "brevo"  # brevo, gmail_smtp, gmail_oauth, or mock

    # AI Service Configuration
    AI_API_KEY: Optional[str] = None
    AI_PROVIDER: str = "openai"  # openai, gemini, or mock
    AI_MODEL: str = "gpt-4o-mini"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # File uploads
    UPLOAD_DIR: str = "uploads"

    model_config = SettingsConfigDict(
        env_file=[".env", "../.env"],
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
