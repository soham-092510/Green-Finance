# =====================================================================
# ECO MONITOR — TELEMETRY.PY (ENERGY TELEMETRY API ROUTER)
# =====================================================================
# Purpose/Existence of this file:
# This file is like a series of doors/windows (API routes) that let the frontend 
# website or outside clients ask questions about energy telemetry.
# Here, we define the web address paths (endpoints) like `/telemetry/realtime` 
# that are exposed to visitors. When a visitor sends a request to one of these paths,
# this code triggers the translation logic in our services and returns the data back to them.
# =====================================================================

# 🔹 Import APIRouter, Depends, HTTPException, status
# APIRouter → Allows grouping routes under `/telemetry` prefix.
# Depends → A dependency manager that automatically hooks up authentication and DB connections.
# HTTPException → Used to report clear error messages (e.g. 400 Bad Request) back to the user's browser.
# status → Contains standard web response codes (like 201 Created).
from fastapi import APIRouter, Depends, HTTPException, status

# 🔹 Import Session
# Database Session class used to execute database operations.
from sqlalchemy.orm import Session

# 🔹 Import Dict
# A dictionary data structure description.
from typing import Dict, Optional

# 🔹 Import get_db
# A helper function that opens a database connection session and closes it when the request is done.
from backend.db.session import get_db

# 🔹 Import get_current_user
# A guard function that reads the login token (JWT) from the visitor's request headers
# to prove they are logged in.
from backend.core.dependencies import get_current_user

# 🔹 Import User
# The User model blueprint representing registered users.
from backend.models.user import User

# 🔹 Import telemetry_service
# The service containing the PromQL logic to fetch metrics from Prometheus.
from backend.services import telemetry_service


# 🔹 Create Router Instance
# Group all endpoints in this file under the prefix "/telemetry" and add tags for Swagger UI documentation.
router = APIRouter(prefix="/telemetry", tags=["Energy Telemetry"])


# 🔹 Endpoint: GET /telemetry/realtime
# Exposes an endpoint to read current real-time energy usage.
# Requires the user to be logged in (verified by `get_current_user`).
@router.get(
    "/realtime",
    summary="Get real-time energy usage and carbon emissions rate"
)
def get_realtime(
    current_user: User = Depends(get_current_user)
):
    # 1. Trigger service to run PromQL queries on Prometheus
    metrics = telemetry_service.get_realtime_metrics()
    # 2. Send the metrics package back to the user's browser
    return metrics


# 🔹 Endpoint: GET /telemetry/historical
# Exposes an endpoint to check accumulated energy statistics over a period of time.
# Query parameter `range_str` lets the visitor ask for different periods (e.g. "5m", "1h", "24h").
@router.get(
    "/historical",
    summary="Get cumulative energy usage and carbon emissions over a time range"
)
def get_historical(
    range_str: str = "1h",
    current_user: User = Depends(get_current_user)
):
    # 1. Trigger service to query energy increase over the duration
    return telemetry_service.get_historical_metrics(range_str=range_str)


# 🔹 Endpoint: POST /telemetry/log
# Exposes an endpoint to automatically audit and log container emissions into the database.
# Returns 201 Created status. Connects to database and login validator.
@router.post(
    "/log",
    status_code=status.HTTP_201_CREATED,
    summary="Auto-log carbon emissions using Kepler physical telemetry metrics"
)
def auto_log_emissions(
    range_str: str = "1h",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Trigger service to read metrics, calculate carbon, write to DB, and post ledger updates
    log_summary = telemetry_service.log_telemetry_emissions(
        db=db,
        user_id=current_user.id,
        range_str=range_str
    )
    
    # 2. If it returned None (because energy consumption was 0), throw a bad request error
    if log_summary is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not generate emissions record. Energy usage must be greater than zero."
        )
        
    # 3. Return the created ledger records summary
    return log_summary


@router.get(
    "/mode",
    summary="Get current telemetry mode (OBSERVED/SIMULATED/CALCULATED)"
)
def get_telemetry_mode():
    """Returns the current telemetry source mode and Kepler availability."""
    return {
        "telemetry_mode": telemetry_service.get_telemetry_mode(),
        "kepler_available": telemetry_service.KEPLER_AVAILABLE,
        "description": "OBSERVED = Physical Kepler RAPL counters; SIMULATED = High-fidelity model; CALCULATED = Derived from formula"
    }


@router.post(
    "/calculate-carbon",
    summary="Calculate carbon from energy joules with explicit labeling"
)
def calculate_transaction_carbon(
    energy_joules: float,
    factor_gco2_per_kwh: float = 713.0,
    current_user: User = Depends(get_current_user)
):
    """Calculate carbon footprint from energy with full methodology transparency."""
    return telemetry_service.calculate_transaction_carbon(energy_joules, factor_gco2_per_kwh)


@router.get(
    "/promql",
    summary="Execute raw PromQL query against Prometheus"
)
def execute_promql(
    query: str,
    current_user: User = Depends(get_current_user)
):
    """Execute a raw PromQL query and return results."""
    result = telemetry_service.query_prometheus(query)
    if result:
        return result
    return {"status": "error", "message": "Query failed or returned no data"}


# =====================================================================
# 🕸️ CONNECTIONS & WORKFLOW (How this file communicates with others):
# =====================================================================
# 1. READS INCOMING WEB REQUESTS:
#    - Intercepts calls on paths: `/telemetry/realtime`, `/telemetry/historical`, `/telemetry/log`.
#
# 2. TRIGGERS SECURITY AUTHENTICATION:
#    - [dependencies.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/core/dependencies.py):
#      Calls `get_current_user` to validate the visitor's JWT identity card.
#
# 3. LOADS DATABASE SESSION:
#    - [session.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/db/session.py):
#      Calls `get_db` to get a transactional session connection.
#
# 4. DELEGATES WORKFLOW TO:
#    - [telemetry_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/telemetry_service.py):
#      Calls service functions to perform calculations and data collection.
#
# 5. REGISTERED IN:
#    - [main.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/main.py):
#      This router is imported and registered in the app startup code to open these doors/paths.
# =====================================================================

