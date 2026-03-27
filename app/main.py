"""FastAPI app — mounts all routers, startup/shutdown, health check."""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.dependencies import close_db_pool, close_qdrant, init_db_pool, init_qdrant

logger = logging.getLogger(__name__)

_start_time: float = 0.0


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown hooks."""
    global _start_time
    _start_time = time.time()

    settings = get_settings()

    # Init Sentry
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            traces_sample_rate=0.1,
            environment="production",
        )

    # Configure structured logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    logger.info("Starting Noble Intel v3.0.0")

    # Initialize services
    await init_db_pool(settings)
    logger.info("PostgreSQL pool ready")

    await init_qdrant(settings)
    logger.info("Qdrant client ready")

    yield

    # Shutdown
    logger.info("Shutting down Noble Intel")
    await close_qdrant()
    await close_db_pool()


app = FastAPI(
    title="Noble Intel",
    description="Adaptive Logistics Decision Engine",
    version="3.0.0",
    lifespan=lifespan,
)


# ── Global exception handler ─────────────────────────────────────────────


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled exceptions — log to Sentry, return generic error."""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": "An unexpected error occurred"},
    )


# ── Health check (no auth required) ──────────────────────────────────────


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint — no authentication required."""
    return {
        "status": "ok",
        "version": "3.0.0",
        "uptime_seconds": int(time.time() - _start_time),
    }


# ── Mount routers ────────────────────────────────────────────────────────

from app.api.intel_router import intel_router  # noqa: E402
from cli.server.router import cli_router  # noqa: E402

app.include_router(intel_router, prefix="", tags=["intel"])
app.include_router(cli_router, prefix="", tags=["cli"])
