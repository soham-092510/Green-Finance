# =====================================================================
# GREEN-FINANCE — TEST_SEC_INJECTION.PY
# Purpose: Automated security regression tests verifying:
#          - INJ-01: Path traversal protection on static file routes
#          - INJ-02: Security headers presence (CSP, X-Frame-Options, No-Sniff)
#          - INJ-03: PromQL internal proxy access restrictions
#          - UI-02: Safe custom error format without traceback leaks
# =====================================================================

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.security import create_access_token


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_inj_01_path_traversal_dot_dot_slash_rejected(client):
    """Ensures ../../.env requests cannot escape the frontend root directory."""
    traversal_paths = [
        "/shared/..%2F..%2F.env",
        "/shared/../../.env",
        "/bank/..%2F..%2Frender.yaml",
        "/investigator/..%2F..%2Fbackend/core/config.py",
        "/grafana/..%2F..%2Ftest.db",
    ]
    for path in traversal_paths:
        response = client.get(path)
        assert response.status_code == 404, f"Path traversal succeeded on {path} with status {response.status_code}"
        assert "JWT_SECRET" not in response.text
        assert "database_url" not in response.text


def test_inj_02_security_headers_present(client):
    """Verifies all mandatory defense-in-depth security headers are attached."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    
    csp = response.headers.get("content-security-policy", "")
    assert "frame-ancestors 'none'" in csp
    assert "default-src 'self'" in csp


def test_inj_03_promql_requires_admin_role(client):
    """Ensures regular customers cannot execute raw PromQL queries."""
    # 1. Unauthenticated request rejected with 401
    resp_unauth = client.get("/telemetry/promql?query=up")
    assert resp_unauth.status_code == 401

    # 2. Regular customer token rejected with 403
    customer_token = create_access_token(data={"sub": "alice_smith", "role": "USER"})
    headers = {"Authorization": f"Bearer {customer_token}"}
    resp_customer = client.get("/telemetry/promql?query=up", headers=headers)
    assert resp_customer.status_code == 403
    assert "Access denied" in resp_customer.text


def test_inj_04_safe_error_formatting_no_stack_traces(client):
    """Verifies 404 and unhandled errors return clean JSON without internal path disclosure."""
    response = client.get("/non-existent-api-path-404")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data or "detail" in data
    assert "Traceback" not in response.text
    assert "Traceback (most recent call last)" not in response.text
