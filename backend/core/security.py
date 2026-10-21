# =====================================================================
# GREEN-FINANCE — SECURITY.PY (CRYPTOGRAPHY & TOKENS)
# Purpose: Manages Argon2id password hashing (with bcrypt backward compatibility)
#          and cryptographically signed JWT sessions with unique JTIs.
# =====================================================================

import uuid
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
    _ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=1)
except ImportError:
    _ph = None

from backend.core.config import settings


def hash_password(password: str) -> str:
    """
    Hashes plaintext passwords using Argon2id (OWASP recommended),
    falling back to bcrypt work factor 12 if argon2 is not available.
    """
    if _ph:
        return _ph.hash(password)
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies passwords against either Argon2id ($argon2id$) or bcrypt ($2b$, $2a$) hashes.
    """
    if not plain_password or not hashed_password:
        return False

    if hashed_password.startswith("$argon2id") and _ph:
        try:
            return _ph.verify(hashed_password, plain_password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False

    # Bcrypt fallback
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generates a cryptographically signed JWT Access Token with unique JTI,
    subject, and expiration claims.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    jti = to_encode.get("jti") or str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "token_type": "access",
        "iat": int(datetime.utcnow().timestamp())
    })
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict) -> str:
    """
    Generates a cryptographically signed JWT Refresh Token with long expiration and unique JTI.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    jti = str(uuid.uuid4())
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "token_type": "refresh",
        "iat": int(datetime.utcnow().timestamp())
    })
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodes and validates a JWT token signature and expiration.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
