"""
Core configuration module for Project Handler.
Manages environment variables and application settings.
"""
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    anthropic_api_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    sendgrid_api_key: str = ""
    stripe_secret_key: str = ""
    google_maps_api_key: str = ""

    # Database Configuration
    database_url: str = "postgresql://admin:secure_password@localhost:5432/project_handler"
    redis_url: str = "redis://localhost:6379"

    # Application Configuration
    environment: str = "development"
    debug: bool = True
    api_port: int = 8000
    api_host: str = "0.0.0.0"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Settings: Application configuration instance
    """
    return Settings()
