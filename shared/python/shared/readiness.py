"""Reusable readiness probe with bounded database backoff.

Every KnowledgeOps Python service degrades gracefully to an in-memory fallback
when PostgreSQL is unavailable, so a service is always able to *serve* requests.
The readiness probe nonetheless re-checks the database with a short bounded
backoff so orchestrators (Kubernetes ``readinessProbe``, the API gateway health
aggregator) get an accurate, up-to-date picture of whether the persistent store
is reachable.

The probe never raises: a failing database simply reports ``database: "down"``
while the service stays ``ready`` in degraded mode.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


async def probe_database(
    check: Callable[[], Awaitable[bool]],
    *,
    retries: int = 3,
    base_delay: float = 0.05,
    max_delay: float = 0.5,
) -> bool:
    """Probe the database, retrying with exponential backoff.

    Args:
        check: Async callable returning ``True`` when the database is reachable.
        retries: Maximum number of attempts (must be >= 1).
        base_delay: Initial delay between attempts, in seconds.
        max_delay: Cap on the per-attempt delay, in seconds.

    Returns:
        ``True`` if any attempt succeeds, otherwise ``False``. Never raises.
    """
    attempts = max(1, retries)
    delay = base_delay
    for attempt in range(attempts):
        try:
            if await check():
                return True
        except Exception:
            # Treat any probe error as "not ready" and keep retrying.
            pass
        if attempt < attempts - 1:
            await asyncio.sleep(min(delay, max_delay))
            delay = min(delay * 2, max_delay)
    return False


async def readiness_payload(
    service_name: str,
    check: Callable[[], Awaitable[bool]],
    *,
    retries: int = 3,
    base_delay: float = 0.05,
    max_delay: float = 0.5,
) -> dict[str, Any]:
    """Build a standard readiness response for a service.

    The service is always reported ``ready`` because it can serve requests in
    its in-memory degraded mode; the ``database`` field communicates whether the
    persistent store is reachable.

    Args:
        service_name: Human-readable service identifier.
        check: Async callable that probes database availability.
        retries: Maximum probe attempts.
        base_delay: Initial backoff delay in seconds.
        max_delay: Cap on the per-attempt delay in seconds.

    Returns:
        A JSON-serialisable readiness dictionary.
    """
    db_ok = await probe_database(
        check, retries=retries, base_delay=base_delay, max_delay=max_delay
    )
    return {
        "ready": True,
        "service": service_name,
        "database": "up" if db_ok else "down",
        "mode": "persistent" if db_ok else "degraded",
    }
