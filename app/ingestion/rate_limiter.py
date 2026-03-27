"""Per-domain rate limiter for async HTTP requests.

Prevents hammering individual domains when ingesting from 100+ sources.
Uses asyncio semaphores per domain with configurable concurrency and
minimum delay between requests to the same host.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Default settings — tunable per tier
DEFAULT_DOMAIN_CONCURRENCY = 2  # Max simultaneous requests per domain
DEFAULT_GLOBAL_CONCURRENCY = 20  # Max simultaneous requests total
DEFAULT_DOMAIN_DELAY_SEC = 1.0  # Min seconds between requests to same domain
TIER1_GLOBAL_CONCURRENCY = 30  # Tier 1 runs hotter


class DomainRateLimiter:
    """Async rate limiter that enforces per-domain and global concurrency."""

    def __init__(
        self,
        *,
        domain_concurrency: int = DEFAULT_DOMAIN_CONCURRENCY,
        global_concurrency: int = DEFAULT_GLOBAL_CONCURRENCY,
        domain_delay: float = DEFAULT_DOMAIN_DELAY_SEC,
    ) -> None:
        self._domain_concurrency = domain_concurrency
        self._domain_delay = domain_delay
        self._global_sem = asyncio.Semaphore(global_concurrency)
        self._domain_sems: dict[str, asyncio.Semaphore] = defaultdict(
            lambda: asyncio.Semaphore(domain_concurrency)
        )
        self._domain_last_request: dict[str, float] = defaultdict(float)
        self._lock = asyncio.Lock()

    def _extract_domain(self, url: str) -> str:
        """Extract hostname from URL for rate limiting key."""
        parsed = urlparse(url)
        return parsed.hostname or "unknown"

    async def acquire(self, url: str) -> None:
        """Wait until we're allowed to make a request to this URL's domain."""
        domain = self._extract_domain(url)

        # Global concurrency gate
        await self._global_sem.acquire()

        # Per-domain concurrency gate
        await self._domain_sems[domain].acquire()

        # Per-domain delay enforcement
        async with self._lock:
            now = time.monotonic()
            last = self._domain_last_request[domain]
            wait = self._domain_delay - (now - last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._domain_last_request[domain] = time.monotonic()

    def release(self, url: str) -> None:
        """Release both domain and global semaphores after request completes."""
        domain = self._extract_domain(url)
        self._domain_sems[domain].release()
        self._global_sem.release()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class RateLimitedContext:
    """Context manager for a single rate-limited request."""

    def __init__(self, limiter: DomainRateLimiter, url: str) -> None:
        self._limiter = limiter
        self._url = url

    async def __aenter__(self):
        await self._limiter.acquire(self._url)
        return self

    async def __aexit__(self, *args):
        self._limiter.release(self._url)


def throttled(limiter: DomainRateLimiter, url: str) -> RateLimitedContext:
    """Convenience: ``async with throttled(limiter, url): ...``"""
    return RateLimitedContext(limiter, url)


# Singleton limiters per tier — created lazily
_tier_limiters: dict[int, DomainRateLimiter] = {}


def get_tier_limiter(tier: int) -> DomainRateLimiter:
    """Get or create a rate limiter tuned for a specific tier."""
    if tier not in _tier_limiters:
        if tier == 1:
            _tier_limiters[tier] = DomainRateLimiter(
                domain_concurrency=3,
                global_concurrency=TIER1_GLOBAL_CONCURRENCY,
                domain_delay=0.5,
            )
        elif tier == 2:
            _tier_limiters[tier] = DomainRateLimiter(
                domain_concurrency=2,
                global_concurrency=DEFAULT_GLOBAL_CONCURRENCY,
                domain_delay=1.0,
            )
        elif tier == 3:
            _tier_limiters[tier] = DomainRateLimiter(
                domain_concurrency=1,
                global_concurrency=10,
                domain_delay=2.0,
            )
        else:
            _tier_limiters[tier] = DomainRateLimiter(
                domain_concurrency=1,
                global_concurrency=5,
                domain_delay=3.0,
            )
    return _tier_limiters[tier]
