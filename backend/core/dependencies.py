# =====================================================================
# GREEN-FINANCE — DEPENDENCIES.PY (REUSABLE FASTAPI DEPENDENCIES)
# Purpose: Enforces server-side authentication, extracts JWT tokens from
#          Bearer headers or secure cookies, verifies session revocation
#          state in auth_sessions, and validates account status.
# =====================================================================

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from backend.db.session import get_db
from backend.core.security import decode_access_token
from backend.models.user import User
from backend.models.session import AuthSession

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def extract_token(request: Request, bearer_token: Optional[str] = Depends(oauth2_scheme)) -> Optional[str]:
    """Extracts JWT token from Authorization header or HttpOnly cookie."""
    if bearer_token:
        return bearer_token
    # Fallback to cookie
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

    # Check account status
    if user.status in ("SUSPENDED", "DISABLED"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.lower()}. Access denied."
        )

    # Attach token JTI to request state for optional logout handling
    request.state.token_jti = jti
    return user
