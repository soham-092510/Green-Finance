# Green Finance — Security Acceptance Tests & Verification Matrix
**Document Version:** 1.0.0  
**Date:** October 21, 2026  
**Test Runner:** `pytest` 9.1.1, `pytest-asyncio` 1.4.0, `httpx` 0.28.1, `FastAPI TestClient`  
**Execution Command:** `pytest -o pythonpath=. tests/ -v`

---

## 1. Baseline Test Suite Status (Pre-Hardening)

Prior to the start of this security hardening initiative, the existing test status was recorded:

| Test File | Total Tests | Passing | Failing | Missing / Incomplete Coverage |
| :--- | :--- | :--- | :--- | :--- |
| `tests/test_accuracy_engine.py` | 7 | 7 (100%) | 0 | Covers mathematical energy attribution, drift detection, and unit bank transfer |
| `tests/test_auth.py` | 0 | 0 | 0 | **Empty file (0 bytes)**; zero authentication test coverage |
| `tests/test_api.py` | 0 | 0 | 0 | **Empty file (0 bytes)**; zero API authorization or route test coverage |
| `tests/test_carbon.py` | 0 | 0 | 0 | **Empty file (0 bytes)**; zero carbon validation test coverage |
| **Total Baseline** | **7** | **7** | **0** | **Critical gap: No security, RBAC, BOLA, or injection tests exist.** |

---

## 2. Security Acceptance Test Matrix

Every test in this matrix must be implemented as an automated test file and pass before each phase is marked complete.

### Group 1: Authentication & Account Lifecycle Tests (`tests/test_sec_auth.py`)

| Test ID | Test Case Name | Objective / Trigger | Expected Outcome | Pass/Fail Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **AUTH-01** | `test_customer_registration_success` | POST `/auth/register` with valid email, username, password | HTTP 201 Created; returns JWT token; sets role to `CUSTOMER` (never Admin) | Role is `CUSTOMER`; double-entry accounts created |
| **AUTH-02** | `test_registration_cannot_select_role` | POST `/auth/register` with payload containing `role: "SUPER_ADMIN"` | Request ignores supplied role or rejects; user is assigned `CUSTOMER` | In database, `user.role == "CUSTOMER"` |
| **AUTH-03** | `test_login_invalid_credentials_generic_error` | POST `/auth/login` with non-existent user or wrong password | HTTP 401 Unauthorized with generic `"Invalid username or password"` | Does not reveal whether user exists |
| **AUTH-04** | `test_argon2id_password_hashing` | Inspect user password hash in DB after registration | Hash starts with `$argon2id$` (or verified bcrypt cost $\ge 12$) | Password is never plaintext or reversibly encrypted |
| **AUTH-05** | `test_anonymous_access_rejected_on_protected_routes` | GET `/user/me`, POST `/payment/transfer`, GET `/sustainability/ledger` without token | HTTP 401 Unauthorized with `WWW-Authenticate: Bearer` | Zero data returned; access blocked |
| **AUTH-06** | `test_session_revocation_on_logout` | Log out or revoke session; invoke protected route with prior token | HTTP 401 Unauthorized | Token is immediately rejected after revocation |
| **AUTH-07** | `test_rate_limiting_login_brute_force` | Submit 15 failed logins within 60 seconds from same IP | HTTP 429 Too Many Requests with `Retry-After` header | IP or account throttled; audit event logged |

---

### Group 2: Authorization & Hierarchical RBAC Tests (`tests/test_sec_rbac.py`)

| Test ID | Test Case Name | Objective / Trigger | Expected Outcome | Pass/Fail Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **RBAC-01** | `test_customer_cannot_transfer_from_other_account` | Customer A invokes `/payment/transfer` with `source_account: Customer_B` | HTTP 403 Forbidden; transfer rejected | Customer cannot spend other users' money |
| **RBAC-02** | `test_customer_cannot_access_admin_portal` | Customer token calls `/admin/users` or `/admin/super/audit` | HTTP 403 Forbidden | Access denied with standard error |
| **RBAC-03** | `test_customer_cannot_mint_credits` | Customer token calls `POST /credits/mint` | HTTP 403 Forbidden | Only authorized registry admins can mint |
| **RBAC-04** | `test_investigator_case_boundary_enforcement` | Investigator token queries a case not assigned to them | HTTP 403 Forbidden | Investigators see only assigned cases |
| **RBAC-05** | `test_investigator_cannot_transfer_money` | Investigator token attempts `POST /payment/transfer` | HTTP 403 Forbidden | Investigation role is read-only for ledger |
| **RBAC-06** | `test_delegated_admin_cannot_grant_super_admin` | Delegated Admin attempts to promote user to `SUPER_ADMIN` | HTTP 403 Forbidden; privilege escalation blocked | Boss Admin role cannot be created by delegated admin |
| **RBAC-07** | `test_delegated_admin_ceiling_enforcement` | Delegated Admin attempts to grant permissions outside their delegation | HTTP 403 Forbidden; violation logged | Admin cannot delegate what they do not possess |
| **RBAC-08** | `test_delegated_admin_cannot_revoke_boss_admin` | Delegated Admin attempts to suspend or revoke Boss Admin | HTTP 403 Forbidden | Root administrator cannot be modified by subordinates |
| **RBAC-09** | `test_bola_transaction_audit_access` | Customer A queries `/ledger/audit/{id}` for Customer B's transaction | HTTP 403 Forbidden (unless assigned investigator) | Cross-customer transaction privacy preserved |

---

### Group 3: Financial & Ledger Integrity Tests (`tests/test_sec_financial.py`)

| Test ID | Test Case Name | Objective / Trigger | Expected Outcome | Pass/Fail Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **FIN-01** | `test_double_entry_balance_invariant` | Execute payment transfer; sum all `ledger_entries` debits and credits | $\sum \text{Debits} == \sum \text{Credits}$ exactly | Difference is 0.0000 |
| **FIN-02** | `test_overdraft_prevention_under_concurrency` | 10 concurrent threads attempt to spend ₹50,000 from an account holding ₹50,000 | Exactly 1 transfer succeeds; 9 fail with HTTP 400 | Final balance is $\ge 0.0$; no overdraft occurs |
| **FIN-03** | `test_idempotency_key_prevents_duplicate_transfer` | Submit `/payment/transfer` twice with identical `Idempotency-Key` header | Second call returns original transaction result without transferring money twice | Sender balance debited only once |
| **FIN-04** | `test_negative_and_zero_amount_rejection` | Submit transfer with amounts: `0.0`, `-100.0`, `NaN`, `1e30` | HTTP 422 Unprocessable Entity | Invalid numbers rejected before ledger write |
| **FIN-05** | `test_atomic_rollback_on_partial_failure` | Intentionally trigger database constraint failure after entry creation | Entire transaction rolls back; no orphaned records | Database remains in clean, balanced state |
| **FIN-06** | `test_cryptographic_audit_hash_chain` | Alter a single transaction record in test fixture; verify hash chain | Chain verification fails at altered block | Tamper-evident detection succeeds |

---

### Group 4: Injection & Abuse Defense Tests (`tests/test_sec_injection.py`)

| Test ID | Test Case Name | Objective / Trigger | Expected Outcome | Pass/Fail Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **INJ-01** | `test_path_traversal_rejection` | Request `GET /shared/..%2F..%2F.env` and `GET /shared/%2e%2e%2fconfig.py` | HTTP 404 Not Found or HTTP 400 Bad Request; zero leaked content | Path traversal blocked completely |
| **INJ-02** | `test_sql_injection_defense` | Send SQL payload in search parameters: `' OR '1'='1` in `/sustainability/ledger` | Parameter treated as literal string; no query syntax execution | Safe ORM parameterization verified |
| **INJ-03** | `test_promql_injection_and_access_restriction` | Anonymous or Customer calls `/telemetry/promql?query=...` | HTTP 401 or 403; arbitrary Prometheus queries blocked | Internal metrics proxy secured |
| **INJ-04** | `test_csv_formula_injection_sanitization` | Export CSV with account note starting with `=cmd|' /C calc'!A0` | CSV field is prepended with `'` or sanitized | Formula execution neutralized |
| **INJ-05** | `test_security_headers_present` | Inspect response headers on any API or frontend route | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy` | All OWASP baseline headers present |

---

### Group 5: Monitoring, Observability & UI Quality Tests (`tests/test_sec_monitoring.py`)

| Test ID | Test Case Name | Objective / Trigger | Expected Outcome | Pass/Fail Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **MON-01** | `test_metrics_endpoint_access_control` | Unauthenticated request to `/metrics` | HTTP 401 Unauthorized or IP-restricted | Prometheus scrape requires auth |
| **MON-02** | `test_metric_labels_cardinality_bounded` | Execute transfers; verify metric labels in `/metrics` | Labels use bounded categories (`status`, `service`), never user IDs or emails | No high-cardinality label leak |
| **MON-03** | `test_telemetry_mode_distinguishes_observed_and_simulated` | Query telemetry when physical Kepler RAPL is unavailable | Telemetry mode is explicitly `"SIMULATED"` | No fabricated data labeled "OBSERVED" |
| **UI-01** | `test_all_frontend_routes_render_cleanly` | GET `/`, `/bank`, `/investigator`, `/admin`, `/operations` | HTTP 200 OK; correct `<!DOCTYPE html>`; unique title tag | Clean rendering without template errors |
| **UI-02** | `test_custom_404_error_page` | Request non-existent route `/non-existent-page` | Safe JSON or branded HTML 404 error page | No stack traces, file paths, or debug leaks |

---

## 3. Test Execution & Reporting Protocol

1. **Automated Execution:** Tests are executed via `pytest -o pythonpath=. -v tests/`.
2. **Isolation Guarantee:** All security tests execute against an isolated temporary SQLite database or mock session; never against production.
3. **Exit Criteria:** A phase cannot be marked complete unless 100% of applicable test cases pass. Suppressing warnings or commenting out assertions is strictly prohibited.

---
*End of Security Acceptance Tests.*
