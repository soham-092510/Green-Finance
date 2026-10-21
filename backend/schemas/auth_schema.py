# =====================================================================
# ECO MONITOR — AUTH_SCHEMA.PY
# Purpose: Defines Pydantic validation models for user authentication inputs
#          (registration, login) and token outputs.
# =====================================================================

# Import BaseModel, EmailStr, Field from pydantic
# WHY:
# - BaseModel: Base class to define Pydantic schemas
# - EmailStr: Automatically validates email format (requires pydantic[email] or standard format checks)
# - Field: Allows customizing validation rules (like string lengths)
from pydantic import BaseModel, EmailStr, Field

# Import Optional from typing
from typing import Optional, Dict, Any


class UserSummary(BaseModel):
    username: str
    role: str
    bank_id: Optional[str] = None
    name: Optional[str] = None
    is_boss_admin: Optional[bool] = False


class UserRegister(BaseModel):
    # Registration Input Validation Schema
    name: Optional[str] = Field(None, max_length=100, description="Full name of the user")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username identifier")
    email: EmailStr = Field(..., description="Valid email address for account notifications")
    password: str = Field(..., min_length=6, description="Plaintext password, minimum 6 characters")


class Token(BaseModel):
    # Authentication Token Output Schema
    access_token: str = Field(..., description="JWT Access Token string")
    token_type: str = Field("bearer", description="Token authentication scheme (usually Bearer)")
    refresh_token: Optional[str] = Field(None, description="Optional long-lived refresh token")
    jti: Optional[str] = None
    user: Optional[UserSummary] = None


class TokenData(BaseModel):
    # Token Payload Schema
    # WHY:
    # - Defines the structure of data stored inside decoded JWT payload claims
    
    username: Optional[str] = None
    role: Optional[str] = None
