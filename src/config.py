"""
Configuration management using Pydantic Settings.

All configuration values are loaded from environment variables.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "Project Orchestrator"
    app_env: str = "development"  # development, staging, production, test
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql+asyncpg://orchestrator:dev_password@localhost:5432/project_orchestrator"
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Anthropic API (for PydanticAI)
    anthropic_api_key: Optional[str] = None

    # Telegram Bot
    telegram_bot_token: Optional[str] = None

    # GitHub
    github_access_token: Optional[str] = None
    github_webhook_secret: Optional[str] = None

    # Redis (optional, for caching)
    redis_url: Optional[str] = None

    # Monitoring
    sentry_dsn: Optional[str] = None

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True  # Auto-reload in development

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()
