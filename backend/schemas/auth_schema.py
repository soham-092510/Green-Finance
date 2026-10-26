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
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator
from typing import Optional, Dict, Any
import re


class UserSummary(BaseModel):
    username: str
    role: str
    bank_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    is_boss_admin: Optional[bool] = False


class UserRegister(BaseModel):
    # Enforce mass-assignment protection: silently ignore any client-supplied role/privileged fields
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., min_length=2, max_length=100, description="Full legal name of the customer")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username identifier")
    email: EmailStr = Field(..., description="Valid email address for account notifications")
    password: str = Field(..., min_length=8, description="Password, minimum 8 characters with letters and numbers")
    confirm_password: Optional[str] = Field(None, description="Password confirmation")

    @model_validator(mode="after")
    def validate_registration_payload(self) -> "UserRegister":
        # 1. Normalize username and validate format
        uname = self.username.strip()
        if not re.match(r"^[a-zA-Z0-9_]+$", uname):
            raise ValueError("Username may only contain letters, numbers, and underscores")
        self.username = uname

        # 2. Normalize email
        self.email = self.email.strip().lower()

        # 3. Password complexity policy: min 8 chars, at least one letter and at least one digit
        pwd = self.password
        if len(pwd) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Za-z]", pwd):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", pwd):
            raise ValueError("Password must contain at least one numeric digit")

        # 4. Check confirm_password if supplied
        if self.confirm_password is not None and self.confirm_password != pwd:
            raise ValueError("Passwords do not match")

        return self


class LoginJsonRequest(BaseModel):
    username: str = Field(..., description="Username or email address")
    password: str = Field(..., description="Password")


class Token(BaseModel):
    access_token: str = Field(..., description="JWT Access Token string")
    token_type: str = Field("bearer", description="Token authentication scheme")
    refresh_token: Optional[str] = Field(None, description="Optional refresh token")
    jti: Optional[str] = None
    csrf_token: Optional[str] = None
    user: Optional[UserSummary] = None


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

