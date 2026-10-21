# =====================================================================
# GREEN-FINANCE — TEST_SEC_FINANCIAL.PY
# Purpose: Comprehensive security acceptance tests for banking engine:
#          - FIN-01: Anonymous transfer attempt rejected (401)
#          - FIN-02: Spoofed source bank account rejected (403)
#          - FIN-03: Zero or negative transfer amount rejected (422/400)
#          - FIN-04: Idempotency-Key deduplication prevents double-spending
#          - FIN-05: Overdraft attempt rejected (400)
#          - FIN-06: Cryptographic SHA-256 hash chaining integrity
#          - FIN-07: Double-entry balanced invariant (DR = CR)
# =====================================================================

import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.session import SessionLocal
from backend.models.user import User
from backend.models.account import Account
from backend.models.transaction import Transaction
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


def test_fin_01_anonymous_transfer_rejected(client):
    """Anonymous transfer request must receive HTTP 401 Unauthorized."""
    resp = client.post("/payment/transfer", json={
        "source_account": "DEMO0001",
        "destination_account": "MAH123",
        "amount": 500.0
    })
    assert resp.status_code == 401


def test_fin_02_spoofed_source_bank_id_rejected(client):
    """User cannot transfer funds out of an account that does not belong to them (403)."""
    alice_token = get_token(client, "alice_smith")  # Alice's bank ID is ALICE101

    # Alice attempts to transfer funds out of DEMO0001 (Demo User)
    resp = client.post(
        "/payment/transfer",
        json={
            "source_account": "DEMO0001",
            "destination_account": "MAH123",
            "amount": 250.0
        },
        headers={"Authorization": f"Bearer {alice_token}"}
    )
    assert resp.status_code == 403
    err = resp.json().get("error") or resp.json().get("detail", "")
    assert "access denied" in err.lower() or "cannot transfer" in err.lower()


def test_fin_03_zero_or_negative_amount_rejected(client):
    """Negative and zero transfer amounts must be rejected."""
    alice_token = get_token(client, "alice_smith")

    # 1. Negative amount
    resp1 = client.post(
        "/payment/transfer",
        json={
            "source_account": "ALICE101",
            "destination_account": "MAH123",
            "amount": -50.0
        },
        headers={"Authorization": f"Bearer {alice_token}"}
    )
    assert resp1.status_code in (400, 422)

    # 2. Zero amount
    resp2 = client.post(
        "/payment/transfer",
        json={
            "source_account": "ALICE101",
            "destination_account": "MAH123",
            "amount": 0.0
        },
        headers={"Authorization": f"Bearer {alice_token}"}
    )
    assert resp2.status_code in (400, 422)


def test_fin_04_idempotency_key_deduplication(client):
    """
    Submitting the same transfer twice with the same Idempotency-Key
    must execute the debit only ONCE and return the identical response.
    """
    alice_token = get_token(client, "alice_smith")
    idempotency_key = f"IDEMP-{uuid.uuid4().hex}"

    db = SessionLocal()
    try:
        alice = db.query(User).filter(User.username == "alice_smith").first()
        acc = db.query(Account).filter(Account.user_id == alice.id, Account.name == "cash_wallet").first()
        initial_balance = acc.balance
    finally:
        db.close()

    transfer_amt = 150.0

    # 1. First execution
    resp1 = client.post(
        "/payment/transfer",
        json={
            "source_account": "ALICE101",
            "destination_account": "MAH123",
            "amount": transfer_amt,
            "note": "Idempotent payment test"
        },
        headers={
            "Authorization": f"Bearer {alice_token}",
            "Idempotency-Key": idempotency_key
        }
    )
    assert resp1.status_code == 200, resp1.text
    tx_id_1 = resp1.json()["transaction_id"]

    # 2. Second execution (replay with same idempotency key)
    resp2 = client.post(
        "/payment/transfer",
        json={
            "source_account": "ALICE101",
            "destination_account": "MAH123",
            "amount": transfer_amt,
            "note": "Idempotent payment test"
        },
        headers={
            "Authorization": f"Bearer {alice_token}",
            "Idempotency-Key": idempotency_key
        }
    )
    assert resp2.status_code == 200, resp2.text
    tx_id_2 = resp2.json()["transaction_id"]

    # Response must match first transaction ID
    assert tx_id_1 == tx_id_2

    # Verify balance was debited ONLY ONCE
    db = SessionLocal()
    try:
        acc_after = db.query(Account).filter(Account.user_id == alice.id, Account.name == "cash_wallet").first()
        expected_balance = initial_balance - transfer_amt
        assert abs(acc_after.balance - expected_balance) < 1e-4, f"Double-spend detected! Balance: {acc_after.balance}, Expected: {expected_balance}"
    finally:
        db.close()


def test_fin_05_overdraft_attempt_rejected(client):
    """Transfer exceeding available balance must fail with HTTP 400 Insufficient balance."""
    bob_token = get_token(client, "bob_kumar")

    resp = client.post(
        "/payment/transfer",
        json={
            "source_account": "BOB202",
            "destination_account": "MAH123",
            "amount": 99999999.0  # Far exceeds balance
        },
        headers={"Authorization": f"Bearer {bob_token}"}
    )
    assert resp.status_code == 400
    err = resp.json().get("error") or resp.json().get("detail", "")
    assert "insufficient balance" in err.lower()


def test_fin_06_sha256_hash_chaining_integrity(client):
    """
    Two sequential transactions must create an unbroken cryptographic SHA-256 chain:
    tx2.prev_audit_hash == tx1.audit_hash
    """
    demo_token = get_token(client, "demo_user")

    # First transaction
    resp1 = client.post(
        "/payment/transfer",
        json={
            "source_account": "DEMO0001",
            "destination_account": "MAH123",
            "amount": 100.0,
            "note": "Chain Tx 1"
        },
        headers={"Authorization": f"Bearer {demo_token}"}
    )
    assert resp1.status_code == 200, resp1.text
    hash1 = resp1.json()["audit_hash"]
    assert hash1 is not None and len(hash1) == 64

    # Second transaction
    resp2 = client.post(
        "/payment/transfer",
        json={
            "source_account": "DEMO0001",
            "destination_account": "IDF892",
            "amount": 120.0,
            "note": "Chain Tx 2"
        },
        headers={"Authorization": f"Bearer {demo_token}"}
    )
    assert resp2.status_code == 200, resp2.text
    prev_hash_2 = resp2.json()["prev_audit_hash"]
    hash2 = resp2.json()["audit_hash"]

    # Verify cryptographic link
    assert prev_hash_2 == hash1, f"Hash chain broken! Expected prev {hash1}, got {prev_hash_2}"
    assert hash2 is not None and len(hash2) == 64
    assert hash2 != hash1


def test_fin_07_double_entry_balanced_invariant(client):
    """
    After a transfer, total change in sender cash must equal total change in recipient cash.
    """
    db = SessionLocal()
    try:
        sender_user = db.query(User).filter(User.username == "demo_user").first()
        recip_user = db.query(User).filter(User.username == "bank_mah123").first()
        s_acc = db.query(Account).filter(Account.user_id == sender_user.id, Account.name == "cash_wallet").first()
        r_acc = db.query(Account).filter(Account.user_id == recip_user.id, Account.name == "cash_wallet").first()
        s_before = s_acc.balance
        r_before = r_acc.balance
    finally:
        db.close()

    demo_token = get_token(client, "demo_user")
    amt = 200.0
    resp = client.post(
        "/payment/transfer",
        json={
            "source_account": "DEMO0001",
            "destination_account": "MAH123",
            "amount": amt,
            "note": "Double-entry integrity verification"
        },
        headers={"Authorization": f"Bearer {demo_token}"}
    )
    assert resp.status_code == 200, resp.text

    db = SessionLocal()
    try:
        s_acc = db.query(Account).filter(Account.user_id == sender_user.id, Account.name == "cash_wallet").first()
        r_acc = db.query(Account).filter(Account.user_id == recip_user.id, Account.name == "cash_wallet").first()
        s_delta = s_before - s_acc.balance
        r_delta = r_acc.balance - r_before
        assert abs(s_delta - amt) < 1e-4, f"Sender balance delta {s_delta} != transfer amount {amt}"
        assert abs(r_delta - amt) < 1e-4, f"Recipient balance delta {r_delta} != transfer amount {amt}"
    finally:
        db.close()
