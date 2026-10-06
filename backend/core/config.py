# =====================================================================
# ECO MONITOR — CONFIG.PY (CONFIGURATION SETTINGS)
# =====================================================================
# Purpose/Existence of this file:
# This file acts as the "Brain of Settings" for the entire project.
# Imagine a physical device where you have knobs, sliders, and dials. This file
# is where we name and validate all those knobs (like the database URL, secrets, etc.)
# so that the rest of the application can simply read them from here instead of 
# searching all over the place. It loads variables from a hidden file called ".env".
# =====================================================================

# 🔹 Import BaseSettings
# BaseSettings is a pre-built tool from the "pydantic-settings" library.
# It acts like a smart template that automatically looks at your computer's 
# environment variables (or a secret text file called ".env") and fills in the values for us.
from pydantic_settings import BaseSettings

# 🔹 Import model_validator
# model_validator is a validation tool from the "pydantic" library.
# It acts like a security guard that double-checks the final values of our settings
# after they are loaded, making sure everything is correct and making adjustments if needed.
from pydantic import model_validator


# 🔹 Define the Settings class
# A "class" is like a blueprints sketch. Here, we outline the name and type of every single 
# configuration parameter our app needs to run.
class Settings(BaseSettings):

    # app_name (Text/String type)
    # The name of our application. If not set, it defaults to "green-finance".
    app_name: str = "green-finance"

    # environment (Text/String type)
    # Tells the code if it is running in "development" mode (like on a programmer's laptop)
    # or "production" mode (active for real users). Defaults to "development".
    environment: str = "development"

    # database_url (Text/String type)
    # The address where the database lives.
    # Note: We do not give it a default value here, which means the app will refuse 
    # to start unless this parameter is defined in the ".env" file (for safety).
    database_url: str

    # prometheus_url (Text/String type)
    # The address of the Prometheus server that collects telemetry from Kepler.
    # Defaults to the docker service hostname "http://prometheus:9090".
    prometheus_url: str = "http://prometheus:9090"

    # redis_url (Text/String type)
    # The address of the Redis cache server used to speed up operations.
    redis_url: str

    # jwt_secret_key (Text/String type)
    # A long, highly secret random string used to encrypt/sign digital session cards (tokens).
    # It must be provided in the ".env" file.
    jwt_secret_key: str

    # jwt_algorithm (Text/String type)
    # The encryption math formula used to secure tokens. Defaults to "HS256".
    jwt_algorithm: str = "HS256"

    # access_token_expire_minutes (Integer/Whole Number type)
    # How long a login session token remains valid (in minutes) before expiring. Defaults to 30.
    access_token_expire_minutes: int = 30

    # refresh_token_expire_days (Integer/Whole Number type)
    # How long a refresh session token remains valid (in days). Defaults to 7.
    refresh_token_expire_days: int = 7

    green_finance_2_url: str = "http://localhost:8000"
    port: int = 8001

    @model_validator(mode="after")
    def resolve_database_url(self) -> "Settings":
        import os
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
                    connect_timeout=1
                )
                conn.close()
            except Exception:
                self.database_url = "sqlite:///test.db"
        return self


    # 🔹 Config class
    # This is a special internal configuration block that tells Pydantic how to load variables.
    class Config:

        # Specifies that Pydantic should search for a file named ".env" to read configuration values from.
        env_file = ".env"

        # Makes configuration variable names case-insensitive (e.g. DATABASE_URL and database_url are treated the same).
        case_sensitive = False


# 🔹 Create the Settings Instance
# Here, we actually build the settings object based on our blueprint above.
# This variable "settings" is what other files will import to read the configuration.
settings = Settings()


# =====================================================================
# 🕸️ CONNECTIONS & WORKFLOW (How this file communicates with others):
# =====================================================================
# 1. READS FROM:
#    - ".env" file (located in the project root): Loads raw configuration values.
#
# 2. READ BY (CONNECTIONS):
#    - [connection.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/db/connection.py):
#      Reads `settings.database_url` to establish the connection to the database.
#    - [telemetry_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/telemetry_service.py):
#      Reads `settings.prometheus_url` to know where to execute PromQL telemetry queries.
#    - [security.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/core/security.py):
#      Reads keys and algorithm settings to issue and decode JWT login tokens.
#    - [main.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/main.py):
#      Reads `settings.app_name` to customize the FastAPI app title.
# =====================================================================