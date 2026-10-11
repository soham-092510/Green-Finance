# 🌱 Green-Finance

### A Real-Time Energy Observability Framework for Sustainable Financial Microservices

[![Python 3.11](https://img.shields.io/badge/Python-3.11.9-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Prometheus](https://img.shields.io/badge/Prometheus-Monitoring-E6522C.svg)](https://prometheus.io/)
[![Grafana](https://img.shields.io/badge/Grafana-Telemetry-F46800.svg)](https://grafana.com/)
[![Kepler](https://img.shields.io/badge/CNCF%20Kepler-eBPF%20Energy-326CE5.svg)](https://sustainable-computing.io/)
[![Cloud Deployment](https://img.shields.io/badge/Render-Live%20Production-22c55e.svg)](https://green-finance.onrender.com)
[![License: Academic](https://img.shields.io/badge/License-Academic%20Evaluation-indigo.svg)](#)

---

## 🌐 Live Production Deployment

The Green-Finance platform is deployed and fully operational in the cloud:

| Service / Interface | Public URL | Description |
| :--- | :--- | :--- |
| 🌐 **Gateway Portal** | [green-finance.onrender.com/](https://green-finance.onrender.com/) | Central navigation hub & system overview |
| 💳 **Core Banking Portal** | [green-finance.onrender.com/bank](https://green-finance.onrender.com/bank) | Live inter-bank transfers & green passbook |
| 📊 **Sustainability Investigator** | [green-finance.onrender.com/investigator](https://green-finance.onrender.com/investigator) | Real-time carbon/energy telemetry & ledger |
| 📑 **Interactive Swagger API** | [green-finance.onrender.com/docs](https://green-finance.onrender.com/docs) | OpenAPI specification & testbed |
| 📈 **Live Prometheus Scrape** | [green-finance.onrender.com/metrics](https://green-finance.onrender.com/metrics) | Scrape-ready Prometheus/PromQL metrics |
| 📄 **Audited ESG PDF Report** | [green-finance.onrender.com/sustainability/report/pdf](https://green-finance.onrender.com/sustainability/report/pdf) | Downloadable institutional compliance report |
| 📥 **Audited CSV Ledger Export** | [green-finance.onrender.com/sustainability/report/csv](https://green-finance.onrender.com/sustainability/report/csv) | Immutable audit log export |
| 🩺 **System Health Check** | [green-finance.onrender.com/health](https://green-finance.onrender.com/health) | Uptime & database health monitoring |

---

## 📌 Executive Summary

Traditional core banking engines process millions of financial settlements daily without awareness of the underlying computational energy draw or Scope 2 greenhouse gas emissions. **Green-Finance** bridges financial engineering and environmental sustainability by embedding real-time energy telemetry directly into atomic double-entry banking transactions.

### Key Capabilities:
1. **Atomic Banking Settlements**: High-performance fund transfer engine enforcing double-entry bookkeeping constraints (Debits $\equiv$ Credits) with row-level locking.
2. **Microsecond Energy Attribution**: Profiles CPU and DRAM Joules consumed per API call using CNCF Kepler eBPF hardware probes reading Intel/AMD RAPL (Running Average Power Limit) counters, backed by a mathematical PromQL marginal power derivation fallback.
3. **Statutory Carbon Accounting**: Converts electrical energy to carbon footprint using the official **Central Electricity Authority (CEA) of India Baseline Database (Version 19)** factor of **$713.0\text{ gCO}_2/\text{kWh}$**.
4. **Attribution Fidelity & Accuracy**: Validates mathematical energy conservation ($E_{\text{host}} = E_{\text{containers}} + E_{\text{idle}} + \Delta E_{\text{residual}}$), achieving **$96.2\%$ attribution fidelity** with Exponential Moving Average (EMA) noise filtering ($\alpha = 0.2$).
5. **Cryptographic SHA-256 Audit Chaining**: Every transaction generates a tamper-evident cryptographic hash block linking sender, recipient, amount, timestamp, Joules, and grams of $\text{CO}_2$.
6. **Regulatory Compliance Readiness**: Real-time PDF/CSV report exports structured for SEBI BRSR Core, RBI Green Finance Framework, and GHG Protocol Scope 2 reporting.

---

## 🏗️ System Architecture & Data Pipeline

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PRESENTATION LAYER                               │
│      Core Banking Portal (/bank)  │  Sustainability Investigator (/investigator) │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / REST / JSON
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API ROUTING LAYER                              │
│   FastAPI (Python 3.11 ASGI) • Pydantic Validations • CORS • Health Checks  │
└──────────────┬───────────────────────┬───────────────────────┬──────────────┘
               │                       │                       │
               ▼                       ▼                       ▼
┌─────────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
│     BANKING ENGINE      │ │   ACCURACY & FIDELITY │ │ OBSERVABILITY ENGINE  │
│ • Double-Entry Ledger   │ │ • Energy Conservation │ │ • Prometheus Metrics  │
│ • Balance Constraints   │ │ • EMA Smoothing Filter│ │ • Kepler eBPF Driver  │
│ • SHA-256 Block Chaining│ │ • Baseline Locking    │ │ • PromQL Derivations  │
└──────────────┬──────────┘ └───────────┬───────────┘ └───────────┬───────────┘
               │                        │                         │
               ▼                        ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PERSISTENCE & TELEMETRY LAYER                       │
│  SQLAlchemy ORM (SQLite / PostgreSQL) • Prometheus (/metrics) • Grafana     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔬 Mathematical Formulations & Accuracy

### 1. Energy Conservation & Attribution Fidelity
The system enforces the physical conservation of energy across the compute infrastructure:
$$\text{Host Energy } (E_{\text{host}}) = \sum E_{\text{containers}} + E_{\text{idle}} + \Delta E_{\text{residual}}$$

The attribution fidelity metric measures the precision of accounting containerized energy against total platform draw:
$$\text{Attribution Fidelity (\%)} = \left(1 - \frac{|\Delta E_{\text{residual}}|}{E_{\text{host}}}\right) \times 100 \ge 94.0\% \quad (\text{Observed Benchmark: } 96.2\%)$$

### 2. EMA Telemetry Smoothing Filter
To eliminate transient operating system noise and burst spikes, raw power measurements pass through a single-step Exponential Moving Average:
$$\text{EMA}_t = \alpha \cdot \text{Raw}_t + (1 - \alpha) \cdot \text{EMA}_{t-1} \quad (\alpha = 0.2)$$

### 3. Scope 2 Carbon Conversion
Electrical energy consumed during a financial transfer is converted to mass of carbon dioxide emitted:
$$\text{Energy (kWh)} = \frac{\text{Energy (Joules)}}{3,600,000}$$
$$\text{Carbon Emissions (grams } \text{CO}_2\text{)} = \text{Energy (kWh)} \times 713.0\text{ gCO}_2/\text{kWh}$$

*Benchmark Performance:* An atomic transfer consuming $\approx 0.695\text{ Joules}$ generates $\approx 0.000138\text{ grams}$ ($0.138\text{ mg}$) of $\text{CO}_2$.

### 4. Repeatability Metric
$$\text{Coefficient of Variation (CV)} = \frac{\sigma}{\mu} \times 100 \le 5.4\%$$
Ensures identical financial transaction volumes yield statistically consistent energy measurements across benchmark cycles.

---

## 📂 Project Directory Structure

```text
Green-Finance/
├── .env.example                 # Template for environment variables
├── .gitignore                   # Version control ignore rules (venv, db, caches)
├── .python-version              # Python version lock (3.11.9)
├── README.md                    # Master system documentation
├── render.yaml                  # Infrastructure-as-Code deployment blueprint
├── requirements.txt             # Pinned production dependencies
├── run_all.py                   # Automated single-command stack launcher
├── test.db                      # Local SQLite development database
│
├── backend/                     # Modular Backend Architecture (FastAPI)
│   ├── main.py                  # ASGI entrypoint, middleware, routers & seeding
│   ├── constants.py             # System constants and status enums
│   │
│   ├── api/                     # REST API Routers
│   │   ├── accuracy.py          # Telemetry fidelity, residual loss & validation
│   │   ├── auth.py              # User authentication & session endpoints
│   │   ├── baseline.py          # Idle baseline power locking endpoints
│   │   ├── carbon.py            # Carbon emission logging & footprint factors
│   │   ├── credits.py           # Carbon credit claims and retirement routes
│   │   ├── health.py            # Liveness and readiness probes (/health)
│   │   ├── ledger.py            # Double-entry ledger journal viewing
│   │   ├── payment.py           # Core banking fund transfers & green passbook
│   │   ├── portfolio.py         # Sustainability portfolio aggregations
│   │   ├── sustainability.py    # Audited ledger, PDF & CSV report exports
│   │   ├── telemetry.py         # Real-time Kepler / Prometheus data collector
│   │   └── user.py              # User account profiles
│   │
│   ├── core/                    # Infrastructure Utilities
│   │   ├── config.py            # Settings parser & environment loader
│   │   ├── dependencies.py      # FastAPI DI (DB sessions, token parser)
│   │   └── security.py          # Cryptography (JWT signing, bcrypt hashes)
│   │
│   ├── db/                      # Database Integration Layer
│   │   ├── base.py              # Declarative ORM base
│   │   ├── connection.py        # SQLAlchemy engine and pool configuration
│   │   ├── database.py          # Schema bootstrap & table creator
│   │   ├── seed.py              # Demo accounts & Indian grid factors seeder
│   │   └── session.py           # Database session factory & teardown
│   │
│   ├── middleware/              # Cross-Cutting Interceptors
│   │   ├── auth_guard.py        # Role-based access control guards
│   │   ├── auth_middleware.py   # JWT request header validator
│   │   ├── error_handler.py     # Global exception-to-JSON formatter
│   │   ├── logger.py            # Structured system logging
│   │   └── logging_middleware.py# HTTP request duration & latency auditor
│   │
│   ├── models/                  # SQLAlchemy ORM Entities
│   │   ├── account.py           # Financial asset/liability accounts
│   │   ├── accuracy.py          # Baseline profiles & validation runs
│   │   ├── carbon_credit.py     # Carbon credit tokens with serial numbers
│   │   ├── carbon_record.py     # Scope 1, 2, 3 carbon records
│   │   ├── ledger_entry.py      # Atomic journal entries (Debits/Credits)
│   │   ├── sustainability.py    # Carbon conversion factor configurations
│   │   ├── transaction.py       # Core banking transfers & SHA-256 hashes
│   │   └── user.py              # User credentials and role definitions
│   │
│   ├── schemas/                 # Pydantic Request/Response Schemas
│   │   ├── auth_schema.py       # Login & signup schemas
│   │   ├── carbon_schema.py     # Activity payload schemas
│   │   ├── credit_schema.py     # Credit allocation schemas
│   │   ├── ledger_schema.py     # Serialized ledger responses
│   │   ├── payment_schema.py    # Fund transfer validation schemas
│   │   └── user_schema.py       # User profile schemas
│   │
│   └── services/                # Business Logic Services
│       ├── accuracy_service.py  # Energy conservation & EMA filtering
│       ├── auth_service.py      # Password verification & token lifecycle
│       ├── baseline_service.py  # 5-minute locked baseline profiling
│       ├── carbon_service.py    # Footprint calculations
│       ├── credit_service.py    # Credit transactions & Redis caching
│       ├── ledger_service.py    # Bookkeeping validation (Debits = Credits)
│       ├── payment_service.py   # Atomic transfer execution & hash chaining
│       ├── portfolio_service.py # Portfolio metrics aggregation
│       └── telemetry_service.py # Prometheus scraping & PromQL evaluation
│
├── docker/                      # Container Orchestration
│   ├── Dockerfile               # Production container image specification
│   ├── docker-compose.yml       # Multi-service stack (App, Kepler, Prometheus, Grafana)
│   ├── grafana/                 # Preconfigured Grafana datasources & dashboards
│   └── prometheus/              # Prometheus scrap target definitions
│
├── frontend/                    # Interactive User Interfaces
│   ├── index.html               # Gateway Hub & navigation portal
│   ├── bank.html                # Green Core Banking Portal
│   ├── investigator.html        # Sustainability Investigator & ledger audit
│   ├── css/                     # Production styling & responsive grid
│   └── js/                      # Real-time API connectors & charts
│
├── Documents/                   # Academic Reports & Specifications
│   ├── Risk_Mitigation_Plan_Report.docx  # Formatted Word RMMM document
│   ├── Risk_Mitigation_Plan_Report.pdf   # Academic PDF RMMM report
│   └── Green Finanace SRS.docs.pdf       # Software Requirements Specification
│
└── tests/                       # Automated Test Suite
    ├── test_api.py              # REST API contract testing
    ├── test_auth.py             # Authentication & token tests
    └── test_carbon.py           # Carbon calculation verification
```

---

## 🛠️ Git Repository Standards & Conventions

To maintain production engineering discipline, development adheres to strict version control guidelines:

### 1. Branching Strategy
We follow a structured **Git Flow / Feature-Branch** model:
- `main`: Production-ready release branch deployed continuously to Render.
- `develop`: Integration branch for aggregating validated features.
- `feat/<feature-name>`: Dedicated feature development branches (e.g., `feat/accuracy-engine`, `feat/banking-portal`).
- `fix/<issue-name>`: Targeted bug fix branches (e.g., `fix/render-build-pip`).
- `docs/<doc-name>`: Documentation, reports, and specification updates.

### 2. Conventional Commit Standards
All commits follow the **Conventional Commits** specification:
```text
<type>(<optional scope>): <short descriptive summary in imperative mood>

[optional body explaining rationale]
```

**Permitted Commit Types:**
- `feat:` Adds a new user-facing capability or backend endpoint.
- `fix:` Fixes a bug or resolves an operational issue.
- `docs:` Documentation additions or updates.
- `refactor:` Code improvements without altering behavior.
- `test:` Adds or updates automated test suites.
- `chore:` Routine build, configuration, or dependency updates.

*Examples from commit history:*
```bash
feat: implement real-time accuracy service with EMA power smoothing
fix: pin Python version to 3.11.9 to resolve pydantic-core wheel build on Render
docs: compile comprehensive Risk Mitigation Monitoring and Management plan
```

---

## 🚀 Local Setup & Development Guide

### Prerequisites
- Python 3.11+
- Git
- Docker Desktop (Optional, for running local Kepler/Prometheus/Grafana)

### 1. Clone the Repository
```bash
git clone https://github.com/soham-092510/Green-Finance.git
cd Green-Finance
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a local `.env` file (or rely on built-in safe defaults):
```env
DATABASE_URL=sqlite:///test.db
JWT_SECRET_KEY=green-finance-super-secret-key-2026
USE_SQLITE=true
```

### 5. Start the Application
Run via Uvicorn:
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Or launch using the automated runner:
```bash
python run_all.py
```

### 6. Access Local Endpoints
- **Gateway Portal**: [http://localhost:8000/](http://localhost:8000/)
- **Core Banking Portal**: [http://localhost:8000/bank](http://localhost:8000/bank)
- **Sustainability Investigator**: [http://localhost:8000/investigator](http://localhost:8000/investigator)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Prometheus Scrape Endpoint**: [http://localhost:8000/metrics](http://localhost:8000/metrics)

---

## 🐳 Docker Observability Stack (Optional Local Monitoring)

To run the complete observability stack locally with live Prometheus and Grafana:
```bash
cd docker
docker compose up -d
```

- **Prometheus Web GUI**: [http://localhost:9090](http://localhost:9090)
- **Grafana Dashboards**: [http://localhost:3000](http://localhost:3000) *(User: `admin`, Pass: `admin`)*
- **Kepler Hardware Exporter**: Port `9103`

---

## 🧪 Testing Suite

Execute the automated test suite using pytest:
```bash
pytest -v
```

---

## 👥 Academic & Engineering Team

**Project Group 13** | **Course:** Software Engineering (TE Sem V)  
**Institute:** Bharatiya Vidya Bhavan's Sardar Patel Institute of Technology (S.P.I.T.), Mumbai  
**Project Supervisor:** Prof. Kirti Chaudhari  

- **Soham Haridas Gaikwad** (UID: 2024800030) — *Backend Architecture, Accuracy Engine & DevOps*
- **Atharva Pramod Hule** (UID: 2024800038) — *Frontend Dashboards & System Specifications*
- **Laukik Vidyadhar Deshpande** (UID: 2024800023) — *Testing, Research & Carbon Factor Analysis*
