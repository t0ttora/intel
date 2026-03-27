"""Application settings loaded from environment variables."""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Noble Intel configuration — all secrets from .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Gemini
    gemini_api_key: str = Field(..., description="Google Gemini API key")

    # PostgreSQL
    database_url: str = Field(..., description="PostgreSQL connection URL")

    # Qdrant
    qdrant_url: str = Field(default="http://127.0.0.1:6333")
    qdrant_api_key: str = Field(..., description="Qdrant API key")
    qdrant_collection: str = Field(default="intel_signals")

    # Redis
    redis_password: str = Field(..., description="Redis password")
    redis_url: str = Field(..., description="Redis connection URL")

    # Supabase
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_service_key: str = Field(..., description="Supabase service role key")

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
