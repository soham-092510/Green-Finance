# =====================================================================
# GREEN-FINANCE — AUTH.PY (AUTHENTICATION API ROUTER)
# Purpose: Handles registration, login (form or JSON), logout/revocation,
#          and session verification.
# =====================================================================

from typing import Optional
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.db.session import get_db
from backend.core.dependencies import get_current_user
from backend.models.user import User
from backend.schemas.auth_schema import UserRegister, Token
from backend.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginJsonRequest(BaseModel):
    username: str
    password: str


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer account"
)
def register(
    schema: UserRegister,
    request: Request,
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
    return tokens


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate with OAuth2 form credentials"
)
def login(
    request: Request,
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
    return tokens


@router.post(
    "/login-json",
    response_model=Token,
    summary="Authenticate with JSON credentials"
)
def login_json(
    payload: LoginJsonRequest,
    request: Request,
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
    return tokens


@router.post(
    "/logout",
    summary="Revoke current session"
)
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revokes the current JWT session token immediately."""
    jti = getattr(request.state, "token_jti", None)
    if jti:
        auth_service.logout_user(db=db, token_jti=jti)
    return {"status": "success", "message": "Session successfully revoked"}
