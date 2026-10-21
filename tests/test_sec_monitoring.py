# =====================================================================
# GREEN-FINANCE — TEST_SEC_MONITORING.PY
# Purpose: Security acceptance tests for Operations Center & Monitoring:
#          - MON-01: Anonymous request to /operations/metrics rejected (401)
#          - MON-02: Customer role denied operational metrics (403); Admin can
#          - MON-03: Operational throughput rates structure verification
#          - MON-04: Health status liveness check returns 200
#          - MON-05: Static dashboard route /operations serves HTML safely
#          - MON-06: Static route /admin/super serves HTML safely
#          - MON-07: Custom 404 error page served on non-existent web paths
# =====================================================================

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.middleware.rate_limit import limiter


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


def test_mon_01_anonymous_operations_metrics_rejected(client):
    """Anonymous access to /operations/metrics must return 401 Unauthorized."""
    resp = client.get("/operations/metrics")
    assert resp.status_code == 401


def test_mon_02_customer_denied_operational_metrics(client):
    """Customer role is denied operational metrics with 403 Forbidden. Admin can access."""
    customer_token = get_token(client, "demo_user")
    resp_cust = client.get("/operations/metrics", headers={"Authorization": f"Bearer {customer_token}"})
    assert resp_cust.status_code == 403

    admin_token = get_token(client, "admin_priya")
    resp_admin = client.get("/operations/metrics", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_admin.status_code == 200
    data = resp_admin.json()
    assert "rates" in data
    assert "health" in data


def test_mon_03_operational_throughput_rates_structure(client):
    """Metrics payload must contain per-second rates and service health."""
    boss_token = get_token(client, "soham_gaikwad")
    resp = client.get("/operations/metrics", headers={"Authorization": f"Bearer {boss_token}"})
    assert resp.status_code == 200
    data = resp.json()
    rates = data["rates"]
    assert "transactions_per_sec" in rates
    assert "logins_per_sec" in rates
    assert "errors_4xx_per_sec" in rates
    assert "errors_5xx_per_sec" in rates
    assert data["health"]["api_server"] == "HEALTHY"


def test_mon_04_health_status_liveness_check(client):
    """Public /operations/health-status liveness endpoint returns UP with 200."""
    resp = client.get("/operations/health-status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "UP"
    assert data["security_mode"] == "RBAC_ENFORCED"


def test_mon_05_static_operations_dashboard_served(client):
    """Static route /operations serves HTML."""
    resp = client.get("/operations")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "OPERATIONS CENTER" in resp.text


def test_mon_06_static_admin_super_dashboard_served(client):
    """Static route /admin/super serves HTML."""
    resp = client.get("/admin/super")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")
    assert "ROOT BOSS ADMIN" in resp.text


def test_mon_07_custom_404_error_page_served(client):
    """Non-existent URL with text/html request returns custom 404 HTML."""
    resp = client.get("/non-existent-page-url-xyz", headers={"Accept": "text/html,application/xhtml+xml"})
    assert resp.status_code == 404
    assert "Resource Not Found" in resp.text
