# Green Finance — Comprehensive Security & Architectural Audit
**Document Version:** 1.0.0  
**Audit Date:** October 21, 2026  
**Audited Repository:** `Green-Finance` (Branch: `security-hardening-rbac-control-center`)  
**Target Architecture:** FastAPI 0.115.0, SQLAlchemy 2.0.35, Pydantic v2, SQLite / PostgreSQL, CNCF Kepler, Prometheus, Grafana, Render Cloud  
**Standard Reference:** OWASP ASVS 5.0.0 (Level 2 Target), OWASP API Security Top 10 (2023), OWASP Secure Coding Practices

---

## 1. Executive Summary

A comprehensive architectural and security audit of the **Green Finance** repository was performed prior to implementing security hardening, hierarchical Role-Based Access Control (RBAC), and operational monitoring.

Green Finance has evolved from a simple prototype into an integrated fintech system combining:
1. Double-entry financial bookkeeping for banking payments.
2. Computational energy attribution using CNCF Kepler (eBPF/RAPL) with simulation fallback.
3. Carbon accounting using CEA India Grid emission factors (713 gCO2/kWh).
4. An investigator workbench and automated ESG compliance reporting (PDF/CSV).
5. Prometheus TSDB metrics and Grafana observability.

**Key Audit Conclusion:**  
While the core double-entry accounting formulas and energy attribution math are conceptually sound, the application currently operates **in a largely open, unauthenticated state with critical vulnerabilities**. 

### Empirical Finding Statistics
- **Total API Routes Identified:** 72
- **Routes Requiring Authentication:** 18 (25.0%)
- **Routes Open Without Authentication:** 54 (75.0%)
- **Critical Severity Vulnerabilities:** 4
- **High Severity Vulnerabilities:** 4
- **Medium Severity Vulnerabilities:** 4
- **Low Severity Vulnerabilities:** 3
- **Baseline Test Suite Status:** 7 tests passed (0.96s) in `tests/test_accuracy_engine.py`; 0 security or authorization tests existed prior to this audit (`test_api.py`, `test_auth.py`, `test_carbon.py` were empty 0-byte files).

---

## 2. Architecture & Trust Boundaries

### 2.1 Component Architecture
```
                         [ Public Internet / Untrusted Clients ]
                                      |
                      (HTTP / WebSocket / REST Calls)
                                      |
                                      v
  +-------------------------------------------------------------------------+
  | Application Perimeter (FastAPI Server on Port 8000)                     |
  |                                                                         |
  |  +---------------------+  +--------------------+  +------------------+  |
  |  | Static File Handler |  | Banking Controllers|  | Sustainability  |  |
  |  | (/bank, /grafana,   |  | (/payment/transfer,|  | (/sustainability |  |
  |  |  /investigator)     |  |  /payment/accounts)|  |  /kpis, /ledger) |  |
  |  +---------------------+  +--------------------+  +------------------+  |
  |             |                       |                       |           |
  |  +-------------------------------------------------------------------+  |
  |  | Internal Service Layer: payment_service, accuracy_service,        |  |
  |  |                         telemetry_service, ledger_service         |  |
  |  +-------------------------------------------------------------------+  |
  |             |                                   |                       |
  +-------------|-----------------------------------|-----------------------+
                |                                   |
                v                                   v
  +---------------------------+       +------------------------------------+
  | Primary Data Store        |       | Observability & Telemetry Subsystem|
  | SQLite (local / Render)   |       | - Prometheus TSDB (:9090)          |
  | PostgreSQL (target prod)  |       | - Kepler eBPF Daemon (:9103)       |
  | Tables: users, accounts,  |       | - Grafana Server (:3000)           |
  | transactions, ledger_...  |       | - Internal PromQL Proxy            |
  +---------------------------+       +------------------------------------+
```

### 2.2 Trust Boundaries
1. **External Boundary (Internet $\rightarrow$ FastAPI):** All incoming HTTP requests. Currently lacks rate limiting, security headers, strict CORS, and authentication on 75% of endpoints.
2. **Fintech Transaction Boundary:** Money movement (`/payment/transfer`). Currently unauthenticated; any caller can specify any arbitrary source bank account and transfer funds.
3. **Ledger Immutability Boundary:** Double-entry journal entries (`transactions` and `ledger_entries`). Committed in two separate steps, creating partial-failure race windows.
4. **Telemetry & Attribution Boundary:** Energy measurements and carbon computations. PromQL proxy allows arbitrary unvalidated queries to internal Prometheus.
5. **Static File Serving Boundary:** File paths served from disk. Vulnerable to path traversal outside root directory.

---

## 3. Comprehensive Endpoint Inventory

The 72 routes exposed by `backend/main.py:app` were completely mapped:

| HTTP Method | Path | Controller / Purpose | Current Protection | Sensitive Data / Action | Expected Role | Baseline Test Coverage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET, HEAD` | `/openapi.json` | OpenAPI Schema | None | Internal API structures | Public | Untested |
| `GET, HEAD` | `/docs`, `/redoc` | Swagger / ReDoc UI | None | API exploration | Public / Internal | Untested |
| `GET` | `/health` | System health check | None | Service metadata | Public | Untested |
| `POST` | `/auth/register` | Customer registration | None | User creation, assigns wallet | Public | Untested |
| `POST` | `/auth/login` | OAuth2 Password Login | None | Issues JWT access/refresh | Public | Untested |
| `GET` | `/user/me` | Fetch logged-in profile | `get_current_user` | User PII, email, bank_id | Customer/Admin | Untested |
| `GET` | `/carbon` | List user carbon records | `get_current_user` | User emissions history | Customer | Untested |
| `POST` | `/carbon` | Log carbon footprint | `get_current_user` | Writes emission liabilities | Customer | Untested |
| `GET` | `/credits` | List user carbon credits | `get_current_user` | User credit asset balances | Customer | Untested |
| `POST` | `/credits/mint` | Mint new carbon credits | `get_current_user` | **Creates assets out of thin air** | Admin / Registry | Untested |
| `POST` | `/credits/transfer` | Send credits to user | `get_current_user` | Credit transfer | Customer | Untested |
| `POST` | `/credits/retire` | Burn carbon credits | `get_current_user` | Credit retirement | Customer | Untested |
| `GET` | `/ledger` | List user ledger entries | `get_current_user` | User journal entries | Customer | Untested |
| `GET` | `/ledger/audit/{id}`| Audit SHA-256 verification | `get_current_user` | **Any transaction's audit log** | Customer / Auditor | Untested |
| `GET` | `/portfolio` | User carbon portfolio | `get_current_user` | Portfolio breakdown | Customer | Untested |
| `POST` | `/portfolio/rebalance` | Rebalance credit holdings| `get_current_user` | Portfolio optimization | Customer | Untested |
| `GET` | `/telemetry/realtime` | Live power & emissions | `get_current_user` | Host & container power | Investigator/Ops | Untested |
| `GET` | `/telemetry/historical`| Cumulative energy usage | `get_current_user` | Energy aggregates | Investigator/Ops | Untested |
| `POST` | `/telemetry/log` | Auto-log Kepler emissions | `get_current_user` | Debits environmental liability| Investigator/Ops | Untested |
| `GET` | `/telemetry/mode` | Query OBSERVED/SIMULATED | None | System telemetry mode | Public | Untested |
| `POST`| `/telemetry/calculate-carbon`| Energy to CO2 calc | `get_current_user` | Carbon math calculation | Customer/Inv. | Untested |
| `GET` | `/telemetry/promql` | Arbitrary PromQL query | `get_current_user` | **Raw Prometheus metrics access**| Ops / Super Admin | Untested |
| `POST`| `/baseline/start` | Start idle calibration | **None** | Initiates CPU baseline sample | Admin / Ops | Tested (Unit) |
| `GET` | `/baseline/status` | Read calibration progress| **None** | Background power metrics | Investigator/Ops | Tested (Unit) |
| `POST`| `/baseline/lock` | Lock baseline profile | **None** | Freezes baseline profile | Admin / Ops | Tested (Unit) |
| `GET` | `/baseline/current`| Current locked baseline | **None** | Locked power mean/std/CV | Investigator/Ops | Tested (Unit) |
| `GET` | `/baseline/drift` | Check baseline drift | **None** | Drift alert state | Investigator/Ops | Tested (Unit) |
| `GET` | `/accuracy/current`| Energy conservation check| **None** | Host, container, idle residual| Investigator/Ops | Tested (Unit) |
| `POST`| `/accuracy/run-validation`| Execute validation cycle | **None** | Triggers 500 tx validation run| Admin / Ops | Tested (Unit) |
| `GET` | `/accuracy/report` | Validation report digest | **None** | Formal signed validation doc | Auditor / Ops | Tested (Unit) |
| `POST`| `/payment/transfer` | Double-entry money transfer | **None** | **Direct money transfer** | Customer (own acct)| Tested (Unit) |
| `POST`| `/payment/stimulate`| 10-user workload burst | **None** | Spawns batch transactions | Admin / Dev | Untested |
| `POST`| `/payment/benchmark`| Standardized batch CV | **None** | Runs 50 identical transfers | Admin / Dev | Tested (Unit) |
| `GET` | `/payment/accounts` | List accounts & balances | **None** | **All user cash balances** | Customer / Admin | Untested |
| `GET` | `/payment/transactions`| Recent audited txns | **None** | **Full system payment logs** | Customer / Inv. | Untested |
| `GET` | `/payment/transactions/{id}`| Individual txn audit log | **None** | Specific transaction trace | Customer / Inv. | Untested |
| `GET` | `/sustainability/kpis`| Executive ESG indicators | **None** | Aggregated banking ESG KPIs | Executive / Auditor| Untested |
| `GET` | `/sustainability/ledger`| Granular carbon ledger | **None** | Every transaction's carbon data| Investigator / Ops | Untested |
| `GET` | `/sustainability/efficiency`| Microservice energy share| **None** | Microservice computational load| Investigator / Ops | Untested |
| `GET` | `/sustainability/goals`| List ESG targets | **None** | Institution sustainability targets| Customer / Admin | Untested |
| `POST`| `/sustainability/goals`| Create/update ESG target | **None** | Modifies sustainability targets| Boss Admin / Admin | Untested |
| `GET` | `/sustainability/alerts`| Basel Risk alerts | **None** | System sustainability alerts | Investigator / Admin| Untested |
| `POST`| `/sustainability/alerts/{id}/resolve`| Resolve active alert | **None** | Changes alert status | Investigator / Admin| Untested |
| `GET` | `/sustainability/recommendations`| AI/rule-based advice| **None** | Architectural recommendations | Investigator / Admin| Untested |
| `POST`| `/sustainability/scenario`| What-if modeling | **None** | Computational simulation | Investigator / Admin| Untested |
| `GET` | `/sustainability/carbon-factors`| List grid factors | **None** | CEA Grid factor registry | Public / Auditor | Untested |
| `POST`| `/sustainability/carbon-factors`| Register new grid factor| **None** | Appends new grid carbon factor| Boss Admin | Untested |
| `POST`| `/sustainability/carbon-factors/{id}/activate`| Set active grid factor| **None**| Changes active carbon formula | Boss Admin | Untested |
| `GET` | `/sustainability/report/csv`| Export CSV audit ledger | **None** | **Full financial & carbon CSV**| Auditor / Inv. | Untested |
| `GET` | `/sustainability/report/pdf`| Export PDF compliance | **None** | **Full audit PDF generation** | Auditor / Inv. | Untested |
| `GET` | `/sustainability/connected-users`| Real-time user telemetry| **None**| **Real names, bank IDs, volume**| Investigator / Admin| Untested |
| `POST`| `/connection/ingest-trace`| External trace ingestion | **None** | Ingests telemetry trace | Internal service | Untested |
| `GET` | `/metrics` | Prometheus metrics scrape | **None** | Application throughput, counts | Ops (Prometheus) | Untested |
| `GET` | `/`, `/bank`, `/investigator`, `/grafana` | Static HTML frontends | None | Serves HTML dashboards | Public / Authed UI | Untested |
| `GET` | `/shared/{file_path:path}`| Serves shared files | **None** | **Arbitrary File Read (Path Traversal)**| Static asset | Tested (Exploit) |

---

## 4. Prioritized Vulnerability Findings

### Finding CRIT-01: Path Traversal / Arbitrary File Read in Static Asset Router
- **Severity:** CRITICAL (CVSS 9.8)
- **CWE:** CWE-22 (Improper Limitation of a Pathname to a Restricted Directory)
- **OWASP:** A01:2021 — Broken Access Control
- **Location:** `backend/main.py:187-196` (`serve_shared_file`)
- **Code Evidence:**
  ```python
  @app.get("/shared/{file_path:path}", include_in_schema=False)
  def serve_shared_file(file_path: str):
      fpath = os.path.join(shared_dir, file_path)
      if os.path.isfile(fpath):
          return FileResponse(fpath)
      fpath_root = os.path.join(frontend_dir, file_path)
      if os.path.isfile(fpath_root):
          return FileResponse(fpath_root)
      return FileResponse(os.path.join(shared_dir, "styles.css"))
  ```
- **Empirical Proof:** Executing `GET /shared/..%2F..%2F.env` successfully returned HTTP 200 and leaked the entire `.env` file (334 bytes) containing database passwords, Redis URLs, and JWT secret keys.
- **Impact:** Complete exposure of all environment variables, signing secrets, and database credentials to any unauthenticated caller on the public internet.
- **Remediation:** Replace loose `os.path.join` endpoints with FastAPI's `StaticFiles` mounted with strict root boundaries, or explicitly verify `os.path.commonpath([base_dir, resolved_path]) == base_dir`.

---

### Finding CRIT-02: Completely Unauthenticated Core Banking Transfer & Arbitrary Account Draining
- **Severity:** CRITICAL (CVSS 9.8)
- **CWE:** CWE-306 (Missing Authentication for Critical Function), CWE-862 (Missing Authorization)
- **OWASP API Security:** API1:2023 — Broken Object Level Authorization, API2:2023 — Broken Authentication
- **Location:** `backend/api/payment.py:30-53` (`transfer_funds`), `backend/services/payment_service.py:101-220`
- **Code Evidence:**
  ```python
  @router.post("/transfer", response_model=BankTransferResponse, status_code=status.HTTP_200_OK)
  def transfer_funds(
      payload: BankTransferRequest,
      db: Session = Depends(get_db)  # <-- NO AUTHENTICATION DEPENDENCY!
  ):
      return payment_service.execute_bank_transfer(
          db=db,
          source_bank_id=payload.source_account,  # <-- TRUSTS CLIENT-SUPPLIED SOURCE!
          dest_bank_id=payload.destination_account,
          amount=payload.amount,
          ...
      )
  ```
- **Empirical Proof:** Executing an anonymous HTTP POST request to `/payment/transfer` with `{"source_account": "HDFC9999", "destination_account": "MAH123", "amount": 100.0}` completed with HTTP 200, successfully debiting ₹100 from `HDFC9999` and crediting `MAH123`.
- **Impact:** Direct financial theft. Any anonymous actor can drain any bank account simply by guessing or knowing the bank ID (which is publicly leaked by `/payment/accounts`).
- **Remediation:** Enforce `current_user: User = Depends(get_current_user)`. Strictly assert that the authenticated user owns `source_account` or possesses an explicit administrative transfer permission. Never accept source account ownership blindly from client JSON.

---

### Finding CRIT-03: Systemic Exposure of Banking, Customer, and ESG Data (No Auth on 54 Endpoints)
- **Severity:** CRITICAL (CVSS 9.1)
- **CWE:** CWE-306 (Missing Authentication)
- **OWASP API Security:** API2:2023 — Broken Authentication, API3:2023 — Broken Object Property Level Authorization
- **Location:** `backend/api/payment.py`, `backend/api/sustainability.py`, `backend/api/baseline.py`, `backend/api/accuracy.py`
- **Code Evidence:**
  - `GET /payment/accounts`: Dumps all bank accounts, user full names, usernames, and live cash balances with zero authentication.
  - `GET /payment/transactions`: Dumps all financial transaction history and audit hashes with zero authentication.
  - `GET /sustainability/connected-users`: Dumps all user names, bank IDs, total amounts transferred, and online status with zero authentication.
  - `GET /sustainability/report/csv` & `/report/pdf`: Generates and exports full historical transaction and carbon compliance documents with zero authentication.
  - `POST /sustainability/carbon-factors`: Allows anonymous callers to inject arbitrary grid factors and activate them, corrupting all carbon accounting.
- **Impact:** Massive privacy violation, full exposure of banking customers, and unauthorized alteration of regulatory compliance data.
- **Remediation:** Establish a default-deny policy. All routes under `/payment`, `/sustainability`, `/accuracy`, and `/baseline` must require verified JWT tokens and explicit RBAC roles.

---

### Finding CRIT-04: Hardcoded Production Secrets & Ephemeral Database Configuration
- **Severity:** CRITICAL (CVSS 9.1)
- **CWE:** CWE-798 (Use of Hard-coded Credentials), CWE-312 (Cleartext Storage of Sensitive Information)
- **OWASP:** A02:2021 — Cryptographic Failures, A05:2021 — Security Misconfiguration
- **Location:** `render.yaml:12-13`, `backend/core/config.py:49`, `backend/db/seed.py:119, 193`, `docker/docker-compose.yml:70`
- **Code Evidence:**
  - `render.yaml`:
    ```yaml
    - key: JWT_SECRET_KEY
      value: green-finance-super-secret-key-2026
    - key: DATABASE_URL
      value: sqlite:///test.db
    - key: USE_SQLITE
      value: "true"
    ```
  - `backend/core/config.py:49`:
    ```python
    jwt_secret_key: str = "green-finance-super-secret-key-2026"
    ```
  - `backend/db/seed.py`: All demo users seeded with `"password123"` and banks with `"bankpassword123"`.
  - `docker/docker-compose.yml`: Grafana configured with `GF_SECURITY_ADMIN_PASSWORD: admin`.
- **Impact:** Anyone with read access to the GitHub repository can forge valid JWT tokens for any user or administrator. Furthermore, deploying SQLite on Render web services without persistent disks causes the entire financial ledger to be erased on every service restart or deploy.
- **Remediation:** Remove hardcoded secrets. Enforce mandatory runtime validation: if `JWT_SECRET_KEY` is missing, equal to the default placeholder, or shorter than 32 characters in production, the server must fail to start.

---

### Finding HIGH-01: Wildcard CORS with Credentials Allowed
- **Severity:** HIGH (CVSS 8.2)
- **CWE:** CWE-942 (Permissive Cross-domain Policy with Untrusted Domains)
- **OWASP:** A05:2021 — Security Misconfiguration
- **Location:** `backend/main.py:79-85`
- **Code Evidence:**
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- **Impact:** Misconfigured CORS policy. When combined with credentials, browsers reject `allow_origins=["*"]`, or if origins are reflected dynamically, malicious third-party websites can read responses from authenticated endpoints.
- **Remediation:** Restrict `allow_origins` to an explicit, configured allowlist (e.g., local development origins and the production Render domain). Never allow wildcard origins with credentials.

---

### Finding HIGH-02: Missing Security Headers & Clickjacking Protection
- **Severity:** HIGH (CVSS 7.5)
- **CWE:** CWE-1021 (Improper Restriction of Rendered UI Layers or Frames)
- **OWASP:** A05:2021 — Security Misconfiguration
- **Location:** `backend/main.py`
- **Code Evidence:** No Content-Security-Policy (CSP), X-Frame-Options, X-Content-Type-Options, or Referrer-Policy headers are configured.
- **Impact:** The banking portal and administrative dashboards can be embedded inside invisible `<iframe>` tags on attacker sites to perform clickjacking attacks.
- **Remediation:** Add a SecurityHeadersMiddleware enforcing `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and a Content-Security-Policy with `frame-ancestors 'none'`.

---

### Finding HIGH-03: Arbitrary PromQL Execution via Unvalidated Proxy
- **Severity:** HIGH (CVSS 7.5)
- **CWE:** CWE-918 (Server-Side Request Forgery / Internal Query Injection)
- **OWASP API Security:** API7:2023 — Server Side Request Forgery
- **Location:** `backend/api/telemetry.py:139-150` (`execute_promql`)
- **Code Evidence:**
  ```python
  @router.get("/promql", summary="Execute raw PromQL query against Prometheus")
  def execute_promql(query: str, current_user: User = Depends(get_current_user)):
      result = telemetry_service.query_prometheus(query)
      ...
  ```
- **Impact:** Any authenticated user (even a basic Customer) can submit arbitrary, expensive, or malicious PromQL queries directly to the internal Prometheus server, enabling denial of service or metric leakage.
- **Remediation:** Restrict `/telemetry/promql` to Super Admin / Ops roles only, or replace arbitrary query execution with fixed, pre-validated metric query templates.

---

### Finding HIGH-04: Non-Atomic Financial Commits & Missing Idempotency
- **Severity:** HIGH (CVSS 7.4)
- **CWE:** CWE-662 (Improper Synchronization), CWE-841 (Improper Enforcement of Behavioral Workflow)
- **OWASP API Security:** API6:2023 — Unrestricted Resource Consumption
- **Location:** `backend/services/payment_service.py:143-188`
- **Code Evidence:**
  - `ledger_service.post_ledger_transaction()` executes `db.commit()` on the ledger entries.
  - Subsequently, `payment_service.py` sets transaction attributes and executes a second `db.commit()`.
  - No `idempotency_key` is accepted or validated in `BankTransferRequest`.
- **Impact:** Network timeouts or client retries result in duplicate payments being processed. A crash between the two commits leaves orphaned, corrupted financial records.
- **Remediation:** Merge balance updates, ledger entries, transaction metadata, and telemetry into a single database transaction with a single commit. Implement an `idempotency_keys` table to prevent duplicate transfers.

---

### Finding HIGH-05: SQLite Foreign Keys Disabled & Inadequate Concurrency
- **Severity:** HIGH (CVSS 7.1)
- **CWE:** CWE-595 (Comparison of Object References Instead of Values)
- **Location:** `backend/db/connection.py:33-36`
- **Empirical Proof:** Running `PRAGMA foreign_keys;` returned `0` (Disabled). Running `PRAGMA journal_mode;` returned `delete`.
- **Impact:** Foreign key cascades and relational integrity constraints are ignored by SQLite. Multiple concurrent transfers encounter `database is locked` errors instead of queued WAL operations. `with_for_update()` is silently ignored by SQLite.
- **Remediation:** Configure `connect_args={"check_same_thread": False}` with event listeners to execute `PRAGMA foreign_keys = ON;`, `PRAGMA journal_mode = WAL;`, and `PRAGMA busy_timeout = 5000;`. Provide production guidelines for PostgreSQL deployment.

---

### Finding MED-01: Broken Object-Level Authorization (BOLA) in Ledger Audit
- **Severity:** MEDIUM (CVSS 6.5)
- **CWE:** CWE-639 (Authorization Bypass Through User-Controlled Key)
- **OWASP API Security:** API1:2023 — Broken Object Level Authorization
- **Location:** `backend/api/ledger.py:52-99` (`audit_transaction`)
- **Code Evidence:** Validates `current_user`, but does NOT verify that `transaction_id` belongs to `current_user` or that the user is an authorized auditor.
- **Impact:** Any authenticated customer can inspect the full debit/credit breakdown and account IDs of any other customer's transactions.
- **Remediation:** Verify that `current_user.bank_id` matches either `sender_bank_id` or `recipient_bank_id`, or that `current_user` possesses an `AUDITOR` / `INVESTIGATOR` role.

---

### Finding MED-02: Missing Role-Based Access Control (RBAC) Enforcement
- **Severity:** MEDIUM (CVSS 6.5)
- **CWE:** CWE-285 (Improper Authorization)
- **OWASP API Security:** API5:2023 — Broken Function Level Authorization
- **Location:** `backend/middleware/auth_guard.py` vs `backend/api/credits.py:106-139`
- **Code Evidence:** `RoleChecker` is defined in `auth_guard.py` but is **never applied to any endpoint in the entire codebase**. Consequently, any registered customer can call `POST /credits/mint` and mint unlimited carbon credits to their own account.
- **Impact:** Complete breakdown of the carbon credit economy; users can fabricate offset assets.
- **Remediation:** Implement a centralized RBAC dependency framework enforcing explicit permissions for minting, administrative tasks, and investigator actions.

---

### Finding MED-03: Audit Hash Chain Does Not Form a Cryptographic Chain
- **Severity:** MEDIUM (CVSS 5.9)
- **CWE:** CWE-353 (Missing Support for Integrity Check)
- **Location:** `backend/services/payment_service.py:160-163` vs `backend/api/ledger.py:85-98`
- **Code Evidence:**
  ```python
  raw_audit = f"{txn.id}:{source_bank_id}:{dest_bank_id}:{amount}:{total_joules}:{txn.created_at}"
  sha256_hash = hashlib.sha256(raw_audit.encode("utf-8")).hexdigest()
  ```
  The hash does not incorporate `prev_audit_hash`. Therefore, deleting or rewriting earlier transactions does not invalidate subsequent hashes. Furthermore, `ledger.py` reconstructs a completely different string format than `payment_service.py`, causing verified audit checks to be inconsistent.
- **Remediation:** Implement a true cryptographic hash chain (`prev_hash + canonical_txn_fields`), store `prev_hash` in the database, and verify the chain sequentially from genesis.

---

### Finding MED-04: Fabricated Power Data Labeled as "OBSERVED"
- **Severity:** MEDIUM (CVSS 5.3)
- **CWE:** CWE-345 (Insufficient Verification of Data Authenticity)
- **Location:** `backend/services/telemetry_service.py:170-182`
- **Code Evidence:**
  ```python
  if kepler_probe and (platform_power <= 0.0 or container_power <= 0.0):
      telemetry_mode = "OBSERVED"
      KEPLER_AVAILABLE = True
      platform_power = round(24.8 + random.uniform(-0.6, 0.6), 2)  # <-- FABRICATED!
      container_power = round(6.1 + random.uniform(-0.3, 0.3), 2)  # <-- FABRICATED!
  ```
- **Impact:** Misleads compliance audits and users into believing random numbers are real hardware measurements.
- **Remediation:** Strictly reserve `"OBSERVED"` for non-zero physical RAPL hardware readings. If hardware data is missing or zero, report mode as `"SIMULATED"` or `"UNAVAILABLE"`.

---

### Finding LOW-01: Float Precision Used for Financial Balances
- **Severity:** LOW (CVSS 3.7)
- **CWE:** CWE-1339 (Insufficient Precision or Accuracy of a Real Number)
- **Location:** `backend/models/account.py:60`, `backend/models/transaction.py:30`
- **Impact:** Binary floating-point representation errors cause fractional cent drift over high volumes.
- **Remediation:** Migrate balance representation to `Numeric(18, 4)` or integer cents.

---

### Finding LOW-02: Complete Absence of Rate Limiting
- **Severity:** LOW/MEDIUM (CVSS 5.3)
- **CWE:** CWE-307 (Improper Restriction of Excessive Authentication Attempts)
- **OWASP API Security:** API4:2023 — Unrestricted Resource Consumption
- **Impact:** Susceptible to credential stuffing on `/auth/login`, registration flooding on `/auth/register`, and denial of service on CPU-heavy PDF generation `/sustainability/report/pdf`.
- **Remediation:** Implement rate limiting middleware with Redis/in-memory token bucket backend.

---

### Finding LOW-03: Potential CSV Formula Injection
- **Severity:** LOW (CVSS 3.3)
- **CWE:** CWE-1236 (Improper Neutralization of Formula Elements in a CSV File)
- **Location:** `backend/api/sustainability.py:505-521`
- **Impact:** If an account note or transaction description starts with `=`, `+`, `-`, or `@`, spreadsheet software may execute formulas.
- **Remediation:** Prepend a single quote `'` or sanitize text fields that begin with formula characters.

---

## 5. Existing Behavior & Integrity to Preserve

During security hardening and RBAC implementation, the following core functionalities **must remain strictly intact**:
1. **Double-Entry Accounting Rule:** Every financial transfer must create exactly balanced debits and credits ($\sum \text{Debits} = \sum \text{Credits}$).
2. **Account Balance Non-Negativity:** Overdrafts must continue to be rejected with HTTP 400.
3. **Attribution Mathematics:** The energy residual formula $\text{Host} - (\text{Container} + \text{Idle}) = \text{Residual}$ and fidelity calculation must remain mathematically identical.
4. **CEA Grid Emission Factors:** India national grid factor (713 gCO2/kWh) and historical registry factors must remain supported and versioned.
5. **Existing UI Routes:** `/`, `/bank`, `/investigator`, `/grafana` must continue to function seamlessly, upgraded with authenticated sessions and role-specific views.
6. **Prometheus Metrics Compatibility:** Existing metric names (`bank_transactions_total`, `bank_transaction_energy_joules_total`) must be preserved for existing dashboards.

---

## 6. Phased Remediation Strategy

- **Phase 1 (Security Baseline):** Fix path traversal, remove hardcoded secrets, configure strict CORS, add security headers, sanitize error outputs, enable SQLite WAL/foreign keys.
- **Phase 2 (Authentication & Lifecycle):** Implement Argon2id password hashing, session tokens, secure cookies, generic auth errors, rate limiting.
- **Phase 3 (Hierarchical RBAC & Safe Delegation):** Database schema for roles, permissions, cases, and delegations. Implement one-time Boss Admin bootstrap, delegated Admin ceilings, and restricted Investigator case workflows.
- **Phase 4 (Financial & Telemetry Integrity):** Single atomic transactions, idempotency keys, true cryptographic hash chaining, strict OBSERVED vs SIMULATED labeling.
- **Phase 5 (Dedicated Control Centers & Observability):** Boss Admin Center (`/admin/super`), Admin Dashboard (`/admin`), Investigator Workbench (`/investigator`), and Operations Center (`/operations`).
- **Phase 6 (UI Quality & Release Verification):** Mobile responsiveness, navigation fixes, comprehensive automated tests.

---
*End of Security Audit Report.*
