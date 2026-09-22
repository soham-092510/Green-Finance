# =====================================================================
# ECO MONITOR / GREEN-FINANCE — BASELINE.PY (API ROUTER)
# Purpose: Endpoints for Idle / Baseline Calibration Mode:
#          - POST /baseline/start: Start zero-workload calibration
#          - GET /baseline/status: Read calibration progress and statistics
#          - POST /baseline/lock: Freeze baseline with Calibration Lock
#          - GET /baseline/current: Fetch current locked baseline profile
#          - GET /baseline/drift: Check drift between live and locked baseline
# =====================================================================

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Dict
from backend.db.session import get_db
from backend.services import baseline_service

router = APIRouter(prefix="/baseline", tags=["Idle Baseline Calibration"])


@router.post("/start", summary="Start zero-workload baseline calibration")
def start_baseline(duration_seconds: int = 30) -> Dict:
    """
    Initiates idle baseline calibration when NO transaction workload is running.
    Samples background host electricity over fixed intervals.
    """
    return baseline_service.start_calibration(duration_seconds=duration_seconds)


@router.get("/status", summary="Get live baseline calibration status and metrics")
def get_status() -> Dict:
    """
    Returns progress %, current idle Watts, mean, standard deviation, and CV_idle.
    """
    return baseline_service.get_calibration_status()


@router.post("/lock", summary="Lock calibrated baseline profile")
def lock_baseline(db: Session = Depends(get_db)) -> Dict:
    """
    Applies Calibration Lock. Prevents modification during transaction validation tests.
    """
    profile = baseline_service.lock_baseline_profile(db=db)
    return {
        "status": "LOCKED",
        "baseline_id": profile.id,
        "idle_power_mean_watts": profile.idle_power_mean,
        "idle_power_std_watts": profile.idle_power_std,
        "idle_cv_percent": profile.idle_cv,
        "machine_id": profile.machine_id,
        "timestamp": profile.timestamp
    }


@router.get("/current", summary="Get currently locked baseline profile")
def get_current(db: Session = Depends(get_db)) -> Dict:
    profile = baseline_service.get_current_locked_baseline(db=db)
    return {
        "baseline_id": profile.id,
        "machine_id": profile.machine_id,
        "idle_power_mean_watts": profile.idle_power_mean,
        "idle_power_std_watts": profile.idle_power_std,
        "idle_cv_percent": profile.idle_cv,
        "status": profile.status,
        "timestamp": profile.timestamp
    }


@router.get("/drift", summary="Check for baseline drift against locked profile")
def check_drift(current_watts: float = 18.7, db: Session = Depends(get_db)) -> Dict:
    profile = baseline_service.get_current_locked_baseline(db=db)
    return baseline_service.check_baseline_drift(
        current_idle_watts=current_watts,
        locked_baseline_watts=profile.idle_power_mean
    )
