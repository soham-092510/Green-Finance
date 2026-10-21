# =====================================================================
# GREEN-FINANCE — TEST_SEC_TELEMETRY.PY
# Purpose: Security acceptance tests for Telemetry, Sustainability, and Baseline:
#          - TEL-01: Anonymous request to baseline calibration rejected (401)
#          - TEL-02: Customer cannot lock baseline profile (403)
#          - TEL-03: Customer cannot execute accuracy validation run (403)
#          - TEL-04: Customer cannot activate regional carbon factor (403)
#          - TEL-05: CSV audit report sanitizes spreadsheet formula injection
#          - TEL-06: Telemetry mode for simulated estimates is never labeled OBSERVED
# =====================================================================

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.session import SessionLocal
from backend.api.sustainability import sanitize_csv_cell
from backend.services import telemetry_service
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


def test_tel_01_anonymous_baseline_rejected(client):
    """Anonymous request to /baseline/start must be rejected (401)."""
    resp = client.post("/baseline/start", json={"duration_seconds": 10})
    assert resp.status_code == 401


def test_tel_02_customer_cannot_lock_baseline(client):
    """Customer role cannot lock baseline profile (403). Super Admin can."""
    customer_token = get_token(client, "demo_user")
    resp_cust = client.post("/baseline/lock", headers={"Authorization": f"Bearer {customer_token}"})
    assert resp_cust.status_code == 403

    boss_token = get_token(client, "soham_gaikwad")
    resp_boss = client.post("/baseline/lock", headers={"Authorization": f"Bearer {boss_token}"})
    assert resp_boss.status_code == 200
    assert resp_boss.json()["status"] == "LOCKED"


def test_tel_03_customer_cannot_run_accuracy_validation(client):
    """Customer role cannot execute accuracy validation cycle (403)."""
    customer_token = get_token(client, "demo_user")
    resp = client.post(
        "/accuracy/run-validation",
        json={"tx_count": 100, "host_joules": 1000.0, "container_joules": 800.0},
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert resp.status_code == 403


def test_tel_04_customer_cannot_activate_carbon_factor(client):
    """Customer cannot activate regional carbon factor (403)."""
    customer_token = get_token(client, "demo_user")
    resp = client.post(
        "/sustainability/carbon-factors/test-factor-id/activate",
        headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert resp.status_code == 403


def test_tel_05_csv_formula_injection_defense():
    """CSV cells beginning with formula trigger characters (=, +, -, @) must be escaped."""
    malicious_inputs = [
        "=CMD|' /C calc'!A0",
        "+1+2+cmd|' /C calc'!A0",
        "-2+3+cmd|' /C calc'!A0",
        "@SUM(1,2)*cmd|' /C calc'!A0",
        "\t=2+5",
        "\r=1+1"
    ]
    for payload in malicious_inputs:
        sanitized = sanitize_csv_cell(payload)
        assert sanitized.startswith("'"), f"Payload {payload} was not sanitized! Got: {sanitized}"

    # Benign text should remain unescaped
    benign_text = "HDFC9999"
    assert sanitize_csv_cell(benign_text) == "HDFC9999"


def test_tel_06_simulated_telemetry_never_labeled_observed():
    """Fallback simulated metrics must report telemetry_mode == 'SIMULATED' and not 'OBSERVED'."""
    metrics = telemetry_service.get_realtime_metrics()
    assert "telemetry_mode" in metrics
    if metrics["kepler_available"] is False:
        assert metrics["telemetry_mode"] == "SIMULATED", f"Unobserved telemetry mode mislabeled: {metrics['telemetry_mode']}"
