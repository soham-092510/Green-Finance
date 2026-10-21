# =====================================================================
# GREEN-FINANCE — RBAC_SERVICE.PY (RBAC & DELEGATION ENGINE)
# Purpose: Server-side authorization verification, scoped delegation ceilings,
#          Boss Admin one-time bootstrap, and immutable security audit logs.
# =====================================================================

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.models.user import User
from backend.models.rbac import (
    Role, Permission, RolePermission, UserRole,
    PermissionDelegation, SecurityAuditEvent,
    InvestigationCase, InvestigationAssignment
)
from backend.services.auth_service import revoke_all_user_sessions
from backend.core.security import hash_password
from backend.middleware.logger import logger


DEFAULT_PERMISSIONS = [
    # Banking
    ("transactions.create_transfer", "banking", "Initiate transfer from own cash wallet"),
    ("transactions.read_own", "banking", "View own transactions and balances"),
    ("transactions.read_all", "banking", "View all system transactions"),
    # User Management
    ("users.read_scoped", "admin", "View users within administrative scope"),
    ("users.suspend_scoped", "admin", "Suspend or restore users"),
    ("admins.create_scoped", "admin", "Create delegated administrators"),
    ("admins.manage_scoped", "admin", "Manage delegated administrators"),
    ("roles.assign_delegable", "admin", "Assign delegable roles and permissions"),
    # Investigation
    ("cases.read_assigned", "investigation", "View assigned investigation cases"),
    ("cases.investigate", "investigation", "Document findings and update assigned case"),
    ("cases.assign", "investigation", "Create cases and assign to investigators"),
    # Assets & Telemetry
    ("credits.mint", "credits", "Mint verified carbon credits"),
    ("telemetry.manage", "telemetry", "Run calibration, lock baselines, execute PromQL"),
    # Governance & Audit
    ("security_audit.read", "governance", "View security audit and administrative logs"),
    ("operations.read", "operations", "View real-time operations and telemetry monitoring"),
]

ROLE_PERMISSION_MAP = {
    "SUPER_ADMIN": [p[0] for p in DEFAULT_PERMISSIONS],  # All permissions
    "ADMIN": [
        "transactions.read_own",
        "users.read_scoped",
        "users.suspend_scoped",
        "admins.create_scoped",
        "roles.assign_delegable",
        "cases.read_assigned",
        "cases.investigate",
        "cases.assign",
        "telemetry.manage",
        "operations.read"
    ],
    "INVESTIGATOR": [
        "transactions.read_own",
        "cases.read_assigned",
        "cases.investigate",
        "operations.read"
    ],
    "AUDITOR": [
        "transactions.read_own",
        "transactions.read_all",
        "security_audit.read",
        "operations.read"
    ],
    "CUSTOMER": [
        "transactions.create_transfer",
        "transactions.read_own"
    ]
}


def log_security_event(
    db: Session,
    action: str,
    outcome: str,
    actor: Optional[User] = None,
    target_id: Optional[str] = None,
    target_type: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> SecurityAuditEvent:
    """Appends an immutable record to the security audit log."""
    event = SecurityAuditEvent(
        actor_id=actor.id if actor else None,
        actor_username=actor.username if actor else "SYSTEM/ANONYMOUS",
        action=action,
        target_id=str(target_id) if target_id else None,
        target_type=target_type,
        outcome=outcome,
        ip_address=ip_address,
        details=json.dumps(details) if details else None
    )
    db.add(event)
    try:
        db.commit()
    except Exception:
        db.rollback()
    return event


def init_rbac_system(db: Session) -> None:
    """Initializes roles and permissions catalog in database if not present."""
    # 1. Seed Permissions
    for code, category, desc in DEFAULT_PERMISSIONS:
        existing = db.query(Permission).filter(Permission.code == code).first()
        if not existing:
            p = Permission(code=code, category=category, description=desc)
            db.add(p)
    db.commit()

    # 2. Seed Roles
    for role_name in ROLE_PERMISSION_MAP.keys():
        existing = db.query(Role).filter(Role.name == role_name).first()
        if not existing:
            r = Role(
                name=role_name,
                description=f"Standard {role_name} role profile",
                is_system_role=True
            )
            db.add(r)
    db.commit()

    # 3. Seed Role Permissions
    for role_name, perm_codes in ROLE_PERMISSION_MAP.items():
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            continue
        for code in perm_codes:
            perm = db.query(Permission).filter(Permission.code == code).first()
            if perm:
                existing_rp = db.query(RolePermission).filter(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == perm.id
                ).first()
                if not existing_rp:
                    db.add(RolePermission(role_id=role.id, permission_id=perm.id))
    db.commit()


def has_permission(db: Session, user: User, permission_code: str) -> bool:
    """
    Checks if a user has a specific permission via Boss Admin status,
    assigned roles, or explicit delegations.
    """
    if not user or user.status != "ACTIVE":
        return False

    # Boss Admin has all permissions unconditionally
    if getattr(user, "is_boss_admin", False) or user.role == "SUPER_ADMIN":
        return True

    # 1. Check primary role permissions
    perm_codes = ROLE_PERMISSION_MAP.get(user.role, [])
    if permission_code in perm_codes:
        return True

    # 2. Check direct delegations
    delegation = db.query(PermissionDelegation).filter(
        PermissionDelegation.delegatee_id == user.id,
        PermissionDelegation.permission_code == permission_code
    ).first()
    if delegation:
        return True

    return False


def bootstrap_boss_admin(
    db: Session,
    username: str,
    password: str,
    email: str,
    name: str = "Root Boss Admin",
    ip_address: Optional[str] = None
) -> User:
    """
    One-time secure initialization of the root Boss Admin.
    FAILS CLOSED if an existing Boss Admin is already present.
    """
    # Verify One-Time Bootstrap Invariant
    existing_boss = db.query(User).filter(
        (User.is_boss_admin == True) | (User.role == "SUPER_ADMIN")
    ).first()

    if existing_boss:
        log_security_event(
            db=db,
            action="BOOTSTRAP_ATTEMPT_DENIED",
            outcome="DENIED",
            target_id=username,
            target_type="user",
            ip_address=ip_address,
            details={"reason": "Boss Admin already initialized. Repeated bootstrap forbidden."}
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Initialization Error: The Boss Admin has already been bootstrapped on this system."
        )

    # Check if user with same username/email exists
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is already registered."
        )

    # Create root Boss Admin
    boss_admin = User(
        username=username,
        email=email,
        name=name,
        bank_id="BOSS001",
        hashed_password=hash_password(password),
        role="SUPER_ADMIN",
        is_boss_admin=True,
        status="ACTIVE"
    )
    db.add(boss_admin)
    db.commit()
    db.refresh(boss_admin)

    log_security_event(
        db=db,
        action="BOSS_ADMIN_BOOTSTRAPPED",
        outcome="SUCCESS",
        actor=boss_admin,
        target_id=boss_admin.id,
        target_type="user",
        ip_address=ip_address,
        details={"username": boss_admin.username, "role": "SUPER_ADMIN"}
    )
    logger.info(f"Boss Admin successfully bootstrapped: {boss_admin.username}")
    return boss_admin


def assign_role_to_user(
    db: Session,
    actor: User,
    target_user_id: str,
    new_role: str,
    ip_address: Optional[str] = None
) -> User:
    """
    Assigns role to target user subject to strict delegation hierarchy:
    - Delegated Admins CANNOT assign SUPER_ADMIN.
    - Delegated Admins CANNOT modify Boss Admin.
    - Delegated Admins CANNOT elevate their own role.
    """
    target = db.query(User).filter(User.id == target_user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found.")

    # Invariant 1: Cannot modify Boss Admin
    if target.is_boss_admin or target.role == "SUPER_ADMIN":
        log_security_event(
            db=db, action="ROLE_ASSIGN_DENIED", outcome="DENIED",
            actor=actor, target_id=target.id, target_type="user", ip_address=ip_address,
            details={"reason": "Attempted modification of protected Boss Admin"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission Denied: Subordinate administrators cannot alter the Boss Admin."
        )

    # Invariant 2: Cannot self-escalate
    if actor.id == target.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission Denied: Administrators cannot escalate their own role."
        )

    # Invariant 3: Only Boss Admin can grant SUPER_ADMIN
    if new_role == "SUPER_ADMIN" and not actor.is_boss_admin:
        log_security_event(
            db=db, action="PRIVILEGE_ESCALATION_BLOCKED", outcome="DENIED",
            actor=actor, target_id=target.id, target_type="user", ip_address=ip_address,
            details={"reason": "Non-boss admin attempted to grant SUPER_ADMIN"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission Denied: Only the Boss Admin can appoint a Super Administrator."
        )

    # Invariant 4: Delegated admin must possess admins.manage_scoped permission
    if not has_permission(db, actor, "admins.manage_scoped"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You lack permissions to manage user roles."
        )

    old_role = target.role
    target.role = new_role
    db.commit()

    # Invalidate target's active sessions immediately so new role takes effect
    revoke_all_user_sessions(db, target.id, reason="ROLE_CHANGE")

    log_security_event(
        db=db, action="ROLE_ASSIGNED", outcome="SUCCESS",
        actor=actor, target_id=target.id, target_type="user", ip_address=ip_address,
        details={"old_role": old_role, "new_role": new_role}
    )
    return target


def suspend_user_account(
    db: Session,
    actor: User,
    target_user_id: str,
    reason: str = "Administrative suspension",
    ip_address: Optional[str] = None
) -> User:
    """
    Suspends a user account and immediately terminates all active sessions.
    Subordinate admins CANNOT suspend the Boss Admin.
    """
    target = db.query(User).filter(User.id == target_user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found.")

    if target.is_boss_admin or target.role == "SUPER_ADMIN":
        log_security_event(
            db=db, action="SUSPEND_ATTEMPT_DENIED", outcome="DENIED",
            actor=actor, target_id=target.id, target_type="user", ip_address=ip_address,
            details={"reason": "Attempted suspension of Boss Admin"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission Denied: The Boss Admin cannot be suspended."
        )

    if not has_permission(db, actor, "users.suspend_scoped"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You lack permissions to suspend users."
        )

    target.status = "SUSPENDED"
    db.commit()

    # Immediately revoke active sessions
    revoked_count = revoke_all_user_sessions(db, target.id, reason=f"SUSPENDED: {reason}")

    log_security_event(
        db=db, action="USER_SUSPENDED", outcome="SUCCESS",
        actor=actor, target_id=target.id, target_type="user", ip_address=ip_address,
        details={"reason": reason, "revoked_sessions": revoked_count}
    )
    return target


def delegate_permission_to_admin(
    db: Session,
    actor: User,
    target_user_id: str,
    permission_code: str,
    can_subdelegate: bool = False,
    ip_address: Optional[str] = None
) -> PermissionDelegation:
    """
    Delegates a specific permission with ceiling enforcement:
    - Delegator must have the permission themselves.
    - Delegator cannot delegate permissions beyond their own authority.
    """
    target = db.query(User).filter(User.id == target_user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found.")

    # Check delegator holds the permission
    if not has_permission(db, actor, permission_code):
        log_security_event(
            db=db, action="DELEGATION_CEILING_EXCEEDED", outcome="DENIED",
            actor=actor, target_id=target.id, target_type="permission", ip_address=ip_address,
            details={"attempted_permission": permission_code}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Ceiling Exceeded: You cannot delegate permission '{permission_code}' which you do not possess."
        )

    # Check if delegator has role assignment permission
    if not has_permission(db, actor, "roles.assign_delegable"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You lack authorization to delegate permissions."
        )

    # Check if delegation already exists
    existing = db.query(PermissionDelegation).filter(
        PermissionDelegation.delegatee_id == target.id,
        PermissionDelegation.permission_code == permission_code
    ).first()
    if existing:
        return existing

    delegation = PermissionDelegation(
        delegator_id=actor.id,
        delegatee_id=target.id,
        permission_code=permission_code,
        can_subdelegate=can_subdelegate
    )
    db.add(delegation)
    db.commit()
    db.refresh(delegation)

    log_security_event(
        db=db, action="PERMISSION_DELEGATED", outcome="SUCCESS",
        actor=actor, target_id=target.id, target_type="permission", ip_address=ip_address,
        details={"permission": permission_code, "can_subdelegate": can_subdelegate}
    )
    return delegation
