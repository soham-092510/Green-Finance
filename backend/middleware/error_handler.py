# =====================================================================
# GREEN-FINANCE — ERROR_HANDLER.PY
# Purpose: Safe HTTP and validation error formatting. Prevents stack trace
#          leaks, path disclosures, and serves branded 404 HTML for browsers.
# =====================================================================

import os
from fastapi import Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

FRONTEND_404 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "404.html"))


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    accept = request.headers.get("accept", "")
    if exc.status_code == 404 and "text/html" in accept and os.path.isfile(FRONTEND_404):
        return FileResponse(FRONTEND_404, status_code=404)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "path": str(request.url)
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation failed",
            "details": exc.errors()
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error"
        },
    )
