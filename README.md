# 🌱 Green Finance System

A scalable, highly modular, and production-ready **Carbon Footprint Monitoring & Carbon Credit Management Platform** built using Python (FastAPI), SQLAlchemy ORM, Redis caching, and an observability-first design featuring Kepler energy telemetry, Prometheus, and Grafana dashboards.

---

> 🚀 **Phase 2 Presentation & Prototype Layout Quick Start**:
> - **Branch**: `layout`
> - **Run Local Server**: `python -m http.server 8085 --directory "prototype layout"`
> - **Access UI**: 👉 **[http://localhost:8085](http://localhost:8085)**
> - Full prototype guide, commands, and architecture: [prototype layout/README.md](prototype%20layout/README.md)

---

## 📌 Table of Contents
1. [Project Overview](#-project-overview)
2. [System Architecture & Data Flows](#-system-architecture--data-flows)
3. [Newly Updated Directory Structure](#-newly-updated-directory-structure)
4. [File-by-File Breakdown: Why Each File Exists](#-file-by-file-breakdown-why-each-file-exists)
5. [Observability Stack Setup](#-observability-stack-setup)
6. [Tech Stack](#-tech-stack)
7. [Local Run & Development Guide](#-local-run--development-guide)
8. [Docker & Production Deployment](#-docker--production-deployment)
9. [Testing Framework](#-testing-framework)

---

## 📌 Project Overview

**Green Finance** is a professional sustainability ecosystem designed to let organizations log carbon emissions, verify offset actions, manage financial carbon ledgers, and monitor physical energy consumption of computing servers. The platform features:

*   🌍 **Carbon Footprint Tracking**: Accurate Scope 1 (Direct Fuel), Scope 2 (Indirect Electricity/Energy), and Scope 3 (Supply Chain/Agriculture) carbon calculations.
*   💳 **Carbon Credit Lifecycle**: Claiming, transferring, and retiring carbon credits verified against environmental conservation projects.
*   📒 **Double-Entry Ledger Engine**: Balance sheet protection ensuring financial auditability. Every allocation registers debits and credits atomically with row locking.
*   📈 **Real-Time Infrastructure Telemetry**: Direct integration with Kepler to scrap CPU, RAM, and motherboard energy footprints and convert them to CO2 weights in real-time.
*   🖥️ **Interactive Dashboard UI**: Dynamic frontend interface displaying real-time graphs, history, and calculator utilities.

---

## 🏗️ System Architecture & Data Flows

The application divides responsibilities into distinct software engineering layers:

```text
┌─────────────────┐
│  Lightweight UI │
│   (Frontend)    │
└────────┬────────┘
         │
         │ HTTP Requests (JSON)
         ▼
┌────────────────────────────────────────────────────────┐
│                      API LAYER                         │
│  Validates input data schemas & handles HTTP routes    │
└────────┬──────────────────────────────────────┬────────┘
         │                                      │
         │ Invokes Services                     │ Invokes Telemetry Service
         ▼                                      ▼
┌─────────────────────────────────┐    ┌─────────────────────────────────┐
│         SERVICE LAYER           │    │    TELEMETRY OBSERVABILITY      │
│  Auth, Carbon, Credit, Ledger   │    │  Runs PromQL against Prometheus │
└────────┬────────────────────────┘    └────────┬────────────────────────┘
         │                                      │
         │ Runs transactions & queries          │ Reads scraped energy stats
         ▼                                      ▼
┌─────────────────────────────────┐    ┌─────────────────────────────────┐
│         DATABASE LAYER          │    │      PROMETHEUS & KEPLER        │
│    SQLite Engine & ORM Models   │    │ Scrapes CPU & process energy    │
└─────────────────────────────────┘    └─────────────────────────────────┘
```

### 🔐 1. Authentication Flow
*   The visitor submits credentials via the UI.
*   [auth.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/auth.py) captures the parameters and redirects to [auth_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/auth_service.py).
*   Password hashes are verified using standard cryptographic checks in [security.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/core/security.py) against [user.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/models/user.py).
*   If valid, a secure JWT session token is returned.

### 🌍 2. Carbon Emission Logging
*   The logged-in user inputs activity details (e.g., flight miles, electricity consumed).
*   [carbon.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/carbon.py) validates the payload through Pydantic schemas in [carbon_schema.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/schemas/carbon_schema.py).
*   [carbon_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/carbon_service.py) computes carbon footprint by querying standard emission coefficients (`EmissionFactor`).
*   It creates a [carbon_record.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/models/carbon_record.py) entry and adjusts the user's `carbon_liability` account balance.

### 💳 3. Credit Transaction & Offset Ledger
*   A user claims credits or retires them to offset liabilities.
*   [credit_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/credit_service.py) checks balances in Redis. On cache miss, it locks database rows in [account.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/models/account.py).
*   It calls [ledger_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/ledger_service.py) to post balancing journal lines: **Debit Liability** and **Credit Asset**.
*   If accounting constraints check out (e.g., positive balance limits), the transaction is committed, and Redis caches are invalidated.

### 📊 4. Observability & Infrastructure Telemetry
*   The Kepler agent reports active node/container power draw metrics to Prometheus.
*   [telemetry.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/telemetry.py) receives user dashboard request and delegates to [telemetry_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/telemetry_service.py).
*   The service queries Prometheus via HTTP, pulls raw Watt/Joule measurements, translates power to carbon footprint (using an emissions intensity multiplier of `0.38 kg CO2/kWh`), and responds with structured data.
*   Additionally, the auto-log scheduler posts telemetry-derived carbon footprints into the DB & Ledger logs automatically.

---

## 📂 Newly Updated Directory Structure

The structure represents the integration of telemetry capabilities (Kepler energy telemetry services, API routes, Prometheus targets, and Grafana data sources):

```bash
eco-monitor/
│   .env                         # Database and JWT credentials config file
│   .gitignore                   # Ignored files (virtual environments, test databases, caches)
│   README.md                    # System layout and design explanation
│   requirements.txt             # Python packages setup list
│   test.db                      # Local development SQLite database file
│
├── backend/                     # Backend Source Code (FastAPI application structure)
│   │   constants.py             # Empty placeholders for shared status limits
│   │   main.py                  # Entrypoint, startup initialization, and routing configurations
│   │
│   ├── api/                     # Controller / Router endpoints
│   │       auth.py              # Signup, login, and token generation paths
│   │       carbon.py            # Custom carbon footprint logging endpoints
│   │       credits.py           # Carbon credit claims and assets transfer paths
│   │       health.py            # Docker/Kubernetes container health status endpoint (/health)
│   │       ledger.py            # Double-entry ledger audit records viewing routes
│   │       portfolio.py         # Unified metrics summaries for user dashboard
│   │       telemetry.py         # Real-time Kepler metrics scraping and auto-logging routes
│   │       user.py              # User details modification and fetch paths
│   │
│   ├── core/                    # Security components and settings engines
│   │       config.py            # Settings parser and default SQLite database locator
│   │       dependencies.py      # Dependency injection providers (DB connection, JWT parser)
│   │       security.py          # Cryptography (JWT signing and bcrypt password checks)
│   │
│   ├── db/                      # Database integration and migrations scripts
│   │       base.py              # Common database metadata mapping structure
│   │       connection.py        # Connects to database engines using configuration strings
│   │       database.py          # Executes initialization tables creation on system startup
│   │       seed.py              # Sets up default emission rates and creates demo profiles
│   │       session.py           # Session factories and generator cleanup rules
│   │
│   ├── middleware/              # Cross-cutting intermediate layers
│   │       auth_guard.py        # Role check restrictions
│   │       auth_middleware.py   # Authenticates requests by reading token headers
│   │       error_handler.py     # Converts system errors into structured HTTP outputs
│   │       logger.py            # Logger formats configurations
│   │       logging_middleware.py# Records request processing times
│   │
│   ├── models/                  # Database Entities (SQLAlchemy ORM tables)
│   │       account.py           # Tracks asset/liability balances
│   │       carbon_credit.py     # Stores credit assets vintage and serial numbers
│   │       carbon_record.py     # Stores logged Scope 1, 2, or 3 activities
│   │       credit.py            # Tracks credit claims and transfers
│   │       ledger_entry.py      # Ledger records (Debits & Credits)
│   │       transaction.py       # Tracks asset transactions
│   │       user.py              # Stores credentials and roles (ADMIN, INVESTOR)
│   │
│   ├── schemas/                 # Data serializations and constraints (Pydantic validations)
│   │       auth_schema.py       # Validation schemas for logins and signups
│   │       carbon_schema.py     # Validates incoming emission forms data
│   │       credit_schema.py     # Validates transaction inputs for credit operations
│   │       ledger_schema.py     # Serializes double-entry bookkeeping lines
│   │       user_schema.py       # Validates update forms for user accounts
│   │
│   └── services/                # Backend Business Logic services
│           auth_service.py      # Controls logins verification and session keys
│           carbon_service.py    # Computes carbon metrics and updates accounts
│           credit_service.py    # Retires credits and manages Redis caching
│           ledger_service.py    # Bookkeeping engine checking Debits = Credits
│           portfolio_service.py # Compiles portfolio statistics summaries
│           telemetry_service.py # Fetches energy statistics from Prometheus
│
├── docker/                      # Multi-service configuration settings
│   │   Dockerfile              # Builds the backend environment image
│   │   docker-compose.yml       # Orchestrates FastAPI app, Kepler, Prometheus, Grafana
│   │
│   ├── grafana/
│   │   └── datasources/
│   │           datasource.yml   # Pre-allocates Prometheus as the default datasource
│   │
│   └── prometheus/
│           prometheus.yml       # Setups Prometheus scraping interval targets
│
├── docs/                        # Specifications and design plans
│       api-endpoints.md         # Reference list of API endpoints
│       architecture.md          # Architectural blueprints and engineering rationale
│
├── frontend/                    # Web visual panel
│       app.js                   # Handles dashboard UI requests
│       index.html               # Web interface layout
│       styles.css               # Styling definitions
│
└── tests/                       # Test suite templates
        test_api.py              # Templates for endpoint tests
        test_auth.py             # Templates for auth tests
        test_carbon.py           # Templates for carbon logic tests
```

---

## 🛠️ File-by-File Breakdown: Why Each File Exists

Here is a detailed explanation of the role, core logic, and connection mapping of each file in the workspace:

### ⚙️ Root Configuration Files

#### 1. [.env](file:///c:/Users/HP/Downloads/Projects/eco-monitor/.env)
*   **Importance**: Decouples application configuration from codebase environments. It stores database connection links, JWT secrets, and port allocations.
*   **Logic**: A dictionary structure parsed by Pydantic's environment loading module.
*   **Connections**: Read on startup by [config.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/core/config.py) and [docker-compose.yml](file:///c:/Users/HP/Downloads/Projects/eco-monitor/docker/docker-compose.yml).

#### 2. [.gitignore](file:///c:/Users/HP/Downloads/Projects/eco-monitor/.gitignore)
*   **Importance**: Prevents local config (like `.env`), Python virtual environments (`venv`), DB files (`test.db`), and cache directories (`__pycache__`) from being committed to the repo.
*   **Logic**: Standard glob matching filters ignored paths.
*   **Connections**: Checked automatically by Git.

#### 3. [requirements.txt](file:///c:/Users/HP/Downloads/Projects/eco-monitor/requirements.txt)
*   **Importance**: Contains the list of Python dependencies required to run the project.
*   **Logic**: Flat text file mapping library requirements to version ranges.
*   **Connections**: Installed via `pip` and used by [Dockerfile](file:///c:/Users/HP/Downloads/Projects/eco-monitor/docker/Dockerfile) to build container images.

#### 4. [test.db](file:///c:/Users/HP/Downloads/Projects/eco-monitor/test.db)
*   **Importance**: Local SQLite database generated during initialization. In development settings, PostgreSQL requests are automatically redirected here.
*   **Logic**: Standard binary database file operated via SQL queries.
*   **Connections**: Managed by the SQLAlchemy engines defined in [connection.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/db/connection.py).

---

### 🕸️ API Routing Layer (`backend/api/`)
Exposes REST endpoints, parses path parameters, and delegates operations to the service layer.

#### 5. [auth.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/auth.py)
*   **Importance**: Exposes routes for user login and signup.
*   **Logic**: Uses FastAPI's `APIRouter`. Maps payloads to [auth_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/auth_service.py).
*   **Connections**: Imported and mounted in [main.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/main.py).

#### 6. [carbon.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/carbon.py)
*   **Importance**: Exposes carbon footprint tracking endpoints.
*   **Logic**: Requires authentication. Converts inputs to [carbon_schema.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/schemas/carbon_schema.py) types and forwards them to [carbon_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/carbon_service.py).
*   **Connections**: Depends on user validations defined in [dependencies.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/core/dependencies.py).

#### 7. [credits.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/credits.py)
*   **Importance**: Exposes endpoints for managing carbon credit balances and transactions.
*   **Logic**: Handles credit claims and transfers. Interacts with [credit_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/credit_service.py).
*   **Connections**: Part of the central router stack in [main.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/main.py).

#### 8. [health.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/health.py)
*   **Importance**: Standard health check endpoint `/health`.
*   **Logic**: Returns a basic status JSON (`{"status": "healthy"}`).
*   **Connections**: Used by container orchestrators to monitor server health.

#### 9. [ledger.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/ledger.py)
*   **Importance**: Exposes endpoints for audit trails and ledger transactions.
*   **Logic**: Interacts with [ledger_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/ledger_service.py) to fetch transaction data.
*   **Connections**: Mounted in [main.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/main.py).

#### 10. [portfolio.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/portfolio.py)
*   **Importance**: Exposes endpoints for user portfolio aggregation.
*   **Logic**: Pulls data from [portfolio_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/portfolio_service.py).
*   **Connections**: Feeds data to the charts in [app.js](file:///c:/Users/HP/Downloads/Projects/eco-monitor/frontend/app.js).

#### 11. [telemetry.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/telemetry.py) *(New)*
*   **Importance**: Exposes energy telemetry metrics endpoints.
*   **Logic**: 
    *   `GET /realtime` returns active energy measurements.
    *   `GET /historical` returns cumulative consumption stats.
    *   `POST /log` saves calculated carbon values into database tables.
*   **Connections**: Delegates execution to [telemetry_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/telemetry_service.py).

#### 12. [user.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/user.py)
*   **Importance**: Exposes endpoints for fetching and editing user profiles.
*   **Logic**: Integrates user profile updates.
*   **Connections**: Connects database models in [user.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/models/user.py) to API actions.

#### 13. [constants.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/constants.py)
*   **Importance**: Holds static values and defaults.
*   **Logic**: Python constants file.

#### 14. [main.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/main.py)
*   **Importance**: The application entry point and central routing registry.
*   **Logic**: Initializes the FastAPI instance, configures CORS settings, attaches middleware logging layers, hooks up Prometheus instrumentation, and triggers database table seeding on startup.
*   **Connections**: Booted by the Uvicorn application server.

---

### 🛡️ Application Core Utilities (`backend/core/`)
Implements configuration management, authentication guards, and security primitives.

#### 15. [config.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/core/config.py)
*   **Importance**: Reads configurations from the environmental variables.
*   **Logic**: Automatically replaces PostgreSQL strings with a local SQLite configuration (`sqlite:///test.db`) during development.
*   **Connections**: Read by [connection.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/db/connection.py) to instantiate database connections.

#### 16. [dependencies.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/core/dependencies.py)
*   **Importance**: Implements dependency injection for database sessions and JWT authentication.
*   **Logic**: Provides database sessions (`get_db`) and parses HTTP Authorization headers (`get_current_user`).
*   **Connections**: Imported as route dependencies throughout `backend/api/`.

#### 17. [security.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/core/security.py)
*   **Importance**: Handles password cryptography and token signing.
*   **Logic**: Uses bcrypt for secure password hashing and PyJWT for signing access tokens.
*   **Connections**: Used by [auth_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/auth_service.py) during login and registration.

---

### 🛢️ Database Layer (`backend/db/`)
Manages connection engines, table migrations, and development seed data.

#### 18. [base.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/db/base.py)
*   **Importance**: Shared declarative base for SQLAlchemy ORM models.
*   **Logic**: Collects table definitions into a unified metadata structure.
*   **Connections**: Inherited by all database models.

#### 19. [connection.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/db/connection.py)
*   **Importance**: Configures the database connection pool.
*   **Logic**: Instantiates the SQLAlchemy connection engine.
*   **Connections**: Connects database sessions to [test.db](file:///c:/Users/HP/Downloads/Projects/eco-monitor/test.db).

#### 20. [database.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/db/database.py)
*   **Importance**: Handles database initialization on application startup.
*   **Logic**: Runs table creation queries if tables do not exist and triggers database seeding.
*   **Connections**: Invoked by the startup handler in [main.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/main.py).

#### 21. [seed.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/db/seed.py)
*   **Importance**: Seeds the database with default Scope conversion factors and demo data.
*   **Logic**: Creates demo users, accounts, and sample ledger transactions.
*   **Connections**: Executed on startup by [database.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/db/database.py).

#### 22. [session.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/db/session.py)
*   **Importance**: Manages active database sessions.
*   **Logic**: Creates database session instances (`SessionLocal`) and handles cleanup.
*   **Connections**: Injected via [dependencies.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/core/dependencies.py) into API routers.

---

### 🚦 Middleware & Request Interceptors (`backend/middleware/`)
Processes HTTP requests and responses to apply cross-cutting logic.

#### 23. [auth_guard.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/middleware/auth_guard.py)
*   **Importance**: Restricts access to routes based on user roles.
*   **Logic**: Validates request contexts against allowed roles.
*   **Connections**: Applied as dependencies on restricted API routes.

#### 24. [auth_middleware.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/middleware/auth_middleware.py)
*   **Importance**: Intercepts requests to validate JWT token signatures.
*   **Logic**: Extracts and decodes token payloads, attaching the user identity to the request state.
*   **Connections**: Mounted in [main.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/main.py) to authenticate incoming requests.

#### 25. [error_handler.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/middleware/error_handler.py)
*   **Importance**: Converts internal exceptions into structured JSON responses.
*   **Logic**: Catches validation errors and system exceptions, mapping them to appropriate HTTP status codes.
*   **Connections**: Registered in the application instance in [main.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/main.py).

#### 26. [logger.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/middleware/logger.py)
*   **Importance**: Configures application logging.
*   **Logic**: Standardizes log output formatting for both development and production.
*   **Connections**: Used across services and controllers to write status messages.

#### 27. [logging_middleware.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/middleware/logging_middleware.py)
*   **Importance**: Audits API request performance.
*   **Logic**: Logs request methods, paths, processing durations, and return status codes.
*   **Connections**: Configured as middleware in [main.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/main.py).

---

### 💾 Database Models (`backend/models/`)
Defines the database schema as Python classes mapped to SQL tables.

#### 28. [user.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/models/user.py)
*   **Importance**: Represents user profiles and credentials.
*   **Logic**: Defines tables storing usernames, email addresses, hashed passwords, roles, and timestamps.
*   **Connections**: Referenced by accounts, carbon records, and credit transactions.

#### 29. [account.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/models/account.py)
*   **Importance**: Models user accounts for asset and liability balances.
*   **Logic**: Includes database constraints to prevent balances from dropping below 0.
*   **Connections**: Updated by [ledger_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/ledger_service.py).

#### 30. [carbon_record.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/models/carbon_record.py)
*   **Importance**: Represents calculated carbon emissions records.
*   **Logic**: Tracks activity types (e.g. transportation, energy, procurement), metric values, calculated CO2 quantities, and timestamps.
*   **Connections**: Written by [carbon_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/carbon_service.py).

#### 31. [carbon_credit.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/models/carbon_credit.py)
*   **Importance**: Represents carbon credit asset tokens.
*   **Logic**: Stores serial numbers, vintage years, offset sources, ownership status, and quantities.
*   **Connections**: Queried and updated by [credit_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/credit_service.py).

#### 32. [credit.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/models/credit.py)
*   **Importance**: Logs credit retirements and allocations.
*   **Logic**: Maps credit retirement operations.
*   **Connections**: Used during credit offset calculations.

#### 33. [ledger_entry.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/models/ledger_entry.py)
*   **Importance**: Represents double-entry ledger lines.
*   **Logic**: Tracks journal entries (Debits & Credits) associated with specific transaction IDs and account IDs.
*   **Connections**: Inserted atomically by [ledger_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/ledger_service.py).

#### 34. [transaction.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/models/transaction.py)
*   **Importance**: Represents transaction records.
*   **Logic**: Stores transaction metadata, descriptions, and audit timestamps.
*   **Connections**: Parent record for multiple [ledger_entry.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/models/ledger_entry.py) items.

---

### 📝 Validation & Serialization Layer (`backend/schemas/`)
Defines Pydantic models to validate API requests and structure responses.

#### 35. [auth_schema.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/schemas/auth_schema.py)
*   **Importance**: Validates authentication credentials payload structures.
*   **Logic**: Validates login data models and token response fields.
*   **Connections**: Injected as filters in [auth.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/auth.py).

#### 36. [carbon_schema.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/schemas/carbon_schema.py)
*   **Importance**: Validates carbon activity payload structures.
*   **Logic**: Validates fields like activity types, numeric measurements, and optional description notes.
*   **Connections**: Used by [carbon.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/carbon.py) to validate input data.

#### 37. [credit_schema.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/schemas/credit_schema.py)
*   **Importance**: Structures payloads for credit claim and transfer operations.
*   **Logic**: Validates target accounts, token amounts, and serial numbers.
*   **Connections**: Used in [credits.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/credits.py).

#### 38. [ledger_schema.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/schemas/ledger_schema.py)
*   **Importance**: Formats ledger transaction entries for responses.
*   **Logic**: Serializes database models to return lists of ledger entries.
*   **Connections**: Injected in [ledger.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/ledger.py).

#### 39. [user_schema.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/schemas/user_schema.py)
*   **Importance**: Validates user details modification payloads.
*   **Logic**: Validates emails, user names, and role definitions.
*   **Connections**: Filters input data in [user.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/user.py).

---

### 🧠 Core Business Logic Services (`backend/services/`)
Implements business rules, ledger accounting calculations, and data processing.

#### 40. [auth_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/auth_service.py)
*   **Importance**: Coordinates authentication workflows.
*   **Logic**: Verifies user accounts, checks password hashes, and issues access/refresh tokens.
*   **Connections**: Invoked by the endpoints router in [auth.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/auth.py).

#### 41. [carbon_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/carbon_service.py)
*   **Importance**: Handles emissions records calculations and liability updates.
*   **Logic**: Looks up emission factors, calculates CO2 equivalents, writes carbon records to the database, and updates user liability accounts.
*   **Connections**: Called by [carbon.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/carbon.py) and [telemetry_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/telemetry_service.py).

#### 42. [credit_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/credit_service.py)
*   **Importance**: Manages carbon credit inventories and retirements.
*   **Logic**: 
    *   Retrieves user carbon credit assets.
    *   Integrates Redis caching to reduce database read loads.
    *   Posts balancing entries to the ledger for credit transactions.
*   **Connections**: Interacts with Redis, the database, and [ledger_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/ledger_service.py).

#### 43. [ledger_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/ledger_service.py)
*   **Importance**: The double-entry bookkeeping engine.
*   **Logic**: 
    *   Enforces the bookkeeping equation: Debits must equal Credits.
    *   Uses row locking (`with_for_update()`) to prevent race conditions during updates.
    *   Validates balances against database constraint rules.
*   **Connections**: Invoked by other services (such as credits and emissions) to post financial entries.

#### 44. [portfolio_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/portfolio_service.py)
*   **Importance**: Aggregates user portfolio data.
*   **Logic**: Gathers database metrics, liability balances, and credit details into a unified summary.
*   **Connections**: Injected into [portfolio.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/portfolio.py) routes to serve the UI.

#### 45. [telemetry_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/telemetry_service.py) *(New)*
*   **Importance**: Connects to Prometheus to retrieve server energy telemetry.
*   **Logic**: 
    *   Fetches Kepler node and container energy metrics via HTTP API using PromQL.
    *   Converts Joules/Watts into kilowatt-hours (kWh).
    *   Calculates carbon emissions (`Power (Watts) * 0.38 kg/kWh / 1000 = emissions (kg CO2)`).
    *   Saves telemetry-derived carbon records to the database using [carbon_service.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/services/carbon_service.py).
*   **Connections**: Called by the endpoints router in [telemetry.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/backend/api/telemetry.py).

---

### 🐳 Deployment Configuration (`docker/`)
Coordinates containerized deployments of the application stack.

#### 46. [Dockerfile](file:///c:/Users/HP/Downloads/Projects/eco-monitor/docker/Dockerfile)
*   **Importance**: Defines the Docker image for the FastAPI application.
*   **Logic**: Sets up a lightweight `python:3.11-slim` environment, installs dependencies from `requirements.txt`, copies source code, and configures the startup command using Uvicorn.
*   **Connections**: Built by Docker and executed by `docker-compose.yml`.

#### 47. [docker-compose.yml](file:///c:/Users/HP/Downloads/Projects/eco-monitor/docker/docker-compose.yml)
*   **Importance**: Orchestrates the multi-container stack.
*   **Logic**: Configures and links the FastAPI application, Kepler energy telemetry agent, Prometheus server, and Grafana.
*   **Connections**: Deploys the service stack using the settings in `.env`.

#### 48. [datasource.yml](file:///c:/Users/HP/Downloads/Projects/eco-monitor/docker/grafana/datasources/datasource.yml) *(New)*
*   **Importance**: Configures Grafana data sources automatically on startup.
*   **Logic**: Declares Prometheus as the default data source.
*   **Connections**: Read by Grafana containers on deployment.

#### 49. [prometheus.yml](file:///c:/Users/HP/Downloads/Projects/eco-monitor/docker/prometheus/prometheus.yml) *(New)*
*   **Importance**: Configures Prometheus metrics scraping targets.
*   **Logic**: Defines metrics scraping intervals and scrap target endpoints (such as Kepler and application services).
*   **Connections**: Loaded by Prometheus containers to scrape target metrics.

---

### 🖥️ User Interface Layer (`frontend/`)
Provides a dashboard interface for user interaction.

#### 50. [index.html](file:///c:/Users/HP/Downloads/Projects/eco-monitor/frontend/index.html)
*   **Importance**: The layout of the web portal.
*   **Logic**: Basic page structure with placeholders for metrics, logs, inputs, and charts.
*   **Connections**: Renders styles from [styles.css](file:///c:/Users/HP/Downloads/Projects/eco-monitor/frontend/styles.css) and registers scripts in [app.js](file:///c:/Users/HP/Downloads/Projects/eco-monitor/frontend/app.js).

#### 51. [styles.css](file:///c:/Users/HP/Downloads/Projects/eco-monitor/frontend/styles.css)
*   **Importance**: Defines layout presentation, gradients, and responsiveness.
*   **Logic**: Flat CSS design rules.
*   **Connections**: Loaded by [index.html](file:///c:/Users/HP/Downloads/Projects/eco-monitor/frontend/index.html).

#### 52. [app.js](file:///c:/Users/HP/Downloads/Projects/eco-monitor/frontend/app.js)
*   **Importance**: Integrates with the API, makes requests, and renders data onto charts.
*   **Logic**: Handles login submittals, queries portfolio data and telemetry metrics, and updates dashboard charts.
*   **Connections**: Interacts with the backend via fetch requests.

---

### 🧪 Automated Testing Suite (`tests/`)
Contains test templates ready for validation checks.

#### 53. [test_api.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/tests/test_api.py)
*   **Importance**: Verifies API routing and responses.
*   **Logic**: Exposes basic test templates.
*   **Connections**: Executed via Pytest.

#### 54. [test_auth.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/tests/test_auth.py)
*   **Importance**: Verifies authentication functionality.
*   **Logic**: Exposes basic test templates.
*   **Connections**: Executed via Pytest.

#### 55. [test_carbon.py](file:///c:/Users/HP/Downloads/Projects/eco-monitor/tests/test_carbon.py)
*   **Importance**: Verifies carbon calculations and ledger updates.
*   **Logic**: Exposes basic test templates.
*   **Connections**: Executed via Pytest.

---

## 📈 Observability Stack Setup

The platform uses Prometheus to collect energy telemetry from Kepler, which is then fetched by the telemetry service to calculate carbon emissions.

```text
[ Kepler Power Telemetry ]  ──────>  [ Prometheus Scraping ]  ──────>  [ Telemetry Service API ]  ──────>  [ Database Records ]
  (CPU/Motherboard Joules)             (Time-Series Database)            (PromQL Calculations)             (Emissions Logging)
```

1.  **Kepler** uses eBPF programs to measure CPU and hardware power draw in real-time.
2.  **Prometheus** scrapes Kepler metrics on port `9103` every 10 seconds.
3.  **FastAPI** calls Prometheus using PromQL to retrieve energy consumption metrics, converts Joules to kWh, and calculates carbon emissions using a standard multiplier (`0.38 kg CO2/kWh`).

---

## ⚙️ Tech Stack

*   **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11)
*   **Database ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) (SQLite local database)
*   **Caching Layer**: [Redis](https://redis.io/) (used to store carbon credit assets data)
*   **Observability Stack**: [Kepler](https://sustainable-computing.io/) (Energy metrics), [Prometheus](https://prometheus.io/) (Time-series data), [Grafana](https://grafana.com/) (Dashboards)
*   **Frontend UI**: HTML5, CSS3, JavaScript (using fetch and Chart.js integration)

---

## 🚀 Local Run & Development Guide

### 1️⃣ Setup Virtual Environment & Dependencies
Navigate to the root directory and create a virtual environment:
```bash
# Create python virtual environment
python -m venv venv

# Activate the environment (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Initialize Database & Seed Demo Data
Run the database seed script to populate default emission factors, users, accounts, and ledger records:
```bash
python -m backend.db.seed
```

### 3️⃣ Launch the Backend Application
Start the FastAPI server:
```bash
uvicorn backend.main:app --reload --port 8000
```
Open http://127.0.0.1:8000/docs in your browser to view the interactive Swagger API documentation.

### 4️⃣ Launch the Frontend UI
Because the frontend consists of static assets, you can serve it using Python's built-in HTTP server:
```bash
# Navigate to the frontend folder
cd frontend

# Start HTTP server
python -m http.server 8080
```
Open http://localhost:8080 in your browser to access the dashboard. Log in with the preloaded credentials:
*   **Username**: `demo_user`
*   **Password**: `password123`

---

## 🐳 Docker & Production Deployment

To run the complete stack including the application, database fallback, Kepler telemetry, Prometheus scraping, and Grafana dashboards, use Docker Compose:

```bash
# Navigate to the docker directory
cd docker

# Start the stack
docker-compose up --build
```

The stack deploys the following services:
*   **FastAPI API Server**: http://localhost:8000
*   **Kepler Energy Telemetry Agent**: Port 9103 (provides raw hardware energy metrics)
*   **Prometheus Engine**: http://localhost:9090 (collects and queries metrics)
*   **Grafana Dashboards**: http://localhost:3000 (preloaded with Prometheus datasource. Admin credentials: `admin` / `admin`)

---

## 🧪 Testing Framework

Tests are run using pytest from the workspace root:

```bash
# Run the test suite
pytest
```
The test files in `tests/` are templates that can be extended to cover custom API, Auth, and Carbon validation tests.
