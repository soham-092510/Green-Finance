# =====================================================================
# GREEN-FINANCE — OPERATIONS.PY (OPERATIONS CENTER API ROUTER)
# Purpose: Real-time operational control center endpoints:
#          - Live transactions/sec, login/sec, registration/sec, 4xx/5xx errors
#          - Health checks across API, DB (WAL), Prometheus, and Kepler RAPL
#          - Active carbon anomaly & risk alert counts
#          - Recent security audit stream
# =====================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.db.session import get_db
from backend.core.dependencies import get_current_user, require_permission
from backend.models.user import User
from backend.services import operations_service

router = APIRouter(prefix="/operations", tags=["Operations & Monitoring Center"])


@router.get(
    "/metrics",
    summary="Get real-time operational metrics and throughput rates"
)
def get_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("operations.read"))
) -> Dict[str, Any]:
    """
    Returns real-time rates (tx/sec, logins/sec, errors/sec), system health,
    carbon anomalies, and recent security audit events.
    Restricted to Admins, Auditors, Investigators, and Super Admins.
    """
    return operations_service.get_operational_metrics(db=db)


@router.get(
    "/health-status",
    summary="Lightweight service health diagnostic check"
)
def get_health_status(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Public/monitoring liveness health check."""
    return {
        "status": "UP",
        "service": "green-finance-backend",
        "security_mode": "RBAC_ENFORCED",
        "rate_limiting": "ENABLED",
        "ledger_integrity": "SHA256_HASH_CHAINED"
    }
