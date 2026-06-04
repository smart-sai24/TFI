from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic

from fastapi import HTTPException, Request, status


@dataclass
class RateLimitBucket:
    attempts: list[float] = field(default_factory=list)


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, RateLimitBucket] = {}

    def check(self, key: str, *, limit: int, window_seconds: int) -> None:
        now = monotonic()
        bucket = self._buckets.setdefault(key, RateLimitBucket())
        bucket.attempts = [timestamp for timestamp in bucket.attempts if now - timestamp < window_seconds]
        if len(bucket.attempts) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail='Too many login attempts. Please wait and try again.',
            )
        bucket.attempts.append(now)

    def reset(self, key: str) -> None:
        self._buckets.pop(key, None)


login_rate_limiter = InMemoryRateLimiter()


def login_rate_limit_key(request: Request, email: str) -> str:
    forwarded_for = request.headers.get('x-forwarded-for', '')
    ip_address = forwarded_for.split(',', 1)[0].strip() or (request.client.host if request.client else 'unknown')
    return f'{ip_address}:{email.strip().lower()}'
