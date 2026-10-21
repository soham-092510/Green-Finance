# =====================================================================
# GREEN-FINANCE — RATE_LIMIT.PY (RATE LIMITING & ABUSE DEFENSE)
# Purpose: Protects sensitive endpoints against brute force, credential
#          stuffing, and denial-of-service resource exhaustion:
#          - Tiered quotas for Auth, Banking Transfers, Reports, & Stress Tests
#          - Returns HTTP 429 Too Many Requests with Retry-After header
#          - Thread-safe sliding window in-memory backend with Redis extensibility
# =====================================================================

import time
import threading
from typing import Dict, List, Tuple, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from backend.middleware.logger import logger


class InMemoryRateLimiter:
    """Thread-safe sliding-window rate limiter."""

    def __init__(self):
        self._lock = threading.Lock()
        # Storage format: { (client_key, bucket_type): [timestamp, timestamp, ...] }
        self._buckets: Dict[Tuple[str, str], List[float]] = {}

    def is_allowed(self, client_key: str, bucket_type: str, max_requests: int, window_seconds: int = 60) -> Tuple[bool, int, int]:
        """
        Checks if the request is permitted within the rate limit window.
        Returns: (is_allowed, remaining_requests, retry_after_seconds)
        """
        now = time.time()
        window_start = now - window_seconds
        bucket_key = (client_key, bucket_type)

        with self._lock:
            timestamps = self._buckets.get(bucket_key, [])
            # Prune timestamps older than window_start
            timestamps = [ts for ts in timestamps if ts > window_start]

            if len(timestamps) >= max_requests:
                # Rate limit exceeded
                oldest = timestamps[0]
                retry_after = max(1, int(window_seconds - (now - oldest)))
                self._buckets[bucket_key] = timestamps
                return False, 0, retry_after

            # Record current request
            timestamps.append(now)
            self._buckets[bucket_key] = timestamps
            remaining = max_requests - len(timestamps)
            return True, remaining, 0

    def reset(self):
        """Resets all rate limit buckets (useful for test isolation)."""
        with self._lock:
            self._buckets.clear()


# Global limiter instance
limiter = InMemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    def get_client_ip(self, request: Request) -> str:
        """Safely extracts client IP address."""
        # Note: Do not blindly trust X-Forwarded-For unless from a verified trusted proxy
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        method = request.method
        client_ip = self.get_client_ip(request)

        # Skip rate limiting for static assets and metrics
        if (
            path.startswith("/shared")
            or path.startswith("/bank.css")
            or path.startswith("/bank.js")
            or path.startswith("/investigator.css")
            or path.startswith("/investigator.js")
            or path.startswith("/styles.css")
            or path.startswith("/app.js")
            or path == "/health"
            or path == "/metrics"
        ):
            return await call_next(request)

        # Determine rate limit quota by route sensitivity
        bucket_type = "general"
        limit = 120  # default 120 req/min

        if path.startswith("/auth/login") or path.startswith("/auth/register"):
            bucket_type = "auth"
            limit = 15  # 15 req/min for auth endpoints
        elif path.startswith("/payment/transfer"):
            bucket_type = "transfers"
            limit = 30  # 30 transfers/min
        elif path.startswith("/payment/stimulate") or path.startswith("/payment/benchmark"):
            bucket_type = "stress_tests"
            limit = 5   # 5 stress test runs/min
        elif "/report/pdf" in path or "/report/csv" in path or "/report" in path:
            bucket_type = "reports"
            limit = 10  # 10 report exports/min

        allowed, remaining, retry_after = limiter.is_allowed(client_ip, bucket_type, max_requests=limit, window_seconds=60)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded | Client IP: {client_ip} | Endpoint: {path} | Quota: {bucket_type} ({limit}/min)"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": f"Rate limit exceeded for {bucket_type}. Please slow down.",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0"
                }
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
