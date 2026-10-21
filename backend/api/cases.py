# =====================================================================
# GREEN-FINANCE — CASES.PY (INVESTIGATION WORKFLOW API ROUTER)
# Purpose: Manages carbon anomaly and financial investigation cases:
#          - Enforces strict case boundary: Investigators see ONLY assigned cases
#          - Documenting findings and evidence references
#          - Admin assignment and triage
# =====================================================================

import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.db.session import get_db
from backend.core.dependencies import get_current_user, require_permission
from backend.models.user import User
from backend.models.rbac import InvestigationCase, InvestigationAssignment
from backend.services import rbac_service

router = APIRouter(prefix="/cases", tags=["Investigation Cases"])


class CaseCreateRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    severity: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    transaction_id: Optional[str] = None
    evidence_notes: Optional[str] = None


class CaseAssignRequest(BaseModel):
    investigator_id: str


class FindingsUpdateRequest(BaseModel):
    findings: str = Field(..., min_length=5)
    status: Optional[str] = Field(default="IN_PROGRESS", description="IN_PROGRESS, RESOLVED, CLOSED")


@router.get(
    "",
    summary="List investigation cases (Scoped to assigned cases for Investigators)"
)
def list_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns investigation cases. Investigators see ONLY cases assigned to them.
    Admins and Auditors can view all system cases.
    """
    is_privileged = (
        current_user.is_boss_admin
        or current_user.role in ("SUPER_ADMIN", "ADMIN", "AUDITOR")
    )

    if is_privileged:
        cases = db.query(InvestigationCase).order_by(InvestigationCase.created_at.desc()).all()
    elif current_user.role == "INVESTIGATOR":
        # Strictly filter by assignment
        cases = (
            db.query(InvestigationCase)
            .join(InvestigationAssignment, InvestigationAssignment.case_id == InvestigationCase.id)
            .filter(InvestigationAssignment.investigator_id == current_user.id)
            .order_by(InvestigationCase.created_at.desc())
            .all()
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Standard customers cannot access investigation cases."
        )

    results = []
    for c in cases:
        assignments = db.query(InvestigationAssignment).filter(InvestigationAssignment.case_id == c.id).all()
        results.append({
            "id": c.id,
            "case_number": c.case_number,
            "title": c.title,
            "severity": c.severity,
            "status": c.status,
            "transaction_id": c.transaction_id,
            "findings": c.findings,
            "assigned_investigators_count": len(assignments),
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        })
    return results


@router.get(
    "/{case_id}",
    summary="Get detailed investigation case file (Strict assignment check)"
)
def get_case_detail(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns case detail. Investigators CANNOT access cases not assigned to them.
    """
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Investigation case not found.")

    is_privileged = (
        current_user.is_boss_admin
        or current_user.role in ("SUPER_ADMIN", "ADMIN", "AUDITOR")
    )

    if not is_privileged:
        if current_user.role == "INVESTIGATOR":
            assignment = db.query(InvestigationAssignment).filter(
                InvestigationAssignment.case_id == case_id,
                InvestigationAssignment.investigator_id == current_user.id
            ).first()
            if not assignment:
                rbac_service.log_security_event(
                    db=db, action="CASE_ACCESS_DENIED_UNASSIGNED", outcome="DENIED",
                    actor=current_user, target_id=case_id, target_type="case",
                    details={"reason": "Investigator attempted to view unassigned case"}
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access Denied: You are not assigned to this investigation case."
                )
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied.")

    assignments = db.query(InvestigationAssignment).filter(InvestigationAssignment.case_id == case.id).all()
    investigators = []
    for a in assignments:
        u = db.query(User).filter(User.id == a.investigator_id).first()
        if u:
            investigators.append({"id": u.id, "name": u.name, "username": u.username})

    return {
        "id": case.id,
        "case_number": case.case_number,
        "title": case.title,
        "severity": case.severity,
        "status": case.status,
        "transaction_id": case.transaction_id,
        "findings": case.findings,
        "evidence_json": case.evidence_json,
        "assigned_investigators": investigators,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None
    }


@router.post(
    "",
    summary="Create a new investigation case"
)
def create_case(
    payload: CaseCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("cases.assign"))
):
    """Creates a new carbon anomaly or transaction investigation case."""
    count = db.query(InvestigationCase).count()
    case_number = f"CASE-2026-{(count + 1):03d}"

    case = InvestigationCase(
        case_number=case_number,
        title=payload.title,
        severity=payload.severity.upper(),
        status="OPEN",
        transaction_id=payload.transaction_id,
        created_by=current_user.id,
        evidence_json=json.dumps({"notes": payload.evidence_notes}) if payload.evidence_notes else None
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    rbac_service.log_security_event(
        db=db, action="CASE_CREATED", outcome="SUCCESS",
        actor=current_user, target_id=case.id, target_type="case",
        ip_address=request.client.host if request.client else None,
        details={"case_number": case.case_number, "severity": case.severity}
    )
    return {"status": "success", "case_id": case.id, "case_number": case.case_number}


@router.post(
    "/{case_id}/assign",
    summary="Assign case to an investigator"
)
def assign_investigator(
    case_id: str,
    payload: CaseAssignRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("cases.assign"))
):
    """Assigns an active investigator to a case."""
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    investigator = db.query(User).filter(User.id == payload.investigator_id).first()
    if not investigator or investigator.role != "INVESTIGATOR":
        raise HTTPException(status_code=400, detail="Target user is not an active Investigator.")

    existing = db.query(InvestigationAssignment).filter(
        InvestigationAssignment.case_id == case_id,
        InvestigationAssignment.investigator_id == payload.investigator_id
    ).first()
    if not existing:
        assignment = InvestigationAssignment(
            case_id=case_id,
            investigator_id=payload.investigator_id,
            assigned_by=current_user.id
        )
        db.add(assignment)
        case.status = "ASSIGNED"
        db.commit()

    rbac_service.log_security_event(
        db=db, action="CASE_ASSIGNED", outcome="SUCCESS",
        actor=current_user, target_id=case.id, target_type="case",
        ip_address=request.client.host if request.client else None,
        details={"investigator_id": payload.investigator_id}
    )
    return {"status": "success", "message": f"Assigned to {investigator.username}"}


@router.post(
    "/{case_id}/findings",
    summary="Update investigation findings and status"
)
def update_findings(
    case_id: str,
    payload: FindingsUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates findings on an assigned case."""
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    # Check assignment if investigator
    if current_user.role == "INVESTIGATOR":
        assignment = db.query(InvestigationAssignment).filter(
            InvestigationAssignment.case_id == case_id,
            InvestigationAssignment.investigator_id == current_user.id
        ).first()
        if not assignment:
            raise HTTPException(status_code=403, detail="Access Denied: Unassigned case.")

    case.findings = payload.findings
    case.status = payload.status
    db.commit()

    rbac_service.log_security_event(
        db=db, action="CASE_FINDINGS_RECORDED", outcome="SUCCESS",
        actor=current_user, target_id=case.id, target_type="case",
        ip_address=request.client.host if request.client else None,
        details={"status": case.status}
    )
    return {"status": "success", "message": "Investigation findings recorded."}
