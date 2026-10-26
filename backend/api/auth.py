# =====================================================================
# GREEN-FINANCE — AUTH.PY (AUTHENTICATION API ROUTER)
# Purpose: Handles registration, login (form or JSON), logout/revocation,
#          and session verification.
# =====================================================================

import secrets
from typing import Optional
from fastapi import APIRouter, Depends, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.core.dependencies import get_current_user
from backend.core.config import settings
from backend.models.user import User
from backend.schemas.auth_schema import UserRegister, Token, LoginJsonRequest
from backend.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

SESSION_COOKIE_NAME = "access_token"
CSRF_COOKIE_NAME = "csrf_token"
SESSION_MAX_AGE = settings.access_token_expire_minutes * 60


def set_session_cookies(response: Response, access_token: str, csrf_token: str) -> None:
    """Sets secure HttpOnly session cookie and readable CSRF token cookie."""
    is_prod = str(settings.environment).lower() == "production"
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        path="/",
        max_age=SESSION_MAX_AGE
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=False,  # Client-side JavaScript reads this to attach X-CSRF-Token header
        secure=is_prod,
        samesite="lax",
        path="/",
        max_age=SESSION_MAX_AGE
    )


def clear_session_cookies(response: Response) -> None:
    """Explicitly clears authentication and CSRF cookies."""
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(key=CSRF_COOKIE_NAME, path="/")


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer account"
)
def register(
    schema: UserRegister,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Registers a new Customer account with default double-entry ledger accounts.
    Role is strictly defaulted to CUSTOMER on server.
    """
    user = auth_service.register_user(db=db, schema=schema)
    tokens = auth_service.authenticate_user(
        db=db,
        username=schema.username,
        password=schema.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    csrf_token = secrets.token_urlsafe(32)
    tokens["csrf_token"] = csrf_token
    set_session_cookies(response=response, access_token=tokens["access_token"], csrf_token=csrf_token)
    return tokens


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate with OAuth2 form credentials"
)
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Handles OAuth2 form-data login."""
    tokens = auth_service.authenticate_user(
        db=db,
        username=form_data.username,
        password=form_data.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    csrf_token = secrets.token_urlsafe(32)
    tokens["csrf_token"] = csrf_token
    set_session_cookies(response=response, access_token=tokens["access_token"], csrf_token=csrf_token)
    return tokens


@router.post(
    "/login-json",
    response_model=Token,
    summary="Authenticate with JSON credentials"
)
def login_json(
    payload: LoginJsonRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Handles JSON login from modern web frontends."""
    tokens = auth_service.authenticate_user(
        db=db,
        username=payload.username,
        password=payload.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    csrf_token = secrets.token_urlsafe(32)
    tokens["csrf_token"] = csrf_token
    set_session_cookies(response=response, access_token=tokens["access_token"], csrf_token=csrf_token)
    return tokens


@router.post(
    "/logout",
    summary="Revoke current session"
)
def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revokes the current JWT session token immediately and clears cookies."""
    jti = getattr(request.state, "token_jti", None)
    if jti:
        auth_service.logout_user(db=db, token_jti=jti)
    clear_session_cookies(response=response)
    return {"status": "success", "message": "Session successfully revoked"}

