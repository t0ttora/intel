"""Remote HTTP client for CLI remote mode (when NOBLE_INTEL_URL is set)."""
from __future__ import annotations

import os
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _get_base_url() -> str:
    """Get the remote API base URL from environment."""
    url = os.environ.get("NOBLE_INTEL_URL", "")
    if not url:
        raise RuntimeError(
            "NOBLE_INTEL_URL not set. Set it to the remote Intel API URL "
            "or run in local mode (unset NOBLE_INTEL_URL)."
        )
    return url.rstrip("/")


def _get_api_key() -> str:
    """Get the API key from environment."""
    key = os.environ.get("INTEL_API_KEY", "")
    if not key:
        raise RuntimeError("INTEL_API_KEY not set for remote mode.")
    return key


def _headers() -> dict[str, str]:
    """Build request headers with API key."""
    return {
        "X-API-Key": _get_api_key(),
        "Content-Type": "application/json",
    }


def remote_get(path: str, params: dict | None = None) -> dict[str, Any]:
    """Synchronous GET request to remote API."""
    url = f"{_get_base_url()}{path}"
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.get(url, headers=_headers(), params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        logger.error(f"Remote API error: {exc.response.status_code} {exc.response.text}")
        raise RuntimeError(f"Remote API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        logger.error(f"Remote connection error: {exc}")
        raise RuntimeError(f"Cannot connect to {url}") from exc


def remote_post(path: str, data: dict | None = None) -> dict[str, Any]:
    """Synchronous POST request to remote API."""
    url = f"{_get_base_url()}{path}"
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=_headers(), json=data or {})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        logger.error(f"Remote API error: {exc.response.status_code} {exc.response.text}")
        raise RuntimeError(f"Remote API error: {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        logger.error(f"Remote connection error: {exc}")
        raise RuntimeError(f"Cannot connect to {url}") from exc


def remote_query(
    query: str,
    *,
    geo_zone: str | None = None,
    include_cascade: bool = True,
) -> dict[str, Any]:
    """Execute a remote intelligence query."""
    payload: dict[str, Any] = {
        "query": query,
        "include_cascade": include_cascade,
    }
    if geo_zone:
        payload["geo_zone"] = geo_zone

    return remote_post("/api/v1/query", data=payload)


async def async_remote_get(path: str, params: dict | None = None) -> dict[str, Any]:
    """Async GET request to remote API (used by TUI dashboard)."""
    url = f"{_get_base_url()}{path}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=_headers(), params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        logger.error(f"Async remote API error: {exc.response.status_code}")
        return {}
    except httpx.RequestError as exc:
        logger.error(f"Async remote connection error: {exc}")
        return {}
