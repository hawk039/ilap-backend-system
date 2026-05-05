from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

from app.core.errors import APIError

RATE_BUCKETS: dict[str, deque[datetime]] = defaultdict(deque)


def enforce_rate_limit(*, key: str, limit: int, window_seconds: int) -> None:
    now = datetime.now(UTC)
    cutoff = now - timedelta(seconds=window_seconds)
    bucket = RATE_BUCKETS[key]
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= limit:
        raise APIError(429, "rate_limited", "Too many requests.")
    bucket.append(now)
