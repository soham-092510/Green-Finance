# =====================================================================
# GREEN-FINANCE — CONFIG.PY (CENTRALIZED CONFIGURATION SETTINGS)
# Purpose: Validates environment variables, secrets, database URLs,
#          CORS origins, and session policies.
# =====================================================================

import os
import sys
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import model_validator


class Settings(BaseSettings):
    app_name: str = "green-finance"
    environment: str = "development"

    # Database
    database_url: str = "sqlite:///test.db"

    # External & Service Targets
    prometheus_url: str = "http://prometheus:9090"
    redis_url: str = "redis://localhost:6379/0"
    green_finance_2_url: str = "http://localhost:8000"
    port: int = 8000

    # Cryptographic & Session Configuration
    jwt_secret_key: str = "change_this_to_a_long_random_string_in_production_min32chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS Allowlist
    cors_origins: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "https://green-finance.onrender.com"
    ]

    # Operator / Bootstrap Configuration
    bootstrap_admin_token: Optional[str] = None

    # Rate Limiting Defaults
    rate_limit_auth_per_minute: int = 15
    rate_limit_transfers_per_minute: int = 30
    rate_limit_general_per_minute: int = 120

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        # In production, enforce non-default cryptographic secret key
        is_prod = self.environment.lower() in ("production", "prod")
        default_insecure_keys = {
            "green-finance-super-secret-key-2026",
            "change_this_to_a_long_random_string",
            "change_this_to_a_long_random_string_in_production_min32chars",
            "secret",
            "admin"
        }

        if is_prod:
            if self.jwt_secret_key in default_insecure_keys or len(self.jwt_secret_key) < 32:
                raise ValueError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: "
                    "JWT_SECRET_KEY must be configured with at least 32 high-entropy characters in production!"
                )

        # Database URL resolution
        if os.environ.get("USE_SQLITE", "").lower() in ("true", "1") or self.database_url.startswith("sqlite"):
            self.database_url = "sqlite:///test.db"
            return self

        if self.database_url.startswith("postgresql"):
            try:
                import psycopg2
                import urllib.parse
                url = urllib.parse.urlparse(self.database_url)
                conn = psycopg2.connect(
                    dbname=url.path.lstrip("/"),
                    user=url.username,
                    password=url.password,
                    host=url.hostname or "localhost",
                    port=url.port or 5432,
                    connect_timeout=2
                )
                conn.close()
            except Exception:
                # In development fallback to sqlite if postgres is unreachable
                if not is_prod:
                    self.database_url = "sqlite:///test.db"
                else:
                    raise ConnectionError("Cannot connect to production PostgreSQL database specified in DATABASE_URL!")
        return self

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
