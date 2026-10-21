# =====================================================================
# GREEN-FINANCE — TEST_SEC_AUTH.PY
# Purpose: Automated security regression tests verifying:
#          - AUTH-01: Customer registration creates double-entry accounts
#          - AUTH-02: Public registration ignores caller-supplied roles
#          - AUTH-03: Generic login error prevents account enumeration
#          - AUTH-04: Argon2id password hashing validation
#          - AUTH-05: Anonymous access to protected routes rejected (401)
#          - AUTH-06: Session revocation on logout
#          - AUTH-07: Rate limiting throttles brute force (429)
# =====================================================================

import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.session import SessionLocal
from backend.models.user import User
from backend.models.account import Account
from backend.middleware.rate_limit import limiter


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Resets rate limit counters before each test run."""
    limiter.reset()


def test_auth_01_customer_registration_creates_accounts(client):
    """Ensures registration creates user with CUSTOMER role and default accounts."""
    username = f"user_{uuid.uuid4().hex[:8]}"
    email = f"{username}@test.dev"
    resp = client.post("/auth/register", json={
        "name": "Test Customer",
        "username": username,
        "email": email,
        "password": "SecurePassword123!"
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data

    # Verify database state
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        assert user is not None
        assert user.role == "CUSTOMER"
        assert user.is_boss_admin is False

        # Verify double-entry accounts created
        accounts = db.query(Account).filter(Account.user_id == user.id).all()
        acct_names = [a.name for a in accounts]
        assert "cash_wallet" in acct_names
        assert "carbon_asset" in acct_names
        assert "carbon_liability" in acct_names
    finally:
        db.close()


def test_auth_02_registration_cannot_self_appoint_admin(client):
    """Ensures caller cannot inject role='SUPER_ADMIN' via registration."""
    username = f"hacker_{uuid.uuid4().hex[:8]}"
    resp = client.post("/auth/register", json={
        "name": "Privilege Escalation Tester",
        "username": username,
        "email": f"{username}@test.dev",
        "password": "Password123!",
        "role": "SUPER_ADMIN"  # Attempt to escalate
    })
    assert resp.status_code == 201
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        assert user.role == "CUSTOMER", "User was able to choose their own role!"
        assert user.is_boss_admin is False
    finally:
        db.close()


def test_auth_03_generic_error_prevents_account_enumeration(client):
    """Ensures existing vs non-existing users receive identical 401 response."""
    # 1. Non-existent user
    resp1 = client.post("/auth/login-json", json={
        "username": "totally_non_existent_user_9999",
        "password": "any_password"
    })
    assert resp1.status_code == 401
    assert "Invalid username or password" in resp1.json().get("error", "")

    # 2. Existing user with wrong password
    resp2 = client.post("/auth/login-json", json={
        "username": "soham_gaikwad",
        "password": "completely_wrong_password_xyz"
    })
    assert resp2.status_code == 401
    assert "Invalid username or password" in resp2.json().get("error", "")


def test_auth_04_argon2id_password_hashing(client):
    """Verifies user passwords are saved using Argon2id."""
    username = f"argon_user_{uuid.uuid4().hex[:8]}"
    client.post("/auth/register", json={
        "name": "Argon Test",
        "username": username,
        "email": f"{username}@test.dev",
        "password": "TestArgonPassword123!"
    })

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        assert user.hashed_password.startswith("$argon2id$")
    finally:
        db.close()


def test_auth_05_anonymous_access_to_protected_route_rejected(client):
    """Verifies unauthenticated calls to /user/me return 401."""
    resp = client.get("/user/me")
    assert resp.status_code == 401


def test_auth_06_session_revocation_on_logout(client):
    """Verifies that calling /auth/logout immediately invalidates the active JWT session."""
    # 1. Register and log in
    username = f"logout_user_{uuid.uuid4().hex[:8]}"
    client.post("/auth/register", json={
        "name": "Logout Tester",
        "username": username,
        "email": f"{username}@test.dev",
        "password": "Password123!"
    })

    login_resp = client.post("/auth/login-json", json={
        "username": username,
        "password": "Password123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Access /user/me with valid token -> 200 OK
    me_resp = client.get("/user/me", headers=headers)
    assert me_resp.status_code == 200

    # 3. Call /auth/logout
    logout_resp = client.post("/auth/logout", headers=headers)
    assert logout_resp.status_code == 200

    # 4. Subsequent access with the same token must be rejected with 401
    revoked_resp = client.get("/user/me", headers=headers)
    assert revoked_resp.status_code == 401
    assert "revoked" in revoked_resp.text.lower()


def test_auth_07_rate_limiting_throttles_excessive_attempts(client):
    """Verifies that exceeding the 15 req/min auth quota triggers HTTP 429."""
    for i in range(15):
        resp = client.post("/auth/login-json", json={
            "username": "spam_bot",
            "password": f"wrong_{i}"
        })
        assert resp.status_code == 401

    # 16th request must trigger rate limit
    blocked_resp = client.post("/auth/login-json", json={
        "username": "spam_bot",
        "password": "wrong_16"
    })
    assert blocked_resp.status_code == 429
    assert blocked_resp.headers.get("retry-after") is not None
    assert "Too Many Requests" in blocked_resp.text
