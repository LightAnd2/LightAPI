"""
Lightweight in-process rate limiting, keyed by client IP.

The app runs as a single instance (SQLite + one container), so an in-memory
sliding window is sufficient and needs no external store. Behind a proxy
(Render/Koyeb/Fly), the real client IP is the first entry of X-Forwarded-For.
"""
import time
from collections import defaultdict, deque

from fastapi import Request, HTTPException


def client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimiter:
    """Allow at most `max_requests` per `window_seconds` per client IP."""

    def __init__(self, max_requests: int, window_seconds: float):
        self.max = max_requests
        self.window = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)

    def __call__(self, request: Request):
        ip = client_ip(request)
        now = time.monotonic()
        dq = self._hits[ip]

        cutoff = now - self.window
        while dq and dq[0] <= cutoff:
            dq.popleft()

        if len(dq) >= self.max:
            retry = max(1, int(self.window - (now - dq[0])))
            raise HTTPException(
                status_code=429,
                detail="Too many requests — slow down.",
                headers={"Retry-After": str(retry)},
            )

        dq.append(now)

        # Opportunistic cleanup so idle IPs don't accumulate forever.
        if len(self._hits) > 10_000:
            for k in [k for k, v in self._hits.items() if not v]:
                del self._hits[k]
