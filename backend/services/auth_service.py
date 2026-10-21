# =====================================================================
# GREEN-FINANCE — AUTH_SERVICE.PY (AUTHENTICATION SERVICE)
# Purpose: Core business logic for user registration, authentication,
#          session issuance with unique JTIs, session revocation, and lockout.
# =====================================================================

import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.models.user import User
from backend.models.account import Account
from backend.models.session import AuthSession
from backend.schemas.auth_schema import UserRegister
from backend.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token
)
from backend.core.config import settings
from backend.middleware.logger import logger


def register_user(db: Session, schema: UserRegister) -> User:
    """
    Registers a new user strictly with role=CUSTOMER.
    Never accepts caller-controlled roles. Creates double-entry asset,
    liability, and cash wallet accounts transactionally.
    """
    existing_username = db.query(User).filter(User.username == schema.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already registered"
        )

    existing_email = db.query(User).filter(User.email == schema.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered"
        )

    bank_id = f"GF{random.randint(100000, 999999)}"

    new_user = User(
        name=schema.name or schema.username,
        username=schema.username,
        email=schema.email,
        bank_id=bank_id,
        hashed_password=hash_password(schema.password),
        role="CUSTOMER",  # Enforce CUSTOMER role strictly
        status="ACTIVE",
        is_boss_admin=False
    )
    db.add(new_user)
    db.flush()

    # Create double-entry accounts
    cash_wallet = Account(
        user_id=new_user.id,
        name="cash_wallet",
        type="asset",
        balance=10000.0  # Seed initial demo liquidity
    )
    carbon_asset = Account(
        user_id=new_user.id,
        name="carbon_asset",
        type="asset",
        balance=100.0
    )
    carbon_liability = Account(
        user_id=new_user.id,
        name="carbon_liability",
        type="liability",
        balance=0.0
    )

    db.add(cash_wallet)
    db.add(carbon_asset)
    db.add(carbon_liability)
    db.commit()
    db.refresh(new_user)

    logger.info(f"User registered successfully: {new_user.username} ({new_user.bank_id})")
    return new_user


def authenticate_user(
    db: Session,
    username: str,
    password: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validates credentials, protects against brute-force lockout,
    issues JWT with unique JTI, and registers an active session in auth_sessions.
    """
    user = db.query(User).filter(User.username == username).first()

    # Check lockout
    now = datetime.utcnow()
    if user and user.locked_until and user.locked_until > now:
        remaining_seconds = int((user.locked_until - now).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account temporarily locked due to failed attempts. Try again in {remaining_seconds} seconds."
        )

    # Check account status
    if user and user.status in ("SUSPENDED", "DISABLED"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.status.lower()}. Please contact administrator."
        )

    # Verify credentials
    is_valid = False
    if user:
        is_valid = verify_password(password, user.hashed_password)

    if not is_valid:
        if user:
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= 5:
                user.locked_until = now + timedelta(minutes=15)
                logger.warning(f"User account locked due to 5 failed attempts: {user.username}")
            db.commit()
        # Constant generic response to prevent username enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None

    # Generate distinct JTIs
    access_jti = str(uuid.uuid4())
    refresh_jti = str(uuid.uuid4())

    access_payload = {
        "sub": user.username,
        "role": user.role,
        "is_boss_admin": user.is_boss_admin,
        "bank_id": user.bank_id,
        "jti": access_jti
    }
    refresh_payload = {
        "sub": user.username,
        "jti": refresh_jti
    }

    access_token = create_access_token(data=access_payload)
    refresh_token = create_refresh_token(data=refresh_payload)

    # Register active session in DB for revocation tracking
    session_record = AuthSession(
        user_id=user.id,
        token_jti=access_jti,
        is_revoked=False,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=now + timedelta(minutes=settings.access_token_expire_minutes)
    )
    db.add(session_record)
    db.commit()

    logger.info(f"User logged in: {user.username} | Role: {user.role} | JTI: {access_jti}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "jti": access_jti,
        "user": {
            "username": user.username,
            "role": user.role,
            "bank_id": user.bank_id,
            "name": user.name,
            "is_boss_admin": user.is_boss_admin
        }
    }


def logout_user(db: Session, token_jti: str) -> bool:
    """Revokes a session immediately."""
    session_rec = db.query(AuthSession).filter(AuthSession.token_jti == token_jti).first()
    if session_rec:
        session_rec.is_revoked = True
        session_rec.revoked_at = datetime.utcnow()
        session_rec.revoked_reason = "USER_LOGOUT"
        db.commit()
        logger.info(f"Revoked session token JTI: {token_jti}")
        return True
    return False


def revoke_all_user_sessions(db: Session, user_id: str, reason: str = "ADMIN_REVOCATION") -> int:
    """Revokes all active sessions for a user (used upon suspension or role change)."""
    now = datetime.utcnow()
    count = db.query(AuthSession).filter(
        AuthSession.user_id == user_id,
        AuthSession.is_revoked == False
    ).update({
        AuthSession.is_revoked: True,
        AuthSession.revoked_at: now,
        AuthSession.revoked_reason: reason
    })
    db.commit()
    logger.info(f"Revoked {count} sessions for user_id={user_id} (Reason: {reason})")
    return count
