# =====================================================================
# GREEN-FINANCE — TEST_SEC_RBAC.PY
# Purpose: Comprehensive security acceptance tests for Hierarchical RBAC,
#          Delegation Ceilings, Investigator Case Workflows, and Invariants:
#          - RBAC-01: Customer cannot access administrative user endpoints (403)
#          - RBAC-02: Customer cannot view security audit event logs (403)
#          - RBAC-03: Customer cannot mint carbon credits (403); Admin can
#          - RBAC-04: Investigator cannot access unassigned investigation case (403)
#          - RBAC-05: Investigator can view and update assigned case
#          - RBAC-06: Delegated Admin cannot grant SUPER_ADMIN (403)
#          - RBAC-07: Delegated Admin cannot delegate permissions beyond ceiling (403)
#          - RBAC-08: Subordinate Admin cannot suspend Boss Admin (403)
#          - RBAC-09: One-time Boss Admin bootstrap invariant fails closed (409)
# =====================================================================

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.session import SessionLocal
from backend.models.user import User
from backend.models.rbac import InvestigationCase, InvestigationAssignment
from backend.services.rbac_service import bootstrap_boss_admin
from backend.middleware.rate_limit import limiter
from fastapi import HTTPException


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Resets rate limit counters before each test run."""
    limiter.reset()


def get_token(client, username, password="password123"):
    resp = client.post("/auth/login-json", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["access_token"]


def test_rbac_01_customer_cannot_access_admin_users(client):
    """Customer must be denied access to /admin/users with 403 Forbidden."""
    token = get_token(client, "demo_user")
    resp = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert "Access denied" in resp.text or "Permission Denied" in resp.text


def test_rbac_02_customer_cannot_view_audit_events(client):
    """Customer must be denied access to /admin/audit-events with 403 Forbidden."""
    token = get_token(client, "demo_user")
    resp = client.get("/admin/audit-events", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_rbac_03_customer_cannot_mint_credits_but_superadmin_can(client):
    """Customer gets 403 trying to mint credits; Super Admin succeeds."""
    customer_token = get_token(client, "demo_user")
    mint_payload = {
        "credit_type": "solar",
        "amount": 100.0,
        "source": "Rooftop Solar Project A",
        "vintage_year": 2024,
        "serial_number": "VCS-2024-SOLAR-001"
    }
    resp = client.post("/credits/mint", json=mint_payload, headers={"Authorization": f"Bearer {customer_token}"})
    assert resp.status_code == 403

    # Super Admin can mint
    boss_token = get_token(client, "soham_gaikwad")
    resp_boss = client.post("/credits/mint", json=mint_payload, headers={"Authorization": f"Bearer {boss_token}"})
    assert resp_boss.status_code in (200, 201), resp_boss.text


def test_rbac_04_investigator_unassigned_case_access_denied(client):
    """Investigator cannot access a case that is not assigned to them (403)."""
    boss_token = get_token(client, "soham_gaikwad")
    investigator_token = get_token(client, "investigator_rahul")

    # 1. Admin/Boss creates a new case
    case_resp = client.post(
        "/cases",
        json={
            "title": "Suspicious Energy Anomaly at Server Farm",
            "severity": "HIGH",
            "evidence_notes": "Unusual power spike detected during low-traffic window."
        },
        headers={"Authorization": f"Bearer {boss_token}"}
    )
    assert case_resp.status_code == 200, case_resp.text
    case_id = case_resp.json()["case_id"]

    # 2. Investigator tries to view unassigned case -> 403 Forbidden
    view_resp = client.get(f"/cases/{case_id}", headers={"Authorization": f"Bearer {investigator_token}"})
    assert view_resp.status_code == 403
    err = view_resp.json().get("error") or view_resp.json().get("detail", "")
    assert "not assigned" in err.lower() or "denied" in err.lower()


def test_rbac_05_investigator_assigned_case_lifecycle(client):
    """Investigator can view and submit findings for a case once assigned."""
    boss_token = get_token(client, "soham_gaikwad")
    investigator_token = get_token(client, "investigator_rahul")

    db = SessionLocal()
    try:
        rahul = db.query(User).filter(User.username == "investigator_rahul").first()
        rahul_id = rahul.id
    finally:
        db.close()

    # 1. Create case
    case_resp = client.post(
        "/cases",
        json={"title": "Grid Carbon Anomaly", "severity": "MEDIUM"},
        headers={"Authorization": f"Bearer {boss_token}"}
    )
    case_id = case_resp.json()["case_id"]

    # 2. Assign to investigator rahul
    assign_resp = client.post(
        f"/cases/{case_id}/assign",
        json={"investigator_id": rahul_id},
        headers={"Authorization": f"Bearer {boss_token}"}
    )
    assert assign_resp.status_code == 200

    # 3. Investigator can now view details
    view_resp = client.get(f"/cases/{case_id}", headers={"Authorization": f"Bearer {investigator_token}"})
    assert view_resp.status_code == 200
    assert view_resp.json()["id"] == case_id

    # 4. Investigator updates findings
    findings_resp = client.post(
        f"/cases/{case_id}/findings",
        json={
            "findings": "Verified meter hardware malfunction; grid factor reassigned to regional standard.",
            "status": "RESOLVED"
        },
        headers={"Authorization": f"Bearer {investigator_token}"}
    )
    assert findings_resp.status_code == 200


def test_rbac_06_delegated_admin_cannot_grant_super_admin(client):
    """Delegated Admin attempting to grant SUPER_ADMIN role must be rejected (403)."""
    admin_token = get_token(client, "admin_priya")

    db = SessionLocal()
    try:
        bob = db.query(User).filter(User.username == "bob_kumar").first()
        bob_id = bob.id
    finally:
        db.close()

    resp = client.post(
        f"/admin/users/{bob_id}/role",
        json={"role": "SUPER_ADMIN"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 403
    err = resp.json().get("error") or resp.json().get("detail", "")
    assert "boss admin" in err.lower() or "denied" in err.lower()


def test_rbac_07_delegated_admin_ceiling_enforcement(client):
    """Admin cannot delegate permissions they do not have themselves."""
    admin_token = get_token(client, "admin_priya")

    db = SessionLocal()
    try:
        bob = db.query(User).filter(User.username == "bob_kumar").first()
        bob_id = bob.id
    finally:
        db.close()

    # admin_priya does NOT have "credits.mint"
    resp = client.post(
        "/admin/delegate",
        json={
            "delegatee_id": bob_id,
            "permission_code": "credits.mint"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 403
    err = resp.json().get("error") or resp.json().get("detail", "")
    assert "ceiling exceeded" in err.lower() or "cannot delegate" in err.lower()


def test_rbac_08_subordinate_admin_cannot_suspend_boss_admin(client):
    """Subordinate Admin cannot suspend the root Boss Admin."""
    admin_token = get_token(client, "admin_priya")

    db = SessionLocal()
    try:
        boss = db.query(User).filter((User.is_boss_admin == True) | (User.role == "SUPER_ADMIN")).first()
        assert boss is not None, "Boss admin must exist"
        boss_id = boss.id
    finally:
        db.close()

    resp = client.post(
        f"/admin/users/{boss_id}/suspend",
        json={"reason": "Attempted hostile takeover"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 403
    err = resp.json().get("error") or resp.json().get("detail", "")
    assert "boss admin" in err.lower() or "cannot be suspended" in err.lower()


def test_rbac_09_boss_admin_bootstrap_invariant_fails_closed():
    """Attempting repeated bootstrap_boss_admin must raise HTTP 409 Conflict."""
    db = SessionLocal()
    try:
        with pytest.raises(HTTPException) as exc_info:
            bootstrap_boss_admin(
                db=db,
                username="imposter_boss",
                password="AnotherPassword123!",
                email="imposter@test.dev"
            )
        assert exc_info.value.status_code == 409
        assert "already been bootstrapped" in exc_info.value.detail
    finally:
        db.close()
