# =====================================================================
# GREEN-FINANCE — DEPENDENCIES.PY (REUSABLE FASTAPI DEPENDENCIES)
# Purpose: Server-side authentication, session revocation validation,
#          and declarative hierarchical RBAC permission enforcement.
# =====================================================================

from datetime import datetime
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
    """
    Extracts JWT token from Authorization header or HttpOnly cookie.
    Query-parameter token extraction is strictly disabled to prevent token leakage in URLs and logs.
    """
    if bearer_token:
        request.state.auth_type = "bearer"
        return bearer_token
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        request.state.auth_type = "cookie"
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
    Validates token signature, expiration, active session status (not revoked/expired),
    CSRF headers for cookie-authenticated mutations, and user account status.
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

    # Check session revocation and expiry if JTI is present in auth_sessions
    jti: Optional[str] = payload.get("jti")
    now = datetime.utcnow()
    if jti:
        session_rec = db.query(AuthSession).filter(AuthSession.token_jti == jti).first()
        if not session_rec or session_rec.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has been revoked or is invalid. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        if session_rec.expires_at and session_rec.expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"}
            )

    # CSRF protection for cookie-authenticated state-changing requests
    auth_type = getattr(request.state, "auth_type", None)
    if auth_type == "cookie" and request.method in ("POST", "PUT", "DELETE", "PATCH"):
        header_csrf = request.headers.get("x-csrf-token") or request.headers.get("X-CSRF-Token")
        cookie_csrf = request.cookies.get("csrf_token")
        if not header_csrf or not cookie_csrf or header_csrf != cookie_csrf:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed: Missing or invalid X-CSRF-Token header"
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


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(extract_token)
) -> Optional[User]:
    """Extracts authenticated user if credentials are provided; returns None otherwise."""
    if not token:
        return None
    try:
        return get_current_user(request=request, db=db, token=token)
    except HTTPException:
        return None


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
