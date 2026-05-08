from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

import httpx

from app.core.config import Settings
from app.core.errors import APIError

RATE_BUCKETS: dict[str, deque[datetime]] = defaultdict(deque)


def enforce_rate_limit(*, key: str, limit: int, window_seconds: int, settings: Settings | None = None) -> None:
    if settings and settings.upstash_redis_rest_url and settings.upstash_redis_rest_token:
        try:
            _enforce_rate_limit_upstash(
                key=key,
                limit=limit,
                window_seconds=window_seconds,
                settings=settings,
            )
            return
        except Exception:
            pass
    _enforce_rate_limit_local(key=key, limit=limit, window_seconds=window_seconds)


def _enforce_rate_limit_local(*, key: str, limit: int, window_seconds: int) -> None:
    now = datetime.now(UTC)
    cutoff = now - timedelta(seconds=window_seconds)
    bucket = RATE_BUCKETS[key]
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= limit:
        raise APIError(429, "rate_limited", "Too many requests.")
    bucket.append(now)


def _enforce_rate_limit_upstash(*, key: str, limit: int, window_seconds: int, settings: Settings) -> None:
    redis_key = f"rate_limit:{key}"
    with httpx.Client(timeout=5) as client:
        response = client.post(
            f"{settings.upstash_redis_rest_url.rstrip('/')}/pipeline",
            headers={
                "Authorization": f"Bearer {settings.upstash_redis_rest_token}",
                "Content-Type": "application/json",
            },
            json=[
                ["INCR", redis_key],
                ["TTL", redis_key],
            ],
        )
        response.raise_for_status()
        results = response.json()
        current = int(results[0]["result"])
        ttl = int(results[1]["result"])
        if ttl < 0:
            expire_response = client.get(
                f"{settings.upstash_redis_rest_url.rstrip('/')}/expire/{redis_key}/{window_seconds}",
                headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"},
            )
            expire_response.raise_for_status()
    if current > limit:
        raise APIError(429, "rate_limited", "Too many requests.")
