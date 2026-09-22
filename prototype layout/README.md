# 🌱 Green-Finance | Eco-Monitor Prototype (Phase 2)

> **Real-Time Energy Observability & Carbon-per-Transaction Dashboard for Sustainable Financial Microservices**  
> Built for SPIT Software Engineering Mini-Project (TE Sem V) • Evaluated according to **IEEE 830 SRS Specification**.

---

## 📌 Table of Contents
1. [Quick Start: Commands to Run the Prototype](#-quick-start-commands-to-run-the-prototype)
2. [Complete Project Folder Structure & Architectural Rationale](#-complete-project-folder-structure--architectural-rationale)
3. [Phase 2 Objectives Implemented from SRS](#-phase-2-objectives-implemented-from-srs)
4. [Step-by-Step Evaluation & Presentation Guide](#-step-by-step-evaluation--presentation-guide)
5. [PromQL Formulas & Telemetry Architecture](#-promql-formulas--telemetry-architecture)
6. [Team Members](#-team-members)

---

## 🚀 Quick Start: Commands to Run the Prototype

The prototype layout is self-contained and runs on `localhost` without requiring any external cloud services or databases.

### 🔹 Method 1: Local HTTP Server (Recommended for Evaluation)

Open your terminal (PowerShell, Command Prompt, or Bash) in the project workspace:

#### Step 1: Ensure you are on the `layout` branch
```bash
git checkout layout
```

#### Step 2: Launch the local server on Port 8085
```bash
# Option A: From workspace root directory
python -m http.server 8085 --directory "prototype layout"

# Option B: By navigating into the prototype folder
cd "prototype layout"
python -m http.server 8085
```

> [!NOTE]
> **Why Port 8085?**  
> On Windows machines with Hyper-V or WSL enabled, port `8080` is often reserved by Windows NAT port exclusions (`WinError 10013`). Port `8085` provides 100% reliable local binding.

#### Step 3: Open in your browser
👉 **[http://localhost:8085](http://localhost:8085)**

---

### 🔹 Method 2: Direct Browser Launch (Zero Commands Required)
You can directly open the prototype file in any modern web browser (Google Chrome, Microsoft Edge, Mozilla Firefox):

- **Windows PowerShell**:
  ```powershell
  Start-Process "prototype layout/index.html"
  ```
- **macOS Terminal**:
  ```bash
  open "prototype layout/index.html"
  ```
- **Linux Terminal**:
  ```bash
  xdg-open "prototype layout/index.html"
  ```
- **File Explorer**: Simply navigate to the `prototype layout` folder and double-click `index.html`.

---

### 🔹 Method 3: Running the Full Backend Application (Optional)
If you wish to run the underlying FastAPI backend alongside the prototype:

```bash
# 1. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate      # On Windows
source venv/bin/activate     # On Linux / macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed demo accounts & ledger
python -m backend.db.seed

# 4. Start FastAPI server
uvicorn backend.main:app --reload --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Prometheus Scrape Endpoint: [http://localhost:8000/metrics](http://localhost:8000/metrics)

---

## 📂 Complete Project Folder Structure & Architectural Rationale

Here is the complete file and folder breakdown of the repository, explaining **why each component exists** and **how it fulfills the SRS requirements**:

```text
Green-Finance/
│
├── prototype layout/               # 🎨 Phase 2 Presentation & Prototype Layout
│   ├── index.html                  # Main SPA interface (White Theme, Grafana Panels, PromQL Console)
│   ├── styles.css                  # Modern white/emerald styling, responsive cards, CSS variables
│   ├── app.js                      # Application logic, PromQL engine, Chart.js graphs, simulated transfers
│   └── README.md                   # Execution guide, folder architecture, and evaluation walkthrough
│
├── Documents/                      # 📑 Academic & IEEE 830 Project Specifications
│   ├── Green Finanace SRS.docs.pdf # Official IEEE 830-1998 Software Requirements Specification
│   ├── EXP3_GreenFinance_ClassDiagram.pdf # OOAD UML Class Diagram & domain entity relationships
│   ├── DFD.pdf                     # Level 0 & Level 1 Data Flow Diagrams (Context & Functional)
│   ├── Interaction Diagram.pdf     # UML Sequence Diagram for money & credit transfer workflows
│   ├── UML Class Diagram.jpeg      # Visual blueprint of User, Account, Transaction, LedgerEntry models
│   └── project proposal template (2).pdf # Initial scope and problem definition
│
├── backend/                        # ⚙️ Python FastAPI Banking Microservice Engine
│   ├── main.py                     # Central switchboard, CORS setup, and Prometheus Instrumentation
│   ├── constants.py                # System-wide operational constants
│   ├── api/                        # REST Routing Controllers
│   │   ├── auth.py                 # RF01: JWT user signup, login & token issuing
│   │   ├── credits.py              # Carbon credit minting, transfers, and retirement
│   │   ├── ledger.py               # Double-entry audit ledger query endpoints
│   │   ├── telemetry.py            # Real-time Kepler metrics scraping & auto-logging routes
│   │   ├── portfolio.py            # Unified sustainability portfolio metrics
│   │   ├── user.py                 # Profile details and role management
│   │   └── health.py               # Container health check endpoint (/health)
│   ├── core/                       # Core Security & Configuration
│   │   ├── config.py               # Pydantic environment parser (.env loader)
│   │   ├── dependencies.py         # FastAPI dependency injection (get_db, get_current_user)
│   │   └── security.py             # Bcrypt hashing & PyJWT token cryptography
│   ├── db/                         # Database Access & Migrations
│   │   ├── base.py                 # Shared SQLAlchemy DeclarativeBase
│   │   ├── connection.py           # Database engine connection pool
│   │   ├── database.py             # Startup table creation routines
│   │   ├── session.py              # Context-managed SessionLocal generator
│   │   └── seed.py                 # Preloaded demo users, accounts, and ledger rows
│   ├── models/                     # SQLAlchemy ORM Database Entities
│   │   ├── user.py                 # Stores user credentials, bank IDs, and roles
│   │   ├── account.py              # Financial & carbon accounts with non-negative SQL constraints
│   │   ├── transaction.py          # Atomic transaction headers
│   │   ├── ledger_entry.py         # Double-entry lines (Debits & Credits)
│   │   ├── carbon_credit.py        # Carbon credits with serial numbers and vintages
│   │   ├── carbon_record.py        # Logged Scope 1, 2, and 3 activities
│   │   └── credit.py               # Credit retirement and certificate records
│   ├── schemas/                    # Pydantic Data Validation Models
│   │   ├── auth_schema.py          # Login & registration payload validation
│   │   ├── credit_schema.py        # Credit minting & transfer request schemas
│   │   ├── ledger_schema.py        # Serialized double-entry ledger outputs
│   │   ├── carbon_schema.py        # Emission activity form schemas
│   │   └── user_schema.py          # User profile modification schemas
│   ├── services/                   # Business Logic Layer
│   │   ├── auth_service.py         # Password verification & session tokens
│   │   ├── credit_service.py       # Inventory management & Redis caching
│   │   ├── ledger_service.py       # Double-entry engine enforcing Debits = Credits
│   │   ├── telemetry_service.py    # PromQL query client parsing Prometheus metrics
│   │   ├── carbon_service.py       # Emission calculation from standard factors
│   │   └── portfolio_service.py    # Aggregated user sustainability summaries
│   └── middleware/                 # Cross-Cutting Interceptors
│       ├── logging_middleware.py   # Latency measurement & access auditor
│       ├── auth_guard.py           # Role-Based Access Control (RBAC)
│       └── error_handler.py        # Unified JSON error interceptor
│
├── docker/                         # 🐳 Container Orchestration Layer
│   ├── Dockerfile                  # Python 3.11-slim container build recipe
│   ├── docker-compose.yml          # Multi-container orchestration (API, Kepler, Prometheus, Grafana)
│   ├── prometheus/
│   │   └── prometheus.yml          # Prometheus scrape configuration (15s interval)
│   └── grafana/
│       └── datasources/
│           └── datasource.yml      # Pre-provisioned Prometheus data source
│
├── frontend/                       # 🌐 Synchronized Web Portal
│   ├── index.html                  # Synchronized Phase 2 layout
│   ├── styles.css                  # Synchronized CSS styling
│   └── app.js                      # Synchronized frontend logic
│
├── tests/                          # 🧪 Automated Test Suite
│   ├── test_api.py                 # REST endpoint validation tests
│   ├── test_auth.py                # Authentication & JWT security tests
│   └── test_carbon.py              # Carbon calculation & ledger checks
│
├── .env                            # Environment credentials (JWT secrets, ports, DB URLs)
├── .gitignore                      # Excludes cache, venv, test databases, and OS files
└── requirements.txt                # Production dependencies list
```

---

## 🎯 Phase 2 Objectives Implemented from SRS

| SRS Requirement ID | Requirement Name | How It Is Implemented in This Prototype |
| :--- | :--- | :--- |
| **RF01** | **User / Service Authentication** | Simulated bank customer session logged in with Bank ID `HDFC9999` and JWT credentials. Includes interactive `POST /auth/login` tester. |
| **RF02** | **Simulated Payment Processing** | Interactive transfer module allowing user control over transfer amounts (₹ INR), protocol (IMPS, NEFT, RTGS, UPI), and recipient Bank IDs (`MAH123`, `IDF892`, `SBIN456`, `AXIS777`). |
| **RF03** | **Kernel-Level Energy Telemetry** | Attributing active container power in Joules/Watts (`payment-service` vs `auth-service`) using Kepler eBPF counter logic. |
| **RF04** | **Metrics Scraping & Storage** | Simulated Prometheus scraper polling every 15 seconds, storing time-series counters (`http_requests_total`, `kepler_container_joules_total`). |
| **RF05** | **Carbon-per-Transaction Calculation** | Live PromQL calculation joining Kepler energy telemetry with transaction rate: $(\text{Energy} \times \text{Factor}) \div \text{Tx Count}$, outputting $\text{g CO}_2/\text{tx}$. |
| **RF06** | **Real-Time Dashboard Visualization** | 4-panel embedded Grafana view: (1) Carbon-per-Tx over time, (2) Power allocation by service, (3) Request throughput & latency, (4) Service Hotspot Ranking table with ESG ratings. |
| **RF07** | **High Emission Spikes Alerting** | Configurable threshold alerts. Exceeding the safety limit (default: 12.0 g CO₂ / tx) triggers an immediate warning banner and Grafana alert. |
| **RF08** | **Containerized Deployment Status** | Topbar status pills showing live connectivity of Prometheus (:9090), Grafana (:3000), and Kepler (:9103). |
| **RF09** | **Historical Time-Range Queries** | Time range selector on Grafana dashboard supporting `5m`, `15m`, `1h`, and `24h` query windows. |
| **RF10** | **Configuration Management** | Configurable regional carbon intensity factor (default: `0.38 kg CO₂/kWh` Indian National Grid Average) and alert threshold controls. |

---

## 🖥️ Step-by-Step Evaluation & Presentation Guide

When demonstrating this prototype to professors, evaluators, or stakeholders, follow this narrative:

1. **Step 1: Open the Overview Dashboard**  
   - Show the 4 KPI cards: **Carbon-per-Transaction (8.42 g CO₂)**, **Container Energy (118.6 W)**, **Transaction Volume (1,429)**, and **Cumulative Footprint (12.03 kg)**.
   - Point out the **real-time live line charts** showing carbon intensity and service power allocation.

2. **Step 2: Simulate a Bank Money Transfer**  
   - In the Quick Transfer card, select Recipient Bank ID (e.g. `MAH123 — Bank of Maharashtra`).
   - Enter an amount (e.g. `₹15,000`) and click **"Execute Simulated Transaction & Measure Carbon"**.
   - Watch the transaction appear instantly in the **Live Stream** with exact Joules measured and grams of $\text{CO}_2$ produced!
   - Observe the live KPI counter increment and the chart update smoothly.

3. **Step 3: Demonstrate High Emission Alerting (RF07)**  
   - Enter a large amount (e.g. `₹150,000`) to simulate high compute/row-locking load.
   - Watch the system detect that carbon emission exceeded the threshold and raise the **RF07 High Carbon Emission Alert banner**!

4. **Step 4: Explore the Grafana Observability Dashboard**  
   - Click **"Grafana Observability"** in the sidebar.
   - Walk through the **4 Panels**: Carbon-per-Tx, Container Energy Rate, Throughput, and the **Service Energy Hotspot Ranking Table** (showing `payment-service` at 68.4% energy share).
   - Change the **Time Range** filter (`5m`, `15m`, `1h`) to demonstrate historical query capability (RF09).

5. **Step 5: Execute PromQL Queries in the PromQL Console**  
   - Click **"PromQL Console"** in the sidebar.
   - Select the pre-configured query:  
     `sum(rate(kepler_container_joules_total[1m])) * 0.38 / sum(rate(http_requests_total[1m]))`
   - Click **"Execute PromQL"** to show the live evaluated time-series curve and the raw Prometheus vector JSON response.

6. **Step 6: Review the Double-Entry Ledger**  
   - Click **"Double-Entry Ledger"** in the sidebar.
   - Show that every transfer creates balanced accounting lines:  
     `DR: HDFC9999 (-₹12,500) = CR: MAH123 (+₹12,500)` while logging exact energy Joules and carbon weights.
   - Click **"Export CSV"** to demonstrate audit compliance.

---

## 📐 PromQL Formulas & Telemetry Architecture

The system uses the following PromQL derivation to join physical hardware telemetry with API request throughput:

$$\text{Carbon-per-Transaction (g CO}_2/\text{tx)} = \frac{\sum \text{rate}(\text{kepler\_container\_joules\_total}[1m]) \times F_{\text{grid}}}{\sum \text{rate}(\text{http\_requests\_total}[1m])}$$

Where:
- $\text{kepler\_container\_joules\_total}$: Cumulative energy (Joules) attributed to the container by Kepler via eBPF probes.
- $\text{http\_requests\_total}$: Counter incremented on every processed transaction.
- $F_{\text{grid}}$: Configurable regional grid emissions factor ($0.38 \text{ kg CO}_2/\text{kWh} = 0.0001055 \text{ g CO}_2/\text{Joule}$).

---

## 👥 Team Members (Sardar Patel Institute of Technology)

- **Soham Haridas Gaikwad** (UID: `2024800030`) — Backend (FastAPI Services), Monitoring Stack (Prometheus/Grafana/Kepler), DevOps (Docker Compose).
- **Atharva Pramod Hule** (UID: `2024800038`) — Frontend Dashboard Development, System Documentation, Integration Support.
- **Laukik Vidyadhar Deshpande** (UID: `2024800023`) — Testing, Carbon-Factor Research, and Report Generation.
