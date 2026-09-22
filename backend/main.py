# =====================================================================
# ECO MONITOR — MAIN.PY (APPLICATION ENTRY POINT)
# =====================================================================
# Purpose/Existence of this file:
# This file is the "Main Switchboard" and starter engine of our entire project.
# Think of it like a train station manager. It initializes the FastAPI server,
# hooks up security layers (CORS), configures error reporting sheets, loads all 
# route path controllers (like /auth, /credits, /telemetry), and handles the 
# database table initialization on system startup.
# =====================================================================

# 🔹 Import FastAPI
# FastAPI is the core framework library used to construct modern Python APIs.
# It acts like the building foundation structure for our web servers.
from fastapi import FastAPI

# 🔹 Import StarletteHTTPException
# Starlette is the lightweight engine under the hood of FastAPI. We import its 
# exception class to intercept standard web navigation errors (like 404 Not Found).
from starlette.exceptions import HTTPException as StarletteHTTPException

# 🔹 Import RequestValidationError
# Triggered automatically when incoming request forms or JSON variables are missing 
# or formatted incorrectly (e.g. text entered where a number was required).
from fastapi.exceptions import RequestValidationError

# 🔹 Import Instrumentator
# Exposes request metrics to Prometheus so we can monitor server performance, 
# query latency, and traffic in Grafana.
from prometheus_fastapi_instrumentator import Instrumentator

# 🔹 Import settings
# The global configuration settings loaded from config.py.
from backend.core.config import settings

# 🔹 Import LoggingMiddleware
# An interceptor that records the timestamp, visitor IP, and response time of every request.
from backend.middleware.logging_middleware import LoggingMiddleware

# 🔹 Import custom error handlers
# Error handlers intercept crashes and translate them into friendly JSON error statements
# instead of crashing the visitor's screen.
from backend.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)

# 🔹 Import init_db
# The function that builds SQL database tables based on our ORM models.
from backend.db.database import init_db

# 🔹 Import API routers
# Registers the different pages/sections of our application.
from backend.api import health, auth, user, carbon, credits, ledger, portfolio, telemetry, baseline, accuracy, payment

# 🔹 Import CORSMiddleware
# CORS (Cross-Origin Resource Sharing) is a browser security mechanism.
# We import this to control which websites are allowed to dial our backend (e.g. allowing
# our HTML/JS frontend to fetch carbon statistics).
from fastapi.middleware.cors import CORSMiddleware


# 🔹 Create FastAPI application instance
# We configure title from Settings class and set version to 1.0.0.
# This variable "app" is what uvicorn runs.
app = FastAPI(
    title=settings.app_name,
    version="1.0.0"
)


# =====================================================================
# 🛡️ MIDDLEWARE INSTALLATION
# =====================================================================

# 1. CORS Guard Middleware
# We configure it to allow any domain client ("*") to access endpoints during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Performance & Access Logger Middleware
# Tracks duration of every request.
app.add_middleware(LoggingMiddleware)


# =====================================================================
# 🚨 ERROR EXCEPTION INTERCEPTORS
# =====================================================================

# Catch HTTP exceptions (like 404, 401)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

# Catch field validation errors (422)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Catch unexpected internal crashes (500)
app.add_exception_handler(Exception, unhandled_exception_handler)


# =====================================================================
# 🚪 PATHWAY ROUTE REGISTRATIONS
# =====================================================================

# Hook up sub-controllers onto our central app switchboard
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(carbon.router)
app.include_router(credits.router)
app.include_router(ledger.router)
app.include_router(portfolio.router)
app.include_router(telemetry.router) # Registers the Kepler PromQL telemetry pathways
app.include_router(baseline.router)  # Registers Idle Baseline Calibration endpoints
app.include_router(accuracy.router)  # Registers Attribution Fidelity & Accuracy endpoints
app.include_router(payment.router)   # Registers Simulated Banking Microservices endpoints


# =====================================================================
# 📊 PROMETHEUS INSTRUMENTATION
# =====================================================================

# Exposes Prometheus tracking metrics under "/metrics" endpoint
Instrumentator().instrument(app).expose(app)


# =====================================================================
# ⚙️ STARTUP EVENT LOGIC
# =====================================================================

# Runs automatically when the server is powered up.
@app.on_event("startup")
def on_startup():
    # Automatically creates all database tables (User, Accounts, CarbonCredit, Ledger)
    # and populates them with seed demo data on local development SQLite database.
    init_db()


# =====================================================================
# 🕸️ CONNECTIONS & WORKFLOW (How this file communicates with others):
# =====================================================================
# 1. BOOTED BY:
#    - Uvicorn server launcher: Run via `uvicorn backend.main:app` or Docker.
#
# 2. LOADS CONFIGURATION:
#    - [config.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/core/config.py):
#      Reads `settings.app_name` to define application metadata.
#
# 3. CONTEXTS ERROR HANDLERS:
#    - [error_handler.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/middleware/error_handler.py)
#
# 4. INITIALIZES STORAGE DATABASE:
#    - [database.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/db/database.py):
#      Calls `init_db()` to run schemas check on SQLite database engine.
#
# 5. EXPANDS ACCESS ROUTERS:
#    - Registers [telemetry.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/telemetry.py)
#      and other APIs, mapping them to the server web paths.
# =====================================================================