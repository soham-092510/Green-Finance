# Green Finance — Threat Model & STRIDE Analysis
**Document Version:** 1.0.0  
**Date:** October 21, 2026  
**System:** Green Finance Enterprise Ecosystem  
**Standards:** Microsoft STRIDE Model, OWASP Top 10, OWASP API Security Top 10

---

## 1. Scope & System Overview

Green Finance is a hybrid financial technology and sustainability platform. It processes real-time financial fund transfers, maintains a double-entry general ledger, monitors computational energy consumption via eBPF/RAPL hardware counters, calculates Scope 2 greenhouse gas emissions using regional grid factors, and exports regulatory compliance reports.

This threat model identifies key threat actors, assets, data flows, trust boundaries, and specific threat vectors categorized by the **STRIDE** methodology.

---

## 2. Attacker Profiles & Motivations

| Attacker Profile | Capabilities / Access Level | Primary Motivation | Potential Impact |
| :--- | :--- | :--- | :--- |
| **A1: Anonymous Web Attacker** | Unauthenticated internet access to public endpoints (port 8000, 3000, 9090) | Financial theft, data leakage, denial of service | Draining balances via unauthenticated `/payment/transfer`, leaking `.env` via path traversal, exploiting Grafana default credentials |
| **A2: Malicious Registered Customer** | Authenticated as a standard user (`CUSTOMER` / `INVESTOR`) | Illicit credit creation, unauthorized transfers from other accounts | Minting arbitrary carbon credits via `/credits/mint`, BOLA on `/ledger/audit/{id}`, overdrafting via race conditions |
| **A3: Compromised or Rogue Delegated Admin** | Delegated administrative privileges granted by Boss Admin | Privilege escalation, unauthorized surveillance, audit tampering | Attempting to promote themselves to Boss Admin, delegating permissions beyond their ceiling, revoking superior admins |
| **A4: Rogue or Overreaching Investigator** | Read access to assigned carbon emission cases | Corporate espionage, tampering with investigation evidence | Viewing transactions outside assigned cases, modifying case conclusions or altering raw telemetry |
| **A5: Automated Bot / Scraper** | High-concurrency automated scripts | Credential stuffing, denial of service | Flooding `/auth/login`, exhausting CPU via `/sustainability/report/pdf` batch generation |

---

## 3. High-Value Assets & Impact Matrix

| Asset | Description | Confidentiality Impact | Integrity Impact | Availability Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Cash Wallets & Bank Balances** | User financial assets stored in `accounts` table | **HIGH** (exposing wealth) | **CRITICAL** (theft/alteration) | **HIGH** (frozen funds) |
| **Double-Entry General Ledger** | Balanced journal entries (`transactions`, `ledger_entries`) | **HIGH** (transaction privacy)| **CRITICAL** (ledger corruption)| **HIGH** (reconciliation halt)|
| **Authentication Secrets & Tokens** | Passwords, JWT secrets, active session records | **CRITICAL** (account takeover)| **CRITICAL** (token forgery) | **MEDIUM** |
| **Cryptographic Audit Chain** | SHA-256 digests linking historical transactions | **LOW** (hashes are public) | **CRITICAL** (undetected fraud) | **MEDIUM** |
| **Grid Carbon Registry & Calculations**| CEA emission factors, mathematical formulas | **LOW** (factors are public)  | **HIGH** (false greenwashing) | **MEDIUM** |
| **Hardware Telemetry & Metrics** | Kepler PromQL metrics, host RAPL power data | **MEDIUM** (operational intel) | **HIGH** (falsifying efficiency) | **MEDIUM** |
| **Investigation Case Evidence** | Investigator notes, suspicious anomaly alerts | **HIGH** (whistleblower/fraud) | **HIGH** (evidence destruction) | **MEDIUM** |

---

## 4. Data Flow Diagrams (DFDs) & Trust Boundaries

```
[ External Client ]
       |
       |  (Untrusted Boundary 1: Public Network)
       v
+-------------------------------------------------------------+
| FastAPI Ingress & Security Middleware                        |
| - Rate Limiter -> CORS Check -> Security Headers -> Router  |
+-------------------------------------------------------------+
       |
       |  (Trust Boundary 2: Identity & Session Verification)
       v
+-------------------------------------------------------------+
| Central Authorization & RBAC Dependency Guard               |
| - Verifies JWT Signature, Expiry, Session Revocation        |
| - Validates Scoped Permissions & Role Ceilings              |
+-------------------------------------------------------------+
       |
       +--------------------+--------------------+
       |                    |                    |
       v                    v                    v
+---------------+    +----------------+    +------------------+
| Banking &     |    | Sustainability |    | Observability &  |
| Ledger Core   |    | Intelligence   |    | Monitoring Core  |
+---------------+    +----------------+    +------------------+
       |                    |                    |
       | (Atomic Boundary 3)|                    | (SSRF Guard 4)
       v                    v                    v
+---------------+    +----------------+    +------------------+
| Database (SQL)|    | Case & Reports |    | Prometheus TSDB  |
| - Row Locks   |    | - SHA-256 Chain|    | - Kepler RAPL    |
| - Constraints |    | - Sanitized CSV|    | - Scoped Labels  |
+---------------+    +----------------+    +------------------+
```

---

## 5. Detailed STRIDE Threat Analysis

### 5.1 Spoofing (Identity Deception)
- **Threat S-1: JWT Forgery via Hardcoded Secret**
  - *Vulnerability:* `JWT_SECRET_KEY` was hardcoded as `"green-finance-super-secret-key-2026"` in `render.yaml` and `config.py`.
  - *Attack:* Attacker signs arbitrary JWT payloads with `sub: "soham_gaikwad"` and `role: "SUPER_ADMIN"`.
  - *Mitigation:* Require high-entropy environment secrets generated at runtime; fail server startup if secret is default or $<32$ characters.
- **Threat S-2: Unauthenticated Bank Transfer Spoofing**
  - *Vulnerability:* `/payment/transfer` accepts `source_account` from the request body without checking authentication.
  - *Attack:* Attacker transfers funds out of `HDFC9999` while unauthenticated.
  - *Mitigation:* Extract authenticated identity exclusively from server-side JWT session; reject caller-supplied source accounts.

### 5.2 Tampering (Data Modification)
- **Threat T-1: Path Traversal Arbitrary File Read & Overwrite**
  - *Vulnerability:* `/shared/{file_path:path}` uses loose path resolution without directory boundary checks.
  - *Attack:* Attacker leaks `.env` or application source code.
  - *Mitigation:* Enforce strict `os.path.commonpath` verification and mount static files using FastAPI's hardened handlers.
- **Threat T-2: Non-Atomic Double-Entry Commits**
  - *Vulnerability:* `post_ledger_transaction` commits ledger entries before payment metadata is saved.
  - *Attack:* Crash or interrupt between commits creates unbalanced or metadata-free financial records.
  - *Mitigation:* Execute ledger entry writes, balance updates, telemetry recording, and audit hash updates in a single atomic database transaction.
- **Threat T-3: Audit Hash Rewriting**
  - *Vulnerability:* Hashes are calculated independently per transaction without chaining `prev_hash`.
  - *Attack:* Attacker alters an old transaction and recomputes only its single hash without invalidating subsequent blocks.
  - *Mitigation:* Implement true cryptographic hash chaining linking each transaction to the previous block's digest (`hash(prev_hash + canonical_txn_fields)`).

### 5.3 Repudiation (Denying Actions)
- **Threat R-1: Absence of Security & Administrative Audit Logging**
  - *Vulnerability:* Role assignments, permission delegations, case status updates, and failed logins are not recorded in a persistent security audit table.
  - *Attack:* Rogue admin grants privileges or alters carbon factors and denies involvement.
  - *Mitigation:* Create a dedicated `security_audit_events` table recording actor ID, target ID, action, timestamp, and IP address for all sensitive operations.

### 5.4 Information Disclosure (Privacy Breach)
- **Threat I-1: Public Exposure of All Bank Accounts & Balances**
  - *Vulnerability:* `GET /payment/accounts` dumps all registered accounts, names, and balances to unauthenticated callers.
  - *Attack:* Competitive intelligence gathering, targeted phishing, or account identification for theft.
  - *Mitigation:* Require authentication and restrict account listing so regular customers see only their own accounts.
- **Threat I-2: BOLA in Transaction Audit Details**
  - *Vulnerability:* `GET /ledger/audit/{id}` allows any authenticated user to inspect another user's transaction details.
  - *Attack:* User A views User B's financial relationships and amounts.
  - *Mitigation:* Enforce object-level ownership checks (`user.bank_id IN (sender, recipient)`).

### 5.5 Denial of Service (Resource Exhaustion)
- **Threat D-1: Absence of Rate Limiting & Expensive Workload Endpoints**
  - *Vulnerability:* `/payment/stimulate`, `/payment/benchmark`, and `/sustainability/report/pdf` can be triggered without limits.
  - *Attack:* Attacker sends thousands of PDF generation requests or benchmark batches, saturating CPU and memory.
  - *Mitigation:* Implement rate limiting middleware (IP + account limits) with 429 Retry-After responses and bounded execution timeouts.
- **Threat D-2: Arbitrary PromQL Execution (SSRF / Heavy Queries)**
  - *Vulnerability:* `/telemetry/promql` proxies arbitrary Prometheus queries.
  - *Attack:* Attacker sends expensive regex or multi-year matrix queries crashing Prometheus.
  - *Mitigation:* Restrict endpoint to authorized Operations admins; validate query complexity.

### 5.6 Elevation of Privilege (Unauthorized Authority)
- **Threat E-1: Ineffective Role Guards & Direct Credit Minting**
  - *Vulnerability:* `RoleChecker` is never applied to route controllers.
  - *Attack:* Standard user calls `POST /credits/mint` to mint millions of carbon offset credits.
  - *Mitigation:* Centralize RBAC enforcement using FastAPI dependencies; require explicit permissions for minting.
- **Threat E-2: Delegated Admin Privilege Escalation**
  - *Vulnerability:* If ordinary Admins can create other Admins without ceiling restrictions, they can grant root authority.
  - *Attack:* A delegated admin grants themselves or a peer `SUPER_ADMIN` privileges.
  - *Mitigation:* Enforce strict delegation rules: Admins can delegate only permissions they explicitly hold, cannot grant Boss Admin, cannot elevate their own role, and cannot revoke superiors.

---

## 6. Threat Mitigation Matrix

| Threat ID | STRIDE Category | Affected Component | Target Remediation Phase |
| :--- | :--- | :--- | :--- |
| **S-1** | Spoofing | Auth / JWT Configuration | Phase 1 & Phase 2 |
| **S-2** | Spoofing | Core Banking API | Phase 1 & Phase 4 |
| **T-1** | Tampering | Static Asset Serving | Phase 1 |
| **T-2** | Tampering | Financial Ledger Engine | Phase 4 |
| **T-3** | Tampering | Audit Hash Chain | Phase 4 |
| **R-1** | Repudiation | System Audit Logging | Phase 3 & Phase 4 |
| **I-1** | Information Disclosure | Banking API / Sustainability | Phase 1 & Phase 3 |
| **I-2** | Information Disclosure | Ledger API (BOLA) | Phase 3 |
| **D-1** | Denial of Service | Global Rate Limiter | Phase 1 & Phase 2 |
| **D-2** | Denial of Service | Telemetry PromQL Proxy | Phase 1 & Phase 5 |
| **E-1** | Elevation of Privilege | Carbon Credits Router | Phase 3 |
| **E-2** | Elevation of Privilege | RBAC Delegation Engine | Phase 3 |

---
*End of Security Threat Model.*
