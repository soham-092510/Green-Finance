# =====================================================================
# GREEN-FINANCE — DEPENDENCIES.PY (REUSABLE FASTAPI DEPENDENCIES)
# Purpose: Server-side authentication, session revocation validation,
#          and declarative hierarchical RBAC permission enforcement.
# =====================================================================

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional, List

from backend.db.session import get_db
from backend.core.security import decode_access_token
from backend.models.user import User
from backend.models.session import AuthSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def extract_token(request: Request, bearer_token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """Extracts JWT token from Authorization header or HttpOnly cookie."""
    if bearer_token:
        return bearer_token
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        if cookie_token.startswith("Bearer "):
            return cookie_token.split(" ")[1]
        return cookie_token
    return None


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(extract_token)
) -> User:
    """
    Validates token signature, expiration, active session status (not revoked),
    and user account status (not suspended/disabled).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    # Check session revocation if JTI is present
    jti: Optional[str] = payload.get("jti")
    if jti:
        session_rec = db.query(AuthSession).filter(AuthSession.token_jti == jti).first()
        if session_rec and session_rec.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been revoked. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"}
            )

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    if user.status in ("SUSPENDED", "DISABLED"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.lower()}. Access denied."
        )

    request.state.token_jti = jti
    return user


def require_permission(permission_code: str):
    """Declarative FastAPI dependency enforcing granular server-side permissions."""
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        from backend.services.rbac_service import has_permission
        if not has_permission(db, current_user, permission_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Missing required permission '{permission_code}'"
            )
        return current_user
    return permission_checker


def require_role(allowed_roles: List[str]):
    """Declarative FastAPI dependency enforcing allowed role names."""
    def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if getattr(current_user, "is_boss_admin", False) or current_user.role == "SUPER_ADMIN":
            return current_user
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: User role '{current_user.role}' lacks sufficient privileges."
            )
        return current_user
    return role_checker
