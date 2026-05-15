import time
import functools
import asyncio
from datetime import datetime
from typing import Optional
from lightai.client import send_async


def monitor(name: str = None, threshold_ms: Optional[int] = None, endpoint_id: Optional[str] = None):
    """
    Decorator that instruments any function and reports latency to LightAI.

    Usage:
        @monitor(name="get_odds", threshold_ms=200)
        def get_odds(league):
            ...

        @monitor(name="fetch_prices")
        async def fetch_prices(card_id):
            ...
    """
    def decorator(func):
        fn_name = name or f"{func.__module__}.{func.__qualname__}"

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.monotonic()
                success = True
                status_code = 200
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as exc:
                    success = False
                    status_code = 500
                    raise
                finally:
                    latency_ms = (time.monotonic() - start) * 1000
                    send_async({
                        "name": fn_name,
                        "endpoint_id": endpoint_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "latency_ms": round(latency_ms, 2),
                        "success": success,
                        "status_code": status_code,
                        "threshold_ms": threshold_ms,
                        "source": "sdk",
                    })
            return async_wrapper

        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start = time.monotonic()
                success = True
                status_code = 200
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as exc:
                    success = False
                    status_code = 500
                    raise
                finally:
                    latency_ms = (time.monotonic() - start) * 1000
                    send_async({
                        "name": fn_name,
                        "endpoint_id": endpoint_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "latency_ms": round(latency_ms, 2),
                        "success": success,
                        "status_code": status_code,
                        "threshold_ms": threshold_ms,
                        "source": "sdk",
                    })
            return sync_wrapper

    return decorator
