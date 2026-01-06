"""
Configuration management using Pydantic Settings.

All configuration values are loaded from environment variables.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "Project Manager"
    app_env: str = "development"  # development, staging, production, test
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"
    debug: bool = False  # Legacy support for web UI

    # Database
    database_url: str = "postgresql+asyncpg://manager:dev_password@localhost:5432/project_manager"
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Anthropic API (for PydanticAI)
    anthropic_api_key: Optional[str] = None

    # Telegram Bot
    telegram_bot_token: Optional[str] = None
    telegram_webhook_url: Optional[str] = None  # Legacy support

    # GitHub
    github_access_token: Optional[str] = None
    github_token: Optional[str] = None  # Legacy alias
    github_webhook_secret: Optional[str] = None

    # Redis (optional, for caching)
    redis_url: Optional[str] = None

    # Monitoring
    sentry_dsn: Optional[str] = None

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True  # Auto-reload in development

    # Frontend (Web Interface)
    frontend_url: str = "http://localhost:3002"  # Vite dev server
    serve_frontend: bool = False  # Set to True in production

    # SCAR Project Import Settings
    scar_auto_import: bool = True  # Enable/disable auto-import on startup
    scar_import_repos: Optional[str] = None  # Comma-separated list of "owner/repo"
    scar_import_user: Optional[str] = None  # GitHub username to import all repos
    scar_import_org: Optional[str] = None  # GitHub org to import all repos
    scar_projects_config: str = ".scar/projects.json"  # Config file path

    # SCAR Integration (Test Adapter HTTP API)
    scar_base_url: str = "http://localhost:3000"  # SCAR Test Adapter base URL
    scar_timeout_seconds: int = 300  # Max wait time for SCAR command completion
    scar_conversation_prefix: str = "pm-project-"  # Conversation ID prefix

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()
