# =====================================================================
# GREEN-FINANCE — ADMIN.PY (ADMINISTRATIVE & GOVERNANCE API ROUTER)
# Purpose: Endpoints for Delegated Admin and Boss Admin:
#          - User management and account suspension
#          - Role assignment with delegation ceiling enforcement
#          - Permission delegations
#          - Security audit trail review
# =====================================================================

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.db.session import get_db
from backend.core.dependencies import get_current_user, require_permission
from backend.models.user import User
from backend.models.rbac import SecurityAuditEvent, PermissionDelegation
from backend.services import rbac_service

router = APIRouter(prefix="/admin", tags=["Administration & Governance"])


class RoleAssignRequest(BaseModel):
    role: str = Field(..., description="Target role name (ADMIN, INVESTIGATOR, AUDITOR, CUSTOMER)")


class SuspendUserRequest(BaseModel):
    reason: str = Field(default="Administrative policy enforcement")


class DelegatePermissionRequest(BaseModel):
    delegatee_id: str
    permission_code: str
    can_subdelegate: bool = False


@router.get(
    "/users",
    summary="List all users within administrative scope"
)
def list_users(
    search: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.read_scoped"))
):
    """Lists registered users and their current roles and account statuses."""
    q = db.query(User)
    if search:
        search_filter = f"%{search}%"
        q = q.filter((User.username.like(search_filter)) | (User.email.like(search_filter)) | (User.bank_id.like(search_filter)))
    if status:
        q = q.filter(User.status == status)
    if role:
        q = q.filter(User.role == role)

    users = q.order_by(User.created_at.desc()).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "name": u.name,
            "bank_id": u.bank_id,
            "role": u.role,
            "status": u.status,
            "is_boss_admin": u.is_boss_admin,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]


@router.post(
    "/users/{user_id}/role",
    summary="Assign role to a user (Delegation ceiling enforced)"
)
def assign_role(
    user_id: str,
    payload: RoleAssignRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admins.manage_scoped"))
):
    """
    Assigns role to a user. Delegated Admins cannot grant SUPER_ADMIN or alter Boss Admin.
    """
    updated_user = rbac_service.assign_role_to_user(
        db=db,
        actor=current_user,
        target_user_id=user_id,
        new_role=payload.role,
        ip_address=request.client.host if request.client else None
    )
    return {
        "status": "success",
        "message": f"Assigned role '{payload.role}' to {updated_user.username}",
        "user_id": updated_user.id,
        "new_role": updated_user.role
    }


@router.post(
    "/users/{user_id}/suspend",
    summary="Suspend a user account and terminate active sessions"
)
def suspend_user(
    user_id: str,
    payload: SuspendUserRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.suspend_scoped"))
):
    """
    Suspends a user account and revokes all active JWT sessions immediately.
    Boss Admin cannot be suspended.
    """
    suspended = rbac_service.suspend_user_account(
        db=db,
        actor=current_user,
        target_user_id=user_id,
        reason=payload.reason,
        ip_address=request.client.host if request.client else None
    )
    return {
        "status": "success",
        "message": f"User {suspended.username} suspended and all active sessions revoked.",
        "user_id": suspended.id,
        "account_status": suspended.status
    }


@router.post(
    "/users/{user_id}/restore",
    summary="Restore a suspended user account"
)
def restore_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("users.suspend_scoped"))
):
    """Restores a suspended user back to ACTIVE status."""
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    target.status = "ACTIVE"
    db.commit()
    rbac_service.log_security_event(
        db=db, action="USER_RESTORED", outcome="SUCCESS",
        actor=current_user, target_id=target.id, target_type="user",
        ip_address=request.client.host if request.client else None
    )
    return {"status": "success", "message": f"User {target.username} restored to ACTIVE."}


@router.post(
    "/delegate",
    summary="Delegate permission to an administrator"
)
def delegate_permission(
    payload: DelegatePermissionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("roles.assign_delegable"))
):
    """
    Delegates an explicit permission to an administrator.
    Delegator cannot grant permissions they do not possess.
    """
    delegation = rbac_service.delegate_permission_to_admin(
        db=db,
        actor=current_user,
        target_user_id=payload.delegatee_id,
        permission_code=payload.permission_code,
        can_subdelegate=payload.can_subdelegate,
        ip_address=request.client.host if request.client else None
    )
    return {
        "status": "success",
        "delegation_id": delegation.id,
        "permission": delegation.permission_code,
        "can_subdelegate": delegation.can_subdelegate
    }


@router.get(
    "/audit-events",
    summary="Review security audit and administrative event logs"
)
def get_audit_events(
    limit: int = 50,
    offset: int = 0,
    action: Optional[str] = None,
    outcome: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("security_audit.read"))
):
    """Returns immutable security audit events for compliance review."""
    q = db.query(SecurityAuditEvent)
    if action:
        q = q.filter(SecurityAuditEvent.action == action)
    if outcome:
        q = q.filter(SecurityAuditEvent.outcome == outcome)

    total = q.count()
    events = q.order_by(SecurityAuditEvent.timestamp.desc()).offset(offset).limit(limit).all()
    return {
        "total_records": total,
        "limit": limit,
        "offset": offset,
        "events": [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "actor_id": e.actor_id,
                "actor_username": e.actor_username,
                "action": e.action,
                "target_id": e.target_id,
                "target_type": e.target_type,
                "outcome": e.outcome,
                "ip_address": e.ip_address,
                "details": e.details
            }
            for e in events
        ]
    }
