# Green Finance — Hardening, RBAC & Operations Center Implementation Plan
**Document Version:** 1.0.0  
**Date:** October 21, 2026  
**Implementation Branch:** `security-hardening-rbac-control-center`  
**Execution Standard:** Small, testable phases; verified by automated acceptance tests; zero regressions to existing banking or energy mathematics.

---

## 1. Schema Evolution & Database Migration Design

To support hierarchical RBAC, session revocation, one-time Boss Admin bootstrap, investigation cases, and double-entry idempotency without breaking existing SQLite or PostgreSQL data, the following schema additions are designed.

### 1.1 New & Enhanced Entities

```
  +------------------+         +-------------------------+
  |      users       |         |       user_roles        |
  |------------------|         |-------------------------|
  | id (PK, UUID)    |<------->| user_id (FK -> users)   |
  | username (Unique)|         | role_id (FK -> roles)   |
  | email (Unique)   |         | granted_by (FK -> users)|
  | password_hash    |         | granted_at (DateTime)   |
  | status           |         +-------------------------+
  | is_boss_admin    |
  | mfa_secret       |         +-------------------------+
  | mfa_enabled      |         |  permission_delegations |
  | failed_logins    |         |-------------------------|
  | locked_until     |         | id (PK, UUID)           |
  | created_at       |         | delegator_id (FK)       |
  +------------------+         | delegatee_id (FK)       |
          |                    | permission_id (FK)      |
          |                    | can_subdelegate (Bool)  |
          v                    | max_ceiling (String)    |
  +------------------+         +-------------------------+
  |   auth_sessions  |
  |------------------|         +-------------------------+
  | id (PK, UUID)    |         |   investigation_cases   |
  | user_id (FK)     |         |-------------------------|
  | token_jti        |         | id (PK, UUID)           |
  | is_revoked (Bool)|         | title (String)          |
  | ip_address       |         | severity (String)       |
  | user_agent       |         | status (OPEN/CLOSED)    |
  | created_at       |         | transaction_id (FK)     |
  | expires_at       |         | findings (Text)         |
  +------------------+         +-------------------------+
          |                                 |
          v                                 v
  +------------------+         +-------------------------+
  | security_audit   |         |investigation_assignments|
  |------------------|         |-------------------------|
  | id (PK, UUID)    |         | case_id (FK -> cases)   |
  | actor_id (FK)    |         | investigator_id (FK)    |
  | action (String)  |         | assigned_at (DateTime)  |
  | target_id (Str)  |         +-------------------------+
  | outcome (SUCCESS)|
  | ip_address       |         +-------------------------+
  | details (JSON)   |         |    idempotency_keys     |
  | timestamp        |         |-------------------------|
  +------------------+         | key (PK, String)        |
                               | user_id (FK -> users)   |
                               | response_body (JSON)    |
                               | status_code (Int)       |
                               | created_at (DateTime)   |
                               +-------------------------+
```

### 1.2 Initial Roles & Permission Hierarchy
1. **SUPER_ADMIN / BOSS_ADMIN:**
   - Appointed only via one-time secure bootstrap.
   - Holds all permissions: `users.manage`, `admins.create`, `admins.delegate`, `security.audit`, `investigations.assign`, `telemetry.manage`.
   - Cannot be modified or revoked by subordinate Admins.
2. **ADMIN (Delegated Admin):**
   - Can manage users and assign permissions strictly within their authorized delegation ceiling.
   - Cannot create Boss Admins or escalate own permissions.
3. **INVESTIGATOR:**
   - Scoped access only to assigned `investigation_cases` and related transaction telemetry.
   - Read-only for balances and ledger records; cannot execute fund transfers.
4. **CUSTOMER (Standard User):**
   - Default role on registration.
   - Can view only own account, transactions, and initiate transfers from own cash wallet.

---

## 2. Phase-by-Phase Implementation Blueprint

```
Phase 0: Repository Audit & Baseline Verification (Completed)
   │
   ├── Phase 1: Security Baseline & Perimeter Hardening
   │     • Fix static path traversal (CRIT-01)
   │     • Secure CORS allowlist & add SecurityHeadersMiddleware (HIGH-01, HIGH-02)
   │     • Remove hardcoded secrets; validate environment (CRIT-04)
   │     • Enable SQLite WAL mode, foreign keys & busy timeout (HIGH-05)
   │     • Standardize error handling (avoid stack trace leaks)
   │
   ├── Phase 2: Rate Limiting & Abuse Prevention
   │     • Implement in-memory/Redis rate limiter middleware
   │     • Configure per-endpoint quotas (login, transfer, PDF export)
   │     • Generic authentication error responses (no account enumeration)
   │
   ├── Phase 3: Authentication & Session Lifecycle
   │     • Argon2id password hashing implementation
   │     • Session revocation table (`auth_sessions`)
   │     • Secure cookie and bearer token validation
   │     • Public registration assigns CUSTOMER role only
   │
   ├── Phase 4: Hierarchical RBAC & Boss Admin Bootstrap
   │     • Schema migrations (roles, permissions, delegations, audit)
   │     • One-time Boss Admin CLI bootstrap command
   │     • Centralized FastAPI authorization dependencies (`require_permission`)
   │     • Scoped delegation engine preventing privilege escalation
   │     • Persistent security audit logging (`security_audit_events`)
   │
   ├── Phase 5: Financial Engine & Cryptographic Integrity
   │     • Atomic single-transaction transfers (balance + ledger + telemetry)
   │     • Mandatory Idempotency-Key handling for transfers
   │     • True cryptographic hash chain (`prev_hash` linking)
   │     • Strict OBSERVED vs SIMULATED telemetry labeling
   │
   ├── Phase 6: Operational Control Centers & Real-Time Dashboards
   │     • Boss Admin Center (`/admin/super`)
   │     • Delegated Admin Dashboard (`/admin`)
   │     • Investigator Workbench (`/investigator`) with assigned case views
   │     • Security & Operations Center (`/operations`) with live Prometheus rates
   │
   └── Phase 7: UI Quality, Mobile Responsiveness & Automated CI Verification
         • Eliminate horizontal overflow on all screen sizes
         • Fix navigation links, accessibility, and feedback states
         • Automated CI security checks (pytest, bandit, pip-audit)
```

---

## 3. High-Priority Architectural Decisions

### 3.1 One-Time Boss Admin Bootstrap
- **Mechanism:** A standalone CLI script (`python -m backend.scripts.bootstrap_admin`) or secure environment variable hook `BOOTSTRAP_ADMIN_TOKEN`.
- **Invariants:**
  1. Checks if any user with `is_boss_admin=True` exists in the database.
  2. If an active Boss Admin already exists, bootstrap terminates immediately with a security log event.
  3. Prompts for credentials interactively or reads a single-use secret token; creates the initial Boss Admin within an atomic database transaction.
  4. Requires MFA enrollment before normal administrative session use.

### 3.2 Centralized Authorization Dependency
Instead of loose ad-hoc checks, every endpoint is protected using declarative FastAPI dependencies:
```python
# Customer accessing own account
@router.post("/payment/transfer")
def transfer_funds(
    payload: BankTransferRequest,
    current_user: User = Depends(require_permission("transactions.create_transfer")),
    db: Session = Depends(get_db)
): ...

# Delegated Admin managing users
@router.post("/admin/users/{user_id}/suspend")
def suspend_user(
    user_id: str,
    admin_user: User = Depends(require_permission("users.suspend_scoped")),
    db: Session = Depends(get_db)
): ...
```

### 3.3 Rate Limiter Design
- **Algorithm:** Leaky Bucket / Token Bucket.
- **Storage:** Pluggable backend (in-memory dictionary with thread locking for single-process/local dev; Redis connection for multi-worker Render deployment).
- **Limits:**
  - Login / Auth: 10 requests / minute / IP
  - Transfers: 30 requests / minute / account
  - PDF/CSV Exports: 5 requests / minute / IP
  - Telemetry & General: 120 requests / minute

### 3.4 Financial Idempotency
- Incoming `POST /payment/transfer` requires or accepts an `Idempotency-Key: <UUID>` header.
- If the key exists in the database:
  - If processing: Returns HTTP 409 Conflict.
  - If completed: Returns cached response directly without re-executing ledger entries.
- If new: Key is reserved and committed in the same database transaction.

---

## 4. Rollback & Disaster Recovery Strategy

1. **Database Safety:** SQLite database `test.db` will be backed up prior to schema migration (`test.db.bak_YYYYMMDD`).
2. **Feature Branch Isolation:** All changes reside in branch `security-hardening-rbac-control-center`. If any failure occurs, reverting to `main` restores the working baseline immediately.
3. **Additive Schema Updates:** New tables (`roles`, `permissions`, `auth_sessions`, `investigation_cases`, `idempotency_keys`) and non-destructive column additions are backward-compatible with existing queries.

---
*End of Implementation Plan.*
