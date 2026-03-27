"""Application settings loaded from environment variables."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """Noble Intel configuration — all secrets from .env."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Gemini
    gemini_api_key: str = Field(..., description="Google Gemini API key")

    # PostgreSQL
    database_url: str = Field(..., description="PostgreSQL connection URL")

    # Qdrant
    qdrant_url: str = Field(default="http://127.0.0.1:6333")
    qdrant_api_key: str = Field(default="", description="Qdrant API key (empty for local)")
    qdrant_collection: str = Field(default="intel_signals")

    # Redis
    redis_password: str = Field(default="", description="Redis password (empty for local)")
    redis_url: str = Field(default="redis://127.0.0.1:6379/0", description="Redis connection URL")

    # Supabase
    supabase_url: str = Field(default="", description="Supabase project URL (optional)")
    supabase_service_key: str = Field(default="", description="Supabase service role key (optional)")

    # Intel API
    intel_api_key: str = Field(..., description="API key for authenticating requests")
    intel_api_port: int = Field(default=8000)

    # Sentry
    sentry_dsn: str = Field(default="", description="Sentry DSN (optional)")

    # Proxy
    proxy_url: str | None = Field(default=None, description="HTTP proxy for scrapers")


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return cached settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings
