# =====================================================================
# GREEN-FINANCE — SECURITY_HEADERS.PY (DEFENSE IN DEPTH MIDDLEWARE)
# Purpose: Injects industry-standard security headers into all responses:
#          - Content-Security-Policy (CSP) with frame-ancestors 'none'
#          - X-Frame-Options: DENY (anti-clickjacking)
#          - X-Content-Type-Options: nosniff (anti-MIME sniffing)
#          - Referrer-Policy: strict-origin-when-cross-origin
#          - Permissions-Policy
# =====================================================================

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # 1. Prevent clickjacking by forbidding embedding in iframes
        response.headers["X-Frame-Options"] = "DENY"

        # 2. Prevent browser MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 3. Restrict referrer information sent with outbound links
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 4. Disable unwanted browser hardware features
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # 5. Content Security Policy (allows inline styles/scripts for Chart.js and Google Fonts while blocking framing and untrusted sources)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        # 6. HTTP Strict Transport Security for production domains
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
