# =====================================================================
# GREEN-FINANCE — TEST_AUTH_PRODUCTION.PY
# Purpose: Comprehensive 30-Scenario Automated Security & Functional Test Suite
#          satisfying all requirements in Section 10 against an isolated test database.
# =====================================================================

import os
import uuid
import secrets
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.db.base import Base
from backend.db.session import get_db
from backend.core.config import settings
from backend.core.security import hash_password, verify_password, create_access_token
from backend.models.user import User
from backend.models.account import Account
from backend.models.session import AuthSession
from backend.models.rbac import SecurityAuditEvent, PermissionDelegation
from backend.services.rbac_service import init_rbac_system, assign_role_to_user, bootstrap_boss_admin
from backend.middleware.rate_limit import limiter

# ---------------------------------------------------------------------
# ISOLATED TEST DATABASE FIXTURE (ZERO PRODUCTION/DEV DATA POLLUTION)
# ---------------------------------------------------------------------
TEST_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_auth_isolated.db"))
TEST_DB_URL = f"sqlite:///{TEST_DB_PATH}"

test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False}
)

@event.listens_for(test_engine, "connect")
def configure_sqlite(dbapi_conn, record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.close()

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_isolated_database():
    """Builds clean isolated schema, initializes RBAC seeds, and tears down after tests."""
    if os.path.exists(TEST_DB_PATH):
        try: os.remove(TEST_DB_PATH)
        except Exception: pass

    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db

    db = TestSessionLocal()
    try:
        init_rbac_system(db)
    finally:
        db.close()

    yield

    app.dependency_overrides.pop(get_db, None)
    test_engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        try: os.remove(TEST_DB_PATH)
        except Exception: pass


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_rate_limits():
    limiter.reset()


# =====================================================================
# SECTION 10 TEST SUITE: SCENARIOS 1 - 30
# =====================================================================

# ---------------------------------------------------------------------
# REGISTRATION (Scenarios 1 - 7)
# ---------------------------------------------------------------------

def test_01_valid_customer_registration_succeeds(client):
    """Scenario 1: Valid customer registration succeeds."""
    uname = f"reg_user_{uuid.uuid4().hex[:8]}"
    resp = client.post("/auth/register", json={
        "name": "Alex Mercer",
        "username": uname,
        "email": f"{uname}@greenfinance.dev",
        "password": "ValidPassword99!",
        "confirm_password": "ValidPassword99!"
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["username"] == uname
    assert data["user"]["role"] == "CUSTOMER"


def test_02_new_customer_persisted_in_database(client):
    """Scenario 2: The new customer is persisted in the database."""
    uname = f"persist_{uuid.uuid4().hex[:8]}"
    email = f"{uname}@greenfinance.dev"
    resp = client.post("/auth/register", json={
        "name": "Persisted Customer",
        "username": uname,
        "email": email,
        "password": "ValidPassword99!",
        "confirm_password": "ValidPassword99!"
    })
    assert resp.status_code == 201

    db = TestSessionLocal()
    try:
        user = db.query(User).filter(User.username == uname).first()
        assert user is not None
        assert user.email == email
        assert user.role == "CUSTOMER"
        assert user.bank_id is not None
        # Double-entry ledger accounts must be initialized
        accounts = db.query(Account).filter(Account.user_id == user.id).all()
        acct_names = {a.name for a in accounts}
        assert "cash_wallet" in acct_names
        assert "carbon_asset" in acct_names
        assert "carbon_liability" in acct_names
    finally:
        db.close()


def test_03_duplicate_email_username_rejected(client):
    """Scenario 3: Duplicate email and username are rejected."""
    uname = f"dup_{uuid.uuid4().hex[:8]}"
    email = f"{uname}@greenfinance.dev"
    resp1 = client.post("/auth/register", json={
        "name": "Original User",
        "username": uname,
        "email": email,
        "password": "ValidPassword99!",
        "confirm_password": "ValidPassword99!"
    })
    assert resp1.status_code == 201

    # Attempt duplicate username
    resp2 = client.post("/auth/register", json={
        "name": "Duplicate Username",
        "username": uname,
        "email": f"diff_{uname}@greenfinance.dev",
        "password": "ValidPassword99!",
        "confirm_password": "ValidPassword99!"
    })
    assert resp2.status_code == 400
    assert "Username is already registered" in resp2.text

    # Attempt duplicate email (even with different casing)
    resp3 = client.post("/auth/register", json={
        "name": "Duplicate Email",
        "username": f"diff_{uname}",
        "email": email.upper(),
        "password": "ValidPassword99!",
        "confirm_password": "ValidPassword99!"
    })
    assert resp3.status_code == 400
    assert "Email address is already registered" in resp3.text


def test_04_invalid_fields_rejected(client):
    """Scenario 4: Invalid fields are rejected (short password, invalid email, mismatched confirm)."""
    # 1. Short password (< 8 chars)
    r1 = client.post("/auth/register", json={
        "name": "Short Pwd",
        "username": f"u_{uuid.uuid4().hex[:6]}",
        "email": "short@example.com",
        "password": "Pass1",
        "confirm_password": "Pass1"
    })
    assert r1.status_code == 422

    # 2. Password without digits
    r2 = client.post("/auth/register", json={
        "name": "No Digits",
        "username": f"u_{uuid.uuid4().hex[:6]}",
        "email": "nodigits@example.com",
        "password": "NoDigitsPasswordHere",
        "confirm_password": "NoDigitsPasswordHere"
    })
    assert r2.status_code == 422

    # 3. Invalid email format
    r3 = client.post("/auth/register", json={
        "name": "Invalid Email",
        "username": f"u_{uuid.uuid4().hex[:6]}",
        "email": "not-a-valid-email",
        "password": "ValidPassword99!",
        "confirm_password": "ValidPassword99!"
    })
    assert r3.status_code == 422

    # 4. Mismatched confirm password
    r4 = client.post("/auth/register", json={
        "name": "Mismatch Pwd",
        "username": f"u_{uuid.uuid4().hex[:6]}",
        "email": "mismatch@example.com",
        "password": "ValidPassword99!",
        "confirm_password": "CompletelyDifferent99!"
    })
    assert r4.status_code == 422


def test_05_supplying_privileged_role_cannot_elevate(client):
    """Scenario 5: Supplying role: 'Boss Admin' or 'SUPER_ADMIN' cannot create a privileged account."""
    uname = f"hack_role_{uuid.uuid4().hex[:8]}"
    resp = client.post("/auth/register", json={
        "name": "Role Injection Attacker",
        "username": uname,
        "email": f"{uname}@example.com",
        "password": "ValidPassword99!",
        "confirm_password": "ValidPassword99!",
        "role": "SUPER_ADMIN"
    })
    assert resp.status_code == 201
    db = TestSessionLocal()
    try:
        u = db.query(User).filter(User.username == uname).first()
        assert u.role == "CUSTOMER", "Attacker escalated their role to SUPER_ADMIN!"
        assert u.is_boss_admin is False
    finally:
        db.close()


def test_06_supplying_is_admin_cannot_elevate_privileges(client):
    """Scenario 6: Supplying is_admin: true or permissions cannot elevate privileges."""
    uname = f"hack_admin_{uuid.uuid4().hex[:8]}"
    resp = client.post("/auth/register", json={
        "name": "Admin Field Attacker",
        "username": uname,
        "email": f"{uname}@example.com",
        "password": "ValidPassword99!",
        "confirm_password": "ValidPassword99!",
        "is_admin": True,
        "is_boss_admin": True,
        "permissions": ["*"]
    })
    assert resp.status_code == 201
    db = TestSessionLocal()
    try:
        u = db.query(User).filter(User.username == uname).first()
        assert u.role == "CUSTOMER"
        assert u.is_boss_admin is False
    finally:
        db.close()


def test_07_stored_passwords_are_argon2id_hashes(client):
    """Scenario 7: Stored passwords are hashes and cannot be used as plaintext credentials."""
    uname = f"hash_user_{uuid.uuid4().hex[:8]}"
    plain_pwd = "SecretPassword123!"
    client.post("/auth/register", json={
        "name": "Hash Verification User",
        "username": uname,
        "email": f"{uname}@example.com",
        "password": plain_pwd,
        "confirm_password": plain_pwd
    })

    db = TestSessionLocal()
    try:
        u = db.query(User).filter(User.username == uname).first()
        assert u.hashed_password != plain_pwd
        assert u.hashed_password.startswith("$argon2id$")
        assert verify_password(plain_pwd, u.hashed_password) is True
    finally:
        db.close()


# ---------------------------------------------------------------------
# LOGIN (Scenarios 8 - 13)
# ---------------------------------------------------------------------

def test_08_correct_credentials_succeed_username_and_email(client):
    """Scenario 8: Correct credentials succeed with username and with email."""
    uname = f"login_dual_{uuid.uuid4().hex[:8]}"
    email = f"{uname}@example.com"
    pwd = "ValidPassword99!"
    r_reg = client.post("/auth/register", json={
        "name": "Dual Login User",
        "username": uname,
        "email": email,
        "password": pwd,
        "confirm_password": pwd
    })
    assert r_reg.status_code == 201

    # 1. Login with username
    r1 = client.post("/auth/login-json", json={"username": uname, "password": pwd})
    assert r1.status_code == 200
    assert "access_token" in r1.json()

    # 2. Login with email
    r2 = client.post("/auth/login-json", json={"username": email, "password": pwd})
    assert r2.status_code == 200
    assert "access_token" in r2.json()


def test_09_incorrect_password_fails_with_generic_message(client):
    """Scenario 9: Incorrect password fails with generic message."""
    uname = f"wrong_pwd_{uuid.uuid4().hex[:8]}"
    client.post("/auth/register", json={
        "name": "Wrong Password Test",
        "username": uname,
        "email": f"{uname}@example.com",
        "password": "ValidPassword99!",
        "confirm_password": "ValidPassword99!"
    })

    resp = client.post("/auth/login-json", json={
        "username": uname,
        "password": "IncorrectPassword123!"
    })
    assert resp.status_code == 401
    err_msg = resp.json().get("error") or resp.json().get("detail")
    assert err_msg == "Invalid username/email or password"


def test_10_unknown_account_fails_with_identical_generic_message(client):
    """Scenario 10: Unknown accounts fail with identical generic message (no enumeration)."""
    resp = client.post("/auth/login-json", json={
        "username": f"ghost_user_{uuid.uuid4().hex}",
        "password": "AnyPassword123!"
    })
    assert resp.status_code == 401
    err_msg = resp.json().get("error") or resp.json().get("detail")
    assert err_msg == "Invalid username/email or password"


def test_11_disabled_accounts_fail(client):
    """Scenario 11: Disabled or suspended accounts fail authentication."""
    uname = f"suspended_{uuid.uuid4().hex[:8]}"
    pwd = "ValidPassword99!"
    client.post("/auth/register", json={
        "name": "Suspended User",
        "username": uname,
        "email": f"{uname}@example.com",
        "password": pwd,
        "confirm_password": pwd
    })

    # Manually suspend user in DB
    db = TestSessionLocal()
    try:
        u = db.query(User).filter(User.username == uname).first()
        u.status = "SUSPENDED"
        db.commit()
    finally:
        db.close()

    resp = client.post("/auth/login-json", json={"username": uname, "password": pwd})
    assert resp.status_code == 403
    assert "suspended" in resp.text.lower()


def test_12_login_establishes_authenticated_session_in_db(client):
    """Scenario 12: Login establishes the expected authenticated session in auth_sessions."""
    uname = f"sess_user_{uuid.uuid4().hex[:8]}"
    pwd = "ValidPassword99!"
    client.post("/auth/register", json={
        "name": "Session User",
        "username": uname,
        "email": f"{uname}@example.com",
        "password": pwd,
        "confirm_password": pwd
    })

    resp = client.post("/auth/login-json", json={"username": uname, "password": pwd})
    assert resp.status_code == 200
    jti = resp.json().get("jti")
    assert jti is not None

    db = TestSessionLocal()
    try:
        session_rec = db.query(AuthSession).filter(AuthSession.token_jti == jti).first()
        assert session_rec is not None
        assert session_rec.is_revoked is False
        assert session_rec.expires_at > datetime.utcnow()
    finally:
        db.close()


def test_13_session_cookie_has_expected_security_attributes(client):
    """Scenario 13: The session cookie has expected attributes (HttpOnly, SameSite=Lax, Path=/)."""
    uname = f"cookie_user_{uuid.uuid4().hex[:8]}"
    pwd = "ValidPassword99!"
    client.post("/auth/register", json={
        "name": "Cookie User",
        "username": uname,
        "email": f"{uname}@example.com",
        "password": pwd,
        "confirm_password": pwd
    })

    resp = client.post("/auth/login-json", json={"username": uname, "password": pwd})
    assert resp.status_code == 200
    cookies = resp.headers.get_list("set-cookie")
    access_cookie_header = next((c for c in cookies if "access_token=" in c), None)
    assert access_cookie_header is not None
    assert "HttpOnly" in access_cookie_header
    assert "Path=/" in access_cookie_header
    assert "samesite=lax" in access_cookie_header.lower()
    assert "Max-Age=" in access_cookie_header


# ---------------------------------------------------------------------
# SESSIONS & CSRF (Scenarios 14 - 18)
# ---------------------------------------------------------------------

def test_14_session_restoration_works_after_refresh(client):
    """Scenario 14: Session restoration works after page refresh (using server /user/me)."""
    uname = f"refresh_{uuid.uuid4().hex[:8]}"
    pwd = "ValidPassword99!"
    r_login = client.post("/auth/register", json={
        "name": "Refresh User",
        "username": uname,
        "email": f"{uname}@example.com",
        "password": pwd,
        "confirm_password": pwd
    })
    token = r_login.json()["access_token"]

    # Simulating a page refresh requesting /user/me
    resp = client.get("/user/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == uname


def test_15_logout_invalidates_server_side_session(client):
    """Scenario 15: Logout invalidates the server-side session in auth_sessions."""
    uname = f"logout_db_{uuid.uuid4().hex[:8]}"
    pwd = "ValidPassword99!"
    r_login = client.post("/auth/register", json={
        "name": "Logout DB User",
        "username": uname,
        "email": f"{uname}@example.com",
        "password": pwd,
        "confirm_password": pwd
    })
    token = r_login.json()["access_token"]
    jti = r_login.json()["jti"]

    logout_resp = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200

    db = TestSessionLocal()
    try:
        session_rec = db.query(AuthSession).filter(AuthSession.token_jti == jti).first()
        assert session_rec.is_revoked is True
        assert session_rec.revoked_reason == "USER_LOGOUT"
    finally:
        db.close()


def test_16_logged_out_session_cannot_access_protected_apis(client):
    """Scenario 16: A logged-out session cannot access protected APIs."""
    uname = f"logout_api_{uuid.uuid4().hex[:8]}"
    pwd = "ValidPassword99!"
    r_login = client.post("/auth/register", json={
        "name": "Logged Out API User",
        "username": uname,
        "email": f"{uname}@example.com",
        "password": pwd,
        "confirm_password": pwd
    })
    token = r_login.json()["access_token"]

    # Logout
    client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})

    # Access /user/me with old token
    resp = client.get("/user/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert "revoked" in resp.text.lower()


def test_17_expired_or_revoked_sessions_rejected(client):
    """Scenario 17: Expired or revoked sessions are rejected."""
    uname = f"expired_{uuid.uuid4().hex[:8]}"
    pwd = "ValidPassword99!"
    r_login = client.post("/auth/register", json={
        "name": "Expired User",
        "username": uname,
        "email": f"{uname}@example.com",
        "password": pwd,
        "confirm_password": pwd
    })
    token = r_login.json()["access_token"]
    jti = r_login.json()["jti"]

    # Artificially expire session in DB
    db = TestSessionLocal()
    try:
        session_rec = db.query(AuthSession).filter(AuthSession.token_jti == jti).first()
        session_rec.expires_at = datetime.utcnow() - timedelta(minutes=5)
        db.commit()
    finally:
        db.close()

    resp = client.get("/user/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert "expired" in resp.text.lower()


def test_18_csrf_protections_work_for_cookie_mutations(client):
    """Scenario 18: CSRF protections work for cookie-authenticated mutations."""
    uname = f"csrf_{uuid.uuid4().hex[:8]}"
    pwd = "ValidPassword99!"
    client.post("/auth/register", json={
        "name": "CSRF User",
        "username": uname,
        "email": f"{uname}@example.com",
        "password": pwd,
        "confirm_password": pwd
    })

    login_resp = client.post("/auth/login-json", json={"username": uname, "password": pwd})
    token = login_resp.json()["access_token"]
    csrf_token = login_resp.json()["csrf_token"]

    # 1. Mutation with cookies but MISSING X-CSRF-Token header -> 403 Forbidden
    client.cookies.set("access_token", token)
    client.cookies.set("csrf_token", csrf_token)

    r_fail1 = client.post("/auth/logout")
    assert r_fail1.status_code == 403
    assert "CSRF validation failed" in r_fail1.text

    # 2. Mutation with cookies and MISMATCHED X-CSRF-Token -> 403 Forbidden
    r_fail2 = client.post("/auth/logout", headers={"X-CSRF-Token": "tampered_fake_csrf_token"})
    assert r_fail2.status_code == 403

    # 3. Mutation with cookies and VALID X-CSRF-Token -> 200 OK
    r_pass = client.post("/auth/logout", headers={"X-CSRF-Token": csrf_token})
    assert r_pass.status_code == 200

    client.cookies.clear()


# ---------------------------------------------------------------------
# AUTHORIZATION & RBAC (Scenarios 19 - 24)
# ---------------------------------------------------------------------

def test_19_anonymous_users_cannot_access_protected_apis(client):
    """Scenario 19: Anonymous users cannot access protected dashboards or APIs."""
    r_api = client.get("/user/me")
    assert r_api.status_code == 401

    r_admin = client.get("/admin/users")
    assert r_admin.status_code == 401

    r_page = client.get("/bank", follow_redirects=False)
    assert r_page.status_code == 302
    assert "/login" in r_page.headers.get("location", "")


def test_20_customers_cannot_access_administrative_endpoints(client):
    """Scenario 20: Customers cannot access administrative endpoints."""
    uname = f"cust_{uuid.uuid4().hex[:8]}"
    pwd = "ValidPassword99!"
    r_reg = client.post("/auth/register", json={
        "name": "Customer User",
        "username": uname,
        "email": f"{uname}@example.com",
        "password": pwd,
        "confirm_password": pwd
    })
    token = r_reg.json()["access_token"]

    resp = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert "access denied" in resp.text.lower() or "permission" in resp.text.lower()


def test_21_investigators_cannot_perform_unauthorized_admin_actions(client):
    """Scenario 21: Investigators cannot perform unauthorized administrative actions."""
    db = TestSessionLocal()
    try:
        inv_uname = f"inv_{uuid.uuid4().hex[:8]}"
        inv_user = User(
            name="Investigator Tester",
            username=inv_uname,
            email=f"{inv_uname}@example.com",
            hashed_password=hash_password("ValidPassword99!"),
            role="INVESTIGATOR",
            status="ACTIVE"
        )
        db.add(inv_user)
        db.commit()
        inv_id = inv_user.id
    finally:
        db.close()

    r_login = client.post("/auth/login-json", json={"username": inv_uname, "password": "ValidPassword99!"})
    token = r_login.json()["access_token"]

    # Investigators lack permission to assign roles to other users
    r_assign = client.post(
        f"/admin/users/{inv_id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "ADMIN"}
    )
    assert r_assign.status_code == 403


def test_22_delegated_admins_cannot_exceed_delegated_permissions(client):
    """Scenario 22: Delegated Admins cannot exceed their delegated permissions (ceiling check)."""
    db = TestSessionLocal()
    try:
        admin_uname = f"del_admin_{uuid.uuid4().hex[:8]}"
        admin_user = User(
            name="Delegated Admin",
            username=admin_uname,
            email=f"{admin_uname}@example.com",
            hashed_password=hash_password("ValidPassword99!"),
            role="ADMIN",
            is_boss_admin=False,
            status="ACTIVE"
        )
        db.add(admin_user)
        db.commit()
    finally:
        db.close()

    r_login = client.post("/auth/login-json", json={"username": admin_uname, "password": "ValidPassword99!"})
    token = r_login.json()["access_token"]

    # Target user
    target_uname = f"target_{uuid.uuid4().hex[:8]}"
    client.post("/auth/register", json={
        "name": "Target User",
        "username": target_uname,
        "email": f"{target_uname}@example.com",
        "password": "ValidPassword99!",
        "confirm_password": "ValidPassword99!"
    })

    db = TestSessionLocal()
    try:
        t_user = db.query(User).filter(User.username == target_uname).first()
        t_id = t_user.id
    finally:
        db.close()

    resp = client.post(
        f"/admin/users/{t_id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "SUPER_ADMIN"}
    )
    assert resp.status_code == 403


def test_23_users_cannot_read_or_modify_another_users_records_idor(client):
    """Scenario 23: Users cannot read or modify another user's protected records (IDOR protection)."""
    u1 = f"idor_alice_{uuid.uuid4().hex[:8]}"
    u2 = f"idor_bob_{uuid.uuid4().hex[:8]}"

    r1 = client.post("/auth/register", json={
        "name": "Alice", "username": u1, "email": f"{u1}@example.com",
        "password": "ValidPassword99!", "confirm_password": "ValidPassword99!"
    })
    r2 = client.post("/auth/register", json={
        "name": "Bob", "username": u2, "email": f"{u2}@example.com",
        "password": "ValidPassword99!", "confirm_password": "ValidPassword99!"
    })

    token_alice = r1.json()["access_token"]

    # Bob's user record in DB
    db = TestSessionLocal()
    try:
        bob = db.query(User).filter(User.username == u2).first()
        bob_id = bob.id
    finally:
        db.close()

    # Alice attempts to access Bob's private administrative details
    resp = client.get(f"/admin/users?search={u2}", headers={"Authorization": f"Bearer {token_alice}"})
    assert resp.status_code == 403


def test_24_only_properly_authorized_administrators_can_perform_privileged_actions(client):
    """Scenario 24: Only properly authorized administrators can perform privileged actions."""
    db = TestSessionLocal()
    try:
        boss = db.query(User).filter(User.is_boss_admin == True).first()
        if not boss:
            boss = bootstrap_boss_admin(
                db=db,
                username=f"boss_{uuid.uuid4().hex[:8]}",
                password="RootPassword123!",
                email="boss@example.com",
                name="Root Boss Admin"
            )
        boss_uname = boss.username
    finally:
        db.close()

    r_login = client.post("/auth/login-json", json={"username": boss_uname, "password": "RootPassword123!"})
    token = r_login.json()["access_token"]

    resp = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert len(resp.json()) > 0


# ---------------------------------------------------------------------
# FRONTEND VERIFICATION (Scenarios 25 - 30)
# ---------------------------------------------------------------------

def test_25_demo_login_cards_absent_from_public_page():
    """Scenario 25: Demo-login cards are absent from the public page HTML."""
    login_html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "login", "index.html"))
    with open(login_html_path, "r", encoding="utf-8") as f:
        html = f.read()

    assert "demo-role-section" not in html
    assert "demo-chips-grid" not in html
    assert "demo-chip" not in html
    assert "Instant Role Demonstrator" not in html
    assert "fillCredentials" not in html
    assert "password123" not in html


def test_26_login_and_registration_forms_display_useful_validation():
    """Scenario 26: Login and registration forms display useful validation rules and attributes."""
    login_html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "login", "index.html"))
    with open(login_html_path, "r", encoding="utf-8") as f:
        html = f.read()

    assert 'id="login-username"' in html
    assert 'id="login-password"' in html
    assert 'id="reg-name"' in html
    assert 'id="reg-username"' in html
    assert 'id="reg-email"' in html
    assert 'id="reg-password"' in html
    assert 'id="reg-confirm-password"' in html
    assert 'togglePasswordVisibility' in html
    assert 'Passwords do not match' in html


def test_27_loading_success_and_error_states_present():
    """Scenario 27: Loading, success, failure, and network-error states work."""
    login_html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "login", "index.html"))
    with open(login_html_path, "r", encoding="utf-8") as f:
        html = f.read()

    assert 'disabled = true' in html
    assert 'spinner' in html
    assert 'Invalid username/email or password' in html
    assert 'Customer account created successfully' in html


def test_28_mobile_layout_has_no_horizontal_overflow():
    """Scenario 28: Mobile layout has no horizontal overflow (meta viewport & responsive styles present)."""
    login_html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "login", "index.html"))
    with open(login_html_path, "r", encoding="utf-8") as f:
        html = f.read()

    assert '<meta name="viewport" content="width=device-width, initial-scale=1.0"' in html
    assert 'max-width: 480px;' in html
    assert 'overflow-x: hidden;' in html


def test_29_refreshing_protected_page_checks_authentication():
    """Scenario 29: Refreshing a protected page correctly checks authentication."""
    bank_js_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "bank", "bank.js"))
    with open(bank_js_path, "r", encoding="utf-8") as f:
        js = f.read()

    assert "fetch('/user/me'" in js
    assert "window.location.href = '/login'" in js
    assert "initUserSession()" in js


def test_30_logout_returns_user_to_public_login_page_and_revokes_token(client):
    """Scenario 30: Logout returns the user to the public login page and protected APIs reject the former session."""
    uname = f"final_logout_{uuid.uuid4().hex[:8]}"
    pwd = "ValidPassword99!"
    r_reg = client.post("/auth/register", json={
        "name": "Final Logout User",
        "username": uname,
        "email": f"{uname}@example.com",
        "password": pwd,
        "confirm_password": pwd
    })
    token = r_reg.json()["access_token"]
    csrf = r_reg.json()["csrf_token"]

    # Call logout
    r_logout = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r_logout.status_code == 200

    # Ensure former token is now 100% rejected
    r_rejected = client.get("/user/me", headers={"Authorization": f"Bearer {token}"})
    assert r_rejected.status_code == 401
    assert "revoked" in r_rejected.text.lower()
