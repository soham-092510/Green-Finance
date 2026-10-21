# =====================================================================
# GREEN-FINANCE — LOGGING_MIDDLEWARE.PY
# Purpose: Logs request performance and feeds sliding window event counters
#          for the Real-Time Operations Control Center.
# =====================================================================

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from backend.middleware.logger import logger
from backend.services.operations_service import ops_tracker


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Track operational telemetry metrics
        status_code = response.status_code
        path = request.url.path

        if status_code >= 500:
            ops_tracker.record_event("errors_5xx")
        elif status_code >= 400:
            ops_tracker.record_event("errors_4xx")

        if path.startswith("/auth/login"):
            ops_tracker.record_event("logins")
        elif path.startswith("/auth/register") and status_code in (200, 201):
            ops_tracker.record_event("registrations")
        elif path.startswith("/payment/transfer") and status_code == 200:
            ops_tracker.record_event("transactions")

        logger.info(
            f"{request.method} {request.url.path} "
            f"status={status_code} duration={duration_ms}ms"
        )
        return response
