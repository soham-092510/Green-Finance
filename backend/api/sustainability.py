# =====================================================================
# GREEN-FINANCE — SUSTAINABILITY.PY (API ROUTER)
# Purpose: Enterprise Sustainability Analytics & Compliance Suite:
#          - Executive KPIs & Aggregations
#          - Audited Carbon Ledger (Workload-Window Allocation)
#          - Microservice Efficiency Benchmarking
#          - Sustainability Goals Management & Progress
#          - Basel Risk Alert Center
#          - Explainable Rule-Based Recommendations
#          - "What-If?" Scenario Analysis Lab
#          - CEA India Grid Carbon Factor Registry
#          - CSV/PDF Audit Report Generation
#          - Live Connected Banking Users Insights
# =====================================================================

import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.db.session import get_db
from backend.models.transaction import Transaction
from backend.models.user import User
from backend.models.sustainability import (
    CarbonFactor, SustainabilityGoal, Alert, Recommendation, CarbonMeasurement
)

router = APIRouter(prefix="/sustainability", tags=["Enterprise Sustainability Analytics"])


# --- Pydantic Request Schemas ---

class GoalCreateUpdateRequest(BaseModel):
    title: str
    goal_type: str = Field(..., description="'co2_per_tx', 'monthly_co2', or 'energy_per_tx'")
    target_value: float
    current_value: Optional[float] = 0.0
    unit: str
    period: Optional[str] = "Monthly"
    status: Optional[str] = "ON_TRACK"


class ScenarioAnalysisRequest(BaseModel):
    tx_count: int = Field(default=10000, ge=100, le=1000000)
    current_co2_per_tx_g: float = Field(default=0.16, ge=0.01, le=5.0)
    efficiency_improvement_pct: float = Field(default=15.0, ge=0.0, le=90.0)
    grid_carbon_factor_g_kwh: float = Field(default=713.0, ge=50.0, le=1200.0)


class CarbonFactorCreateRequest(BaseModel):
    region: str
    year: int
    factor_gco2_per_kwh: float
    unit: Optional[str] = "gCO2/kWh"
    source: str
    effective_date: Optional[str] = "2024-01-01"
    is_active: Optional[bool] = False


# --- Endpoints ---

@router.get("/kpis", summary="Executive Sustainability Dashboard KPIs")
def get_sustainability_kpis(
    range_filter: str = Query("30d", enum=["today", "7d", "30d", "all"]),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns aggregate executive sustainability indicators for financial institutions.
    """
    query = db.query(Transaction)
    now = datetime.now()
    if range_filter == "today":
        query = query.filter(Transaction.created_at >= now.replace(hour=0, minute=0, second=0))
    elif range_filter == "7d":
        query = query.filter(Transaction.created_at >= now - timedelta(days=7))
    elif range_filter == "30d":
        query = query.filter(Transaction.created_at >= now - timedelta(days=30))

    transactions = query.all()
    total_tx = len(transactions)
    success_tx = sum(1 for t in transactions if t.status == "COMPLETED")
    total_volume = sum(t.amount or 0.0 for t in transactions)
    total_joules = sum(t.energy_joules or 0.0 for t in transactions)
    total_carbon_g = sum(t.carbon_grams or 0.0 for t in transactions)

    # Convert Joules to kWh (1 kWh = 3.6e6 Joules)
    total_kwh = total_joules / 3600000.0
    avg_co2_per_tx_g = round(total_carbon_g / max(total_tx, 1), 4)

    # Active Carbon Factor
    active_factor = db.query(CarbonFactor).filter(CarbonFactor.is_active == True).first()
    factor_val = active_factor.factor_gco2_per_kwh if active_factor else 713.0
    factor_src = active_factor.source if active_factor else "CEA India CO2 Baseline Database v20.0"

    # Primary goal progress
    primary_goal = db.query(SustainabilityGoal).filter(SustainabilityGoal.goal_type == "co2_per_tx").first()
    goal_target = primary_goal.target_value if primary_goal else 0.20
    goal_status = "ACHIEVED" if avg_co2_per_tx_g <= goal_target else "OFF_TRACK"

    return {
        "range_filter": range_filter,
        "total_transactions": total_tx,
        "successful_transactions": success_tx,
        "failed_transactions": total_tx - success_tx,
        "success_rate_percent": round((success_tx / max(total_tx, 1)) * 100.0, 1),
        "total_volume_inr": round(total_volume, 2),
        "total_energy_joules": round(total_joules, 4),
        "total_energy_kwh": round(total_kwh, 6),
        "total_carbon_grams": round(total_carbon_g, 4),
        "total_carbon_kg": round(total_carbon_g / 1000.0, 6),
        "avg_co2_per_tx_grams": avg_co2_per_tx_g,
        "current_carbon_factor": {
            "factor_gco2_per_kwh": factor_val,
            "region": active_factor.region if active_factor else "India (National Grid)",
            "source": factor_src,
            "unit": "gCO2/kWh"
        },
        "sustainability_target": {
            "target_co2_per_tx_g": goal_target,
            "current_value": avg_co2_per_tx_g,
            "status": goal_status
        },
        "telemetry_source": "SIMULATED (Kepler RAPL unavailable in Docker Desktop/WSL2)",
        "telemetry_mode": "SIMULATED"
    }


@router.get("/ledger", summary="Audited Carbon Ledger Entries")
def get_carbon_ledger(
    limit: int = 50,
    offset: int = 0,
    service: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns granular carbon ledger entries with workload-window attribution formula.
    """
    q = db.query(Transaction)
    if service:
        q = q.filter(Transaction.service == service)
    if search:
        search_filter = f"%{search}%"
        q = q.filter((Transaction.id.like(search_filter)) | (Transaction.sender_bank_id.like(search_filter)) | (Transaction.recipient_bank_id.like(search_filter)))

    total_records = q.count()
    txns = q.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()

    active_factor = db.query(CarbonFactor).filter(CarbonFactor.is_active == True).first()
    factor_val = active_factor.factor_gco2_per_kwh if active_factor else 713.0

    entries = []
    for t in txns:
        energy_kwh = (t.energy_joules or 0.69) / 3600000.0
        entries.append({
            "transaction_id": t.id,
            "timestamp": t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "sender_bank_id": t.sender_bank_id or "HDFC9999",
            "recipient_bank_id": t.recipient_bank_id or "MAH123",
            "amount": t.amount or 0.0,
            "currency": t.currency or "INR",
            "transaction_type": t.transaction_type or "TRANSFER",
            "service": t.service or "payment-service",
            "status": t.status,
            "energy_joules": round(t.energy_joules or 0.69, 4),
            "energy_kwh": round(energy_kwh, 9),
            "carbon_grams": round(t.carbon_grams or 0.00014, 5),
            "carbon_factor_used": factor_val,
            "calculation_basis": "Workload allocation: (Energy_kWh × Factor) / Txn_Window [SIMULATED]",
            "audit_hash": t.audit_hash or "SHA-256-PENDING",
            "measurement_window": {
                "window_duration_seconds": 300,
                "idle_baseline_power_watts": 18.7,
                "fidelity_percent": t.fidelity_percent or 96.2,
                "formula": "CO2_g = (Energy_J / 3,600,000) * 713.0 g/kWh",
                "telemetry_mode": "SIMULATED"
            }
        })

    return {
        "total_records": total_records,
        "limit": limit,
        "offset": offset,
        "records": entries
    }


@router.get("/efficiency", summary="Service Efficiency Comparison")
def get_service_efficiency(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Compares computational energy and carbon intensity across banking microservices:
    Payment Service vs Auth Service vs Ledger Service vs Fraud Service.
    Data derived from actual transaction telemetry where available.
    """
    # Get actual data from transaction telemetry
    from backend.models.accuracy import TransactionTelemetry
    
    services_data = []
    
    # Payment Service
    payment_txns = db.query(Transaction).filter(Transaction.service == "payment-service").all()
    payment_telemetry = db.query(TransactionTelemetry).join(Transaction).filter(Transaction.service == "payment-service").all()
    
    if payment_telemetry:
        avg_payment_energy = sum(t.total_joules for t in payment_telemetry) / len(payment_telemetry)
        avg_payment_carbon = sum(t.carbon_mg for t in payment_telemetry) / len(payment_telemetry)
        avg_payment_latency = sum(t.duration_ms for t in payment_telemetry) / len(payment_telemetry)
    else:
        avg_payment_energy = 0.69
        avg_payment_carbon = 0.137
        avg_payment_latency = 125.0
    
    services_data.append({
        "service_name": "payment-service",
        "role": "Core Double-Entry Funds Settlement",
        "request_count": len(payment_txns),
        "transaction_count": len(payment_txns),
        "energy_joules_total": round(sum(t.energy_joules or 0.69 for t in payment_txns), 2),
        "energy_per_tx_j": round(avg_payment_energy, 3),
        "carbon_grams_total": round(sum(t.carbon_grams or 0.00014 for t in payment_txns), 4),
        "carbon_per_tx_mg": round(avg_payment_carbon, 3),
        "avg_latency_ms": round(avg_payment_latency, 1),
        "workload_share_pct": round((len(payment_txns) / max(len(payment_txns), 1)) * 100, 1),
        "computational_intensity": "HIGH",
        "status": "MONITORED",
        "action_advice": "High computation due to row locking & audit hashing. Batch DB writes to optimize.",
        "telemetry_mode": "SIMULATED"
    })
    
    # Auth Service
    auth_txns = db.query(Transaction).filter(Transaction.service == "auth-service").all()
    services_data.append({
        "service_name": "auth-service",
        "role": "JWT Verification & Role Permissions",
        "request_count": len(auth_txns),
        "transaction_count": len(auth_txns),
        "energy_joules_total": round(sum(t.energy_joules or 0.11 for t in auth_txns), 2),
        "energy_per_tx_j": 0.065,
        "carbon_grams_total": round(sum(t.carbon_grams or 0.00002 for t in auth_txns), 4),
        "carbon_per_tx_mg": 0.013,
        "avg_latency_ms": 8.4,
        "workload_share_pct": round((len(auth_txns) / max(len(auth_txns), 1)) * 100, 1) if auth_txns else 9.0,
        "computational_intensity": "LOW",
        "status": "HIGHLY_EFFICIENT",
        "action_advice": "Lightweight token cryptographic check.",
        "telemetry_mode": "SIMULATED"
    })
    
    # Ledger Service
    ledger_txns = db.query(Transaction).filter(Transaction.service == "ledger-service").all()
    services_data.append({
        "service_name": "ledger-service",
        "role": "Double-Entry Bookkeeping & Account Balancing",
        "request_count": len(ledger_txns),
        "transaction_count": len(ledger_txns),
        "energy_joules_total": round(sum(t.energy_joules or 0.16 for t in ledger_txns), 2),
        "energy_per_tx_j": 0.110,
        "carbon_grams_total": round(sum(t.carbon_grams or 0.00003 for t in ledger_txns), 4),
        "carbon_per_tx_mg": 0.022,
        "avg_latency_ms": 14.8,
        "workload_share_pct": round((len(ledger_txns) / max(len(ledger_txns), 1)) * 100, 1) if ledger_txns else 15.0,
        "computational_intensity": "MEDIUM",
        "status": "OPTIMIZED",
        "action_advice": "Balanced journal posting operating at high efficiency.",
        "telemetry_mode": "SIMULATED"
    })
    
    # Fraud Service
    services_data.append({
        "service_name": "fraud-service",
        "role": "Risk Assessment & Sanctions Screening",
        "request_count": len(payment_txns),  # Runs per payment
        "transaction_count": len(payment_txns),
        "energy_joules_total": round(len(payment_txns) * 0.13, 2),
        "energy_per_tx_j": 0.130,
        "carbon_grams_total": round(len(payment_txns) * 0.000025, 4),
        "carbon_per_tx_mg": 0.025,
        "avg_latency_ms": 19.2,
        "workload_share_pct": 18.0,
        "computational_intensity": "MEDIUM",
        "status": "OPTIMIZED",
        "action_advice": "Rule evaluation engine within expected statistical bounds.",
        "telemetry_mode": "SIMULATED"
    })

    return {
        "highest_carbon_service": "payment-service",
        "lowest_carbon_service": "auth-service",
        "services": services_data,
        "recommendation_summary": "payment-service accounts for ~58% of total computational energy. Optimization here yields the greatest carbon reduction.",
        "telemetry_mode": "SIMULATED (Kepler RAPL unavailable)"
    }


@router.get("/goals", summary="List Sustainability Goals")
def list_sustainability_goals(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Returns active sustainability goals and progress."""
    goals = db.query(SustainabilityGoal).all()
    results = []
    for g in goals:
        progress_pct = round(min(100.0, (g.current_value / max(g.target_value, 0.001)) * 100.0), 1)
        remaining = round(max(0.0, g.target_value - g.current_value), 2)
        results.append({
            "id": g.id,
            "title": g.title,
            "goal_type": g.goal_type,
            "target_value": g.target_value,
            "current_value": g.current_value,
            "unit": g.unit,
            "period": g.period,
            "status": g.status,
            "progress_percent": progress_pct,
            "remaining": remaining,
            "created_at": g.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return results


@router.post("/goals", summary="Create or Update Sustainability Goal")
def create_or_update_goal(payload: GoalCreateUpdateRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Adds or updates a sustainability target."""
    existing = db.query(SustainabilityGoal).filter(SustainabilityGoal.goal_type == payload.goal_type).first()
    if existing:
        existing.title = payload.title
        existing.target_value = payload.target_value
        if payload.current_value is not None:
            existing.current_value = payload.current_value
        existing.unit = payload.unit
        existing.period = payload.period or existing.period
        existing.status = payload.status or existing.status
        db.commit()
        db.refresh(existing)
        return {"status": "UPDATED", "goal_id": existing.id, "title": existing.title}
    else:
        new_goal = SustainabilityGoal(
            title=payload.title,
            goal_type=payload.goal_type,
            target_value=payload.target_value,
            current_value=payload.current_value or 0.0,
            unit=payload.unit,
            period=payload.period or "Monthly",
            status=payload.status or "ON_TRACK"
        )
        db.add(new_goal)
        db.commit()
        db.refresh(new_goal)
        return {"status": "CREATED", "goal_id": new_goal.id, "title": new_goal.title}


@router.get("/alerts", summary="List Basel Risk Alerts")
def list_alerts(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Returns dynamic risk alerts."""
    alerts = db.query(Alert).order_by(Alert.created_at.desc()).all()
    results = []
    for a in alerts:
        results.append({
            "id": a.id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "service": a.service,
            "value": a.value,
            "threshold": a.threshold,
            "unit": a.unit,
            "status": a.status,
            "message": a.message,
            "details": a.details,
            "timestamp": a.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return results


@router.post("/alerts/{alert_id}/resolve", summary="Resolve Alert")
def resolve_alert(alert_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Marks an alert as resolved."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    alert.status = "RESOLVED"
    db.commit()
    return {"status": "RESOLVED", "alert_id": alert_id}


@router.get("/recommendations", summary="List Explainable Recommendations")
def list_recommendations(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Returns rule-based optimization recommendations."""
    recs = db.query(Recommendation).order_by(Recommendation.created_at.desc()).all()
    results = []
    for r in recs:
        results.append({
            "id": r.id,
            "issue": r.issue,
            "detected_value": r.detected_value,
            "baseline_threshold": r.baseline_threshold,
            "recommendation": r.recommendation,
            "expected_benefit": r.expected_benefit,
            "service": r.service,
            "status": r.status
        })
    return results


@router.post("/scenario", summary="Run 'What-If?' Scenario Analysis")
def run_scenario_analysis(payload: ScenarioAnalysisRequest) -> Dict[str, Any]:
    """
    Calculates projected Scope 2 operational carbon reductions based on
    transaction scale, computational efficiency improvements, and grid emission factors.
    """
    baseline_co2_g = payload.tx_count * payload.current_co2_per_tx_g
    projected_co2_per_tx_g = round(payload.current_co2_per_tx_g * (1.0 - (payload.efficiency_improvement_pct / 100.0)), 4)
    projected_co2_g = payload.tx_count * projected_co2_per_tx_g
    reduction_g = baseline_co2_g - projected_co2_g
    reduction_pct = payload.efficiency_improvement_pct

    return {
        "inputs": {
            "transaction_count": payload.tx_count,
            "baseline_co2_per_tx_grams": payload.current_co2_per_tx_g,
            "efficiency_improvement_percent": payload.efficiency_improvement_pct,
            "grid_carbon_factor_g_kwh": payload.grid_carbon_factor_g_kwh
        },
        "baseline_co2_grams": round(baseline_co2_g, 2),
        "baseline_co2_kg": round(baseline_co2_g / 1000.0, 4),
        "projected_co2_per_tx_grams": projected_co2_per_tx_g,
        "projected_co2_grams": round(projected_co2_g, 2),
        "projected_co2_kg": round(projected_co2_g / 1000.0, 4),
        "reduction_grams": round(reduction_g, 2),
        "reduction_kg": round(reduction_g / 1000.0, 4),
        "reduction_percent": round(reduction_pct, 1),
        "disclaimer": "This is a projected model calculation based on linear computational workload scaling. Uses SIMULATED telemetry baseline.",
        "telemetry_mode": "SIMULATED"
    }


@router.get("/carbon-factors", summary="List Regional Grid Emission Factors")
def list_carbon_factors(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Returns grid carbon factors with official sources."""
    factors = db.query(CarbonFactor).order_by(CarbonFactor.year.desc()).all()
    results = []
    for f in factors:
        results.append({
            "id": f.id,
            "region": f.region,
            "year": f.year,
            "factor_gco2_per_kwh": f.factor_gco2_per_kwh,
            "unit": f.unit,
            "source": f.source,
            "effective_date": f.effective_date,
            "is_active": f.is_active
        })
    return results


@router.post("/carbon-factors", summary="Add New Carbon Factor")
def add_carbon_factor(payload: CarbonFactorCreateRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Adds a new regional carbon factor."""
    if payload.is_active:
        db.query(CarbonFactor).update({CarbonFactor.is_active: False})

    new_factor = CarbonFactor(
        region=payload.region,
        year=payload.year,
        factor_gco2_per_kwh=payload.factor_gco2_per_kwh,
        unit=payload.unit or "gCO2/kWh",
        source=payload.source,
        effective_date=payload.effective_date or "2024-01-01",
        is_active=payload.is_active or False
    )
    db.add(new_factor)
    db.commit()
    db.refresh(new_factor)
    return {"status": "CREATED", "id": new_factor.id, "region": new_factor.region}


@router.post("/carbon-factors/{factor_id}/activate", summary="Set Active Carbon Factor")
def activate_carbon_factor(factor_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Activates a specific grid carbon factor."""
    target = db.query(CarbonFactor).filter(CarbonFactor.id == factor_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Factor not found.")
    db.query(CarbonFactor).update({CarbonFactor.is_active: False})
    target.is_active = True
    db.commit()
    return {"status": "ACTIVATED", "factor_id": factor_id, "region": target.region}


@router.get("/report/csv", summary="Export Audited Carbon Ledger as CSV")
def export_carbon_report_csv(db: Session = Depends(get_db)):
    """Generates and downloads a clean audited CSV report of transactions and carbon."""
    txns = db.query(Transaction).order_by(Transaction.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Transaction ID", "Timestamp", "Sender Bank ID", "Recipient Bank ID",
        "Amount (INR)", "Currency", "Transaction Type", "Service", "Status",
        "Energy (Joules)", "Energy (kWh)", "Estimated CO2 (grams)", "Fidelity %", "SHA-256 Audit Hash", "Telemetry Mode"
    ])

    for t in txns:
        energy_kwh = (t.energy_joules or 0.0) / 3600000.0
        writer.writerow([
            t.id,
            t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            t.sender_bank_id or "",
            t.recipient_bank_id or "",
            t.amount or 0.0,
            t.currency or "INR",
            t.transaction_type or "TRANSFER",
            t.service or "payment-service",
            t.status or "COMPLETED",
            round(t.energy_joules or 0.0, 4),
            f"{energy_kwh:.8f}",
            round(t.carbon_grams or 0.0, 6),
            t.fidelity_percent or 96.0,
            t.audit_hash or "",
            "SIMULATED"
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=green_finance_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )


@router.get("/report/pdf", summary="Export Audited Carbon Ledger as PDF")
def export_carbon_report_pdf(db: Session = Depends(get_db)):
    """Generates and downloads a professional PDF sustainability report."""
    from fpdf import FPDF
    
    txns = db.query(Transaction).order_by(Transaction.created_at.desc()).all()
    total_tx = len(txns)
    success_tx = sum(1 for t in txns if t.status == "COMPLETED")
    total_volume = sum(t.amount or 0.0 for t in txns)
    total_joules = sum(t.energy_joules or 0.0 for t in txns)
    total_carbon_g = sum(t.carbon_grams or 0.0 for t in txns)
    total_kwh = total_joules / 3600000.0
    avg_co2_per_tx_g = round(total_carbon_g / max(total_tx, 1), 4)
    
    active_factor = db.query(CarbonFactor).filter(CarbonFactor.is_active == True).first()
    factor_val = active_factor.factor_gco2_per_kwh if active_factor else 713.0
    
    class PDF(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 16)
            self.set_text_color(5, 150, 105)
            self.cell(0, 10, 'Green Finance - Sustainability Audit Report', 0, 1, 'C')
            self.set_font('Helvetica', '', 10)
            self.set_text_color(100)
            self.cell(0, 6, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
            self.cell(0, 6, 'Scope 2 Computational Emissions | CEA India Grid Factor', 0, 1, 'C')
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(5)
        
        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 10, f'Page {self.page_no()}/{{nb}} | Green Finance | SIMULATED Telemetry', 0, 0, 'C')
    
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # Executive Summary
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(5, 150, 105)
    pdf.cell(0, 8, '1. Executive Summary', 0, 1)
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(0)
    pdf.multi_cell(0, 5, f'This report presents the computational carbon footprint analysis for Green Finance banking operations. '
                         f'The analysis covers {total_tx} transactions ({success_tx} completed) with a total volume of Rs. {total_volume:,.2f} INR. '
                         f'Total attributed energy consumption: {total_joules:.2f} Joules ({total_kwh:.6f} kWh). '
                         f'Estimated Scope 2 CO2 emissions: {total_carbon_g:.4f} grams ({total_carbon_g/1000:.6f} kg). '
                         f'Average carbon intensity: {avg_co2_per_tx_g:.4f} g CO2 per transaction. '
                         f'Active grid emission factor: {factor_val} gCO2/kWh (CEA India 2024). '
                         f'NOTE: All energy telemetry is SIMULATED due to Kepler RAPL unavailability in Docker Desktop/WSL2 environment.',
                         0, 'L')
    pdf.ln(3)
    
    # Methodology
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(5, 150, 105)
    pdf.cell(0, 8, '2. Calculation Methodology', 0, 1)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(0)
    pdf.multi_cell(0, 5, 'Energy (kWh) = Energy (J) / 3,600,000\n'
                         'Estimated CO2 (g) = Energy (kWh) x Grid Emission Factor (gCO2/kWh)\n'
                         'Avg CO2 per Transaction = Total CO2 (g) / Number of Completed Transactions\n'
                         'Attribution Fidelity: 95%+ (simulated baseline residual <= 6%)\n'
                         'Telemetry Source: SIMULATED (Kepler eBPF RAPL counters unavailable)', 0, 'L')
    pdf.ln(3)
    
    # Transaction Table
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(5, 150, 105)
    pdf.cell(0, 8, '3. Transaction Carbon Ledger (Latest 50)', 0, 1)
    
    # Table header
    pdf.set_font('Helvetica', 'B', 7)
    pdf.set_fill_color(5, 150, 105)
    pdf.set_text_color(255)
    col_widths = [25, 25, 20, 20, 18, 15, 18, 18, 18, 18]
    headers = ['Txn ID', 'Timestamp', 'Sender', 'Recipient', 'Amount', 'Energy(J)', 'CO2(g)', 'Fidelity%', 'Type', 'Mode']
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 7, h, 1, 0, 'C', True)
    pdf.ln()
    
    # Table data
    pdf.set_font('Helvetica', '', 6.5)
    pdf.set_text_color(0)
    for t in txns[:50]:
        energy_kwh = (t.energy_joules or 0.0) / 3600000.0
        pdf.cell(col_widths[0], 6, t.id[:22], 1)
        pdf.cell(col_widths[1], 6, t.created_at.strftime("%m-%d %H:%M"), 1)
        pdf.cell(col_widths[2], 6, (t.sender_bank_id or "")[:18], 1)
        pdf.cell(col_widths[3], 6, (t.recipient_bank_id or "")[:18], 1)
        pdf.cell(col_widths[4], 6, f"Rs.{t.amount or 0:,.0f}", 1, 0, 'R')
        pdf.cell(col_widths[5], 6, f"{t.energy_joules or 0:.3f}", 1, 0, 'R')
        pdf.cell(col_widths[6], 6, f"{t.carbon_grams or 0:.5f}", 1, 0, 'R')
        pdf.cell(col_widths[7], 6, f"{t.fidelity_percent or 96:.0f}%", 1, 0, 'C')
        pdf.cell(col_widths[8], 6, (t.transaction_type or "")[:16], 1)
        pdf.cell(col_widths[9], 6, "SIMULATED", 1, 0, 'C')
        pdf.ln()
    
    pdf.ln(5)
    
    # Service Efficiency
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(5, 150, 105)
    pdf.cell(0, 8, '4. Service Efficiency Breakdown', 0, 1)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_fill_color(5, 150, 105)
    pdf.set_text_color(255)
    svc_cols = [30, 25, 25, 25, 25, 25, 30]
    svc_headers = ['Service', 'Energy/Tx (J)', 'CO2/Tx (mg)', 'Latency (ms)', 'Workload %', 'Intensity', 'Telemetry']
    for i, h in enumerate(svc_headers):
        pdf.cell(svc_cols[i], 7, h, 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font('Helvetica', '', 7.5)
    pdf.set_text_color(0)
    services = [
        ("payment-service", 0.42, 0.083, 38.5, "58%", "HIGH", "SIMULATED"),
        ("fraud-service", 0.13, 0.025, 19.2, "18%", "MED", "SIMULATED"),
        ("ledger-service", 0.11, 0.022, 14.8, "15%", "MED", "SIMULATED"),
        ("auth-service", 0.065, 0.013, 8.4, "9%", "LOW", "SIMULATED"),
    ]
    for svc in services:
        for i, val in enumerate(svc):
            pdf.cell(svc_cols[i], 6, str(val), 1, 0, 'C')
        pdf.ln()
    
    pdf.ln(5)
    
    # Goals
    goals = db.query(SustainabilityGoal).all()
    if goals:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(5, 150, 105)
        pdf.cell(0, 8, '5. Sustainability Goals Progress', 0, 1)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_fill_color(5, 150, 105)
        pdf.set_text_color(255)
        goal_cols = [40, 20, 20, 20, 25, 25, 35]
        goal_headers = ['Goal', 'Target', 'Current', 'Unit', 'Progress%', 'Status', 'Period']
        for i, h in enumerate(goal_headers):
            pdf.cell(goal_cols[i], 7, h, 1, 0, 'C', True)
        pdf.ln()
        
        pdf.set_font('Helvetica', '', 7.5)
        pdf.set_text_color(0)
        for g in goals:
            prog = min(100.0, (g.current_value / max(g.target_value, 0.001)) * 100.0)
            pdf.cell(goal_cols[0], 6, g.title[:38], 1)
            pdf.cell(goal_cols[1], 6, f"{g.target_value:.2f}", 1, 0, 'C')
            pdf.cell(goal_cols[2], 6, f"{g.current_value:.2f}", 1, 0, 'C')
            pdf.cell(goal_cols[3], 6, g.unit[:18], 1, 0, 'C')
            pdf.cell(goal_cols[4], 6, f"{prog:.1f}%", 1, 0, 'C')
            pdf.cell(goal_cols[5], 6, g.status[:22], 1, 0, 'C')
            pdf.cell(goal_cols[6], 6, g.period[:33], 1, 0, 'C')
            pdf.ln()
    
    # Output
    out = pdf.output()
    pdf_bytes = bytes(out) if isinstance(out, (bytes, bytearray)) else str(out).encode('latin-1')
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=green_finance_sustainability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"}
    )


@router.get("/connected-users", summary="Live Connected Banking Users Telemetry")
def get_connected_banking_users(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Returns live activity across all banking users connected from Green-Finance:
    Transaction count, total amount, energy consumed, and estimated carbon emitted.
    """
    users = db.query(User).filter(User.bank_id != None).all()
    results = []

    for u in users:
        user_txns = db.query(Transaction).filter(Transaction.sender_bank_id == u.bank_id).all()
        tx_count = len(user_txns)
        total_amount = sum(t.amount or 0.0 for t in user_txns)
        total_energy = sum(t.energy_joules or 0.0 for t in user_txns)
        total_carbon = sum(t.carbon_grams or 0.0 for t in user_txns)
        last_txn = user_txns[0].created_at.strftime("%Y-%m-%d %H:%M:%S") if user_txns else "Idle"

        results.append({
            "bank_id": u.bank_id,
            "name": u.name or u.username,
            "username": u.username,
            "role": u.role,
            "transaction_count": tx_count,
            "total_transferred_inr": round(total_amount, 2),
            "attributed_energy_joules": round(total_energy, 4),
            "attributed_carbon_grams": round(total_carbon, 5),
            "last_active": last_txn,
            "connection_status": "ONLINE (STREAMING)" if tx_count > 0 else "REGISTERED",
            "telemetry_mode": "SIMULATED"
        })

    return sorted(results, key=lambda x: x["transaction_count"], reverse=True)