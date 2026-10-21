# =====================================================================
# GREEN-FINANCE — RBAC.PY (HIERARCHICAL RBAC & AUDIT MODELS)
# Purpose: Defines SQLAlchemy models for granular role-based access control,
#          permission delegations, investigator case assignments, and append-only
#          security audit events.
# =====================================================================

from backend.db.base import Base
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey, UniqueConstraint, func
import uuid


class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    is_system_role = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=func.now())


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(100), unique=True, nullable=False, index=True)  # e.g. "transactions.create_transfer"
    category = Column(String(50), nullable=False)                         # e.g. "banking", "admin", "investigation"
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(String(36), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    granted_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    granted_at = Column(DateTime, nullable=False, default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )


class PermissionDelegation(Base):
    __tablename__ = "permission_delegations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    delegator_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    delegatee_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_code = Column(String(100), nullable=False, index=True)
    can_subdelegate = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=func.now())


class InvestigationCase(Base):
    __tablename__ = "investigation_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    case_number = Column(String(50), unique=True, nullable=False, index=True)  # e.g. "CASE-2026-001"
    title = Column(String(200), nullable=False)
    severity = Column(String(20), nullable=False, default="MEDIUM")           # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(20), nullable=False, default="OPEN")               # OPEN, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    findings = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())


class InvestigationAssignment(Base):
    __tablename__ = "investigation_assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(36), ForeignKey("investigation_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    investigator_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime, nullable=False, default=func.now())

    __table_args__ = (
        UniqueConstraint("case_id", "investigator_id", name="uq_case_investigator"),
    )


class SecurityAuditEvent(Base):
    __tablename__ = "security_audit_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    actor_id = Column(String(36), nullable=True, index=True)
    actor_username = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False, index=True)  # e.g. "ROLE_GRANT", "SESSION_REVOKE", "TRANSFER_DENIED"
    target_id = Column(String(100), nullable=True)
    target_type = Column(String(50), nullable=True)           # "user", "case", "account", "system"
    outcome = Column(String(20), nullable=False)              # "SUCCESS", "FAILURE", "DENIED"
    ip_address = Column(String(45), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=func.now(), index=True)
