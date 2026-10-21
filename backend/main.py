# =====================================================================
# GREEN-FINANCE — MAIN.PY (APPLICATION ENTRY POINT)
# Purpose: Core FastAPI Switchboard:
#          - Security Headers & Restrictive CORS Allowlist
#          - Performance Logging & Exception Interceptors
#          - Router Mounts: Auth, Banking, Ledger, Telemetry, Sustainability
#          - Safe Static File Serving (No Path Traversal)
#          - Prometheus TSDB Instrumentation
# =====================================================================

import os
from typing import Optional
from fastapi import FastAPI, HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from backend.core.config import settings
from backend.middleware.logging_middleware import LoggingMiddleware
from backend.middleware.security_headers import SecurityHeadersMiddleware
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from backend.db.database import init_db
from backend.api import (
    health, auth, user, carbon, credits, ledger,
    portfolio, telemetry, baseline, accuracy, payment, sustainability,
    admin, cases, operations
)

# 🔹 Create FastAPI Application Instance
app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None
)


# =====================================================================
# 🛡️ MIDDLEWARE INSTALLATION (ORDER MATTERS)
# =====================================================================

# 1. Rate Limiting & Abuse Defense
app.add_middleware(RateLimitMiddleware)

# 2. Defense-in-Depth Security Headers (CSP, Anti-Clickjacking, No-Sniff)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Strict CORS Configuration (Explicit origins; no wildcard with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Requested-With"],
)

# 3. Performance & Access Logger Middleware
app.add_middleware(LoggingMiddleware)


# =====================================================================
# 🚨 ERROR EXCEPTION INTERCEPTORS
# =====================================================================

# Catch HTTP exceptions (FastAPI & Starlette)
app.add_exception_handler(FastAPIHTTPException, http_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


# =====================================================================
# 🚪 PATHWAY ROUTE REGISTRATIONS
# =====================================================================

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(carbon.router)
app.include_router(credits.router)
app.include_router(ledger.router)
app.include_router(portfolio.router)
app.include_router(telemetry.router)
app.include_router(baseline.router)
app.include_router(accuracy.router)
app.include_router(payment.router)
app.include_router(sustainability.router)
app.include_router(admin.router)
app.include_router(cases.router)
app.include_router(operations.router)


@app.post("/connection/ingest-trace", status_code=201, tags=["Connection"])
async def ingest_trace(payload: dict):
    """Ingests transaction trace streamed from banking engine or external clients."""
    return {"status": "success", "message": "Trace ingested", "trace_id": payload.get("trace_id")}


# =====================================================================
# 📊 PROMETHEUS INSTRUMENTATION
# =====================================================================

Instrumentator().instrument(app).expose(app)


# =====================================================================
# 🌐 HARDENED STATIC ASSET ROUTING (ZERO PATH TRAVERSAL)
# =====================================================================

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
shared_dir = os.path.join(frontend_dir, "shared")
bank_dir = os.path.join(frontend_dir, "bank")
investigator_dir = os.path.join(frontend_dir, "investigator")
grafana_dir = os.path.join(frontend_dir, "grafana")
admin_dir = os.path.join(frontend_dir, "admin")
operations_dir = os.path.join(frontend_dir, "operations")


def safe_static_serve(base_dir: str, rel_path: str, fallback_file: Optional[str] = None) -> FileResponse:
    """
    Safely resolves and serves files, strictly preventing directory traversal attacks.
    Guarantees that the resolved target is confined to base_dir.
    """
    base_dir = os.path.abspath(base_dir)
    if not rel_path or rel_path.strip() == "":
        if fallback_file:
            return FileResponse(os.path.join(base_dir, fallback_file))
        raise StarletteHTTPException(status_code=404, detail="Resource not found")

    # Canonicalize target path
    clean_rel = rel_path.lstrip("/\\")
    target_path = os.path.abspath(os.path.join(base_dir, clean_rel))

    try:
        common = os.path.commonpath([base_dir, target_path])
    except ValueError:
        raise StarletteHTTPException(status_code=404, detail="Resource not found")

    if common != base_dir:
        raise StarletteHTTPException(status_code=404, detail="Resource not found")

    if not os.path.isfile(target_path):
        if fallback_file:
            fallback_target = os.path.abspath(os.path.join(base_dir, fallback_file))
            if os.path.isfile(fallback_target):
                return FileResponse(fallback_target)
        raise StarletteHTTPException(status_code=404, detail="Resource not found")

    return FileResponse(target_path)


@app.get("/", include_in_schema=False)
def serve_index():
    return safe_static_serve(frontend_dir, "index.html")

@app.get("/grafana", include_in_schema=False)
@app.get("/grafana/", include_in_schema=False)
def serve_grafana():
    return safe_static_serve(grafana_dir, "index.html")

@app.get("/grafana/{file_path:path}", include_in_schema=False)
def serve_grafana_file(file_path: str):
    return safe_static_serve(grafana_dir, file_path, fallback_file="index.html")

@app.get("/bank", include_in_schema=False)
@app.get("/bank/", include_in_schema=False)
def serve_bank():
    return safe_static_serve(bank_dir, "index.html")

@app.get("/bank/{file_path:path}", include_in_schema=False)
def serve_bank_file(file_path: str):
    return safe_static_serve(bank_dir, file_path, fallback_file="index.html")

@app.get("/investigator", include_in_schema=False)
@app.get("/investigator/", include_in_schema=False)
def serve_investigator():
    return safe_static_serve(investigator_dir, "index.html")

@app.get("/investigator/{file_path:path}", include_in_schema=False)
def serve_investigator_file(file_path: str):
    return safe_static_serve(investigator_dir, file_path, fallback_file="index.html")

@app.get("/admin", include_in_schema=False)
@app.get("/admin/", include_in_schema=False)
def serve_admin():
    return safe_static_serve(admin_dir, "index.html")

@app.get("/admin/super", include_in_schema=False)
@app.get("/admin/super/", include_in_schema=False)
def serve_admin_super():
    return safe_static_serve(admin_dir, "super.html")

@app.get("/operations", include_in_schema=False)
@app.get("/operations/", include_in_schema=False)
def serve_operations():
    return safe_static_serve(operations_dir, "index.html")

@app.get("/operations/{file_path:path}", include_in_schema=False)
def serve_operations_file(file_path: str):
    return safe_static_serve(operations_dir, file_path, fallback_file="index.html")

@app.get("/shared/{file_path:path}", include_in_schema=False)
def serve_shared_file(file_path: str):
    try:
        return safe_static_serve(shared_dir, file_path)
    except StarletteHTTPException:
        pass
    return safe_static_serve(frontend_dir, file_path, fallback_file="shared/styles.css")

@app.get("/styles.css", include_in_schema=False)
def serve_css():
    return safe_static_serve(frontend_dir, "styles.css")

@app.get("/app.js", include_in_schema=False)
def serve_js():
    return safe_static_serve(frontend_dir, "app.js")

@app.get("/bank.css", include_in_schema=False)
def serve_bank_css():
    return safe_static_serve(bank_dir, "bank.css")

@app.get("/bank.js", include_in_schema=False)
def serve_bank_js():
    return safe_static_serve(bank_dir, "bank.js")

@app.get("/investigator.css", include_in_schema=False)
def serve_inv_css():
    return safe_static_serve(investigator_dir, "investigator.css")

@app.get("/investigator.js", include_in_schema=False)
def serve_inv_js():
    return safe_static_serve(investigator_dir, "investigator.js")


# =====================================================================
# ⚙️ STARTUP EVENT LOGIC
# =====================================================================

@app.on_event("startup")
def on_startup():
    init_db()
