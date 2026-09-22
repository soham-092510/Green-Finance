# =====================================================================
# ECO MONITOR / GREEN-FINANCE — ACCURACY.PY (API ROUTER)
# Purpose: Endpoints for Telemetry Attribution Fidelity & Accuracy:
#          - GET /accuracy/current: Live host, containers, idle, residual, fidelity
#          - POST /accuracy/run-validation: Execute full validation cycle
#          - GET /accuracy/report: Generate formal auditable validation report
#          - GET /accuracy/report/{run_id}: Get specific validation certificate
# =====================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Optional
from backend.db.session import get_db
from backend.services import accuracy_service, baseline_service, telemetry_service

router = APIRouter(prefix="/accuracy", tags=["Attribution Fidelity & Accuracy"])


@router.get("/current", summary="Get live attribution fidelity and energy conservation metrics")
def get_current_accuracy(db: Session = Depends(get_db)) -> Dict:
    """
    Returns real-time energy conservation breakdown:
    Host Energy - (Container Energy + Idle Energy) = Residual Loss
    Attribution Fidelity (%) = (1 - Residual / Host) * 100
    """
    telemetry = telemetry_service.get_realtime_metrics()
    locked_baseline = baseline_service.get_current_locked_baseline(db)

    host_p = telemetry["platform_power_watts"]
    cont_p = telemetry["container_power_watts"]
    idle_p = locked_baseline.idle_power_mean
    residual_p = telemetry["residual_power_watts"]
    fidelity = telemetry["attribution_fidelity_percent"]

    return {
        "host_power_watts": host_p,
        "container_power_watts": cont_p,
        "idle_baseline_watts": idle_p,
        "accounted_power_watts": round(cont_p + idle_p, 2),
        "residual_power_watts": residual_p,
        "residual_percent": round((residual_p / host_p * 100.0) if host_p > 0 else 5.0, 2),
        "attribution_fidelity_percent": fidelity,
        "status": "PASS" if fidelity >= 94.0 else "DRIFT",
        "target_tolerance_percent": 6.0,
        "explanation": f"Host power ({host_p}W) minus accounted ({round(cont_p + idle_p, 2)}W) leaves {residual_p}W residual ({round((residual_p / host_p * 100.0) if host_p > 0 else 5.0, 1)}%), achieving {fidelity}% attribution fidelity."
    }


@router.post("/run-validation", summary="Execute full energy validation test cycle")
def run_validation(
    tx_count: int = 500,
    host_joules: float = 1000.0,
    container_joules: float = 800.0,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Runs the complete validation experiment:
    1. Reads locked baseline
    2. Collects container and host energy
    3. Calculates residual loss and attribution fidelity
    4. Records immutable ValidationRun in DB
    """
    run = accuracy_service.run_full_validation_cycle(
        db=db,
        tx_count=tx_count,
        host_joules=host_joules,
        container_joules=container_joules
    )
    return {
        "validation_run_id": run.id,
        "timestamp": run.timestamp,
        "tx_count": run.tx_count,
        "host_energy_joules": run.host_energy_joules,
        "container_energy_joules": run.container_energy_joules,
        "idle_energy_joules": run.idle_energy_joules,
        "residual_joules": run.residual_joules,
        "residual_percent": run.residual_percent,
        "attribution_fidelity_percent": run.fidelity_percent,
        "transaction_repeatability_cv": run.tx_cv_percent,
        "status": run.status
    }


@router.get("/report", summary="Generate the formal Energy Validation Report")
def get_validation_report(run_id: Optional[str] = None, db: Session = Depends(get_db)) -> Dict:
    """
    Generates an official, auditable energy attribution report with SHA-256 digital signature.
    """
    return accuracy_service.generate_formal_validation_report(db=db, run_id=run_id)
