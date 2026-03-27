"""FastAPI dependency injection — DB pool, Qdrant, Redis, API key auth."""
from __future__ import annotations

import logging
from typing import Annotated, AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool
from qdrant_client import AsyncQdrantClient

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

# ── Singletons (initialized in main.py startup) ──────────────────────────

_db_pool: AsyncConnectionPool | None = None
_qdrant: AsyncQdrantClient | None = None


async def init_db_pool(settings: Settings) -> AsyncConnectionPool:
    """Create and open the async connection pool."""
    global _db_pool
    _db_pool = AsyncConnectionPool(
        conninfo=settings.database_url,
        min_size=2,
        max_size=10,
        open=False,
    )
    await _db_pool.open()
    return _db_pool


async def close_db_pool() -> None:
    """Close the connection pool on shutdown."""
    global _db_pool
    if _db_pool is not None:
        await _db_pool.close()
        _db_pool = None


async def init_qdrant(settings: Settings) -> AsyncQdrantClient:
    """Create the Qdrant async client."""
    global _qdrant
    _qdrant = AsyncQdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        timeout=30,
    )
    return _qdrant


async def close_qdrant() -> None:
    """Close the Qdrant client on shutdown."""
    global _qdrant
    if _qdrant is not None:
        await _qdrant.close()
        _qdrant = None


# ── FastAPI Dependencies ──────────────────────────────────────────────────


async def get_db() -> AsyncGenerator[AsyncConnection, None]:
    """Yield an async DB connection from the pool."""
    if _db_pool is None:
        raise RuntimeError("Database pool not initialized")
    async with _db_pool.connection() as conn:
        yield conn


async def get_qdrant_client() -> AsyncQdrantClient:
    """Return the Qdrant async client."""
    if _qdrant is None:
        raise RuntimeError("Qdrant client not initialized")
    return _qdrant


def get_settings_dep() -> Settings:
    """Return application settings."""
    return get_settings()


async def verify_api_key(
    x_api_key: Annotated[str, Header()],
    settings: Settings = Depends(get_settings_dep),
) -> str:
    """Validate the X-API-Key header."""
    if not x_api_key or x_api_key != settings.intel_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return x_api_key


# Type aliases for dependency injection
DBConn = Annotated[AsyncConnection, Depends(get_db)]
QdrantDep = Annotated[AsyncQdrantClient, Depends(get_qdrant_client)]
SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
ApiKeyDep = Annotated[str, Depends(verify_api_key)]
