# =====================================================================
# ECO MONITOR / GREEN-FINANCE — PAYMENT.PY (API ROUTER)
# Purpose: Endpoints for Simulated Banking Microservices:
#          - POST /payment/transfer: Atomic double-entry transfer (DR = CR)
#          - POST /payment/stimulate: Simulate multi-user concurrent traffic
#          - POST /payment/benchmark: Batch standardized transfers (CV <= 5%)
#          - GET /payment/accounts: List active bank accounts and balances
#          - GET /payment/transactions: Recent audited transactions
#          - GET /payment/transactions/{transaction_id}: Detailed transaction lookup
# =====================================================================

from fastapi import APIRouter, Depends, status, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from backend.db.session import get_db
from backend.core.dependencies import get_current_user, require_permission
from backend.models.user import User
from backend.schemas.payment_schema import (
    BankTransferRequest,
    BankTransferResponse,
    BenchmarkRequest,
    BenchmarkResponse,
    BankAccountResponse,
    StimulateRequest,
    StimulateResponse
)
from backend.services import payment_service

router = APIRouter(prefix="/payment", tags=["Simulated Banking Services"])


@router.post(
    "/transfer",
    response_model=BankTransferResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute atomic inter-bank payment transfer"
)
def transfer_funds(
    payload: BankTransferRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Executes an atomic bank transfer with double-entry ledger bookkeeping.
    Guarantees authorization, idempotency, SHA-256 hash chaining, and single-commit rollback.
    Captures container energy, attributes carbon, and streams telemetry trace in real time.
    """
    return payment_service.execute_bank_transfer(
        db=db,
        source_bank_id=payload.source_account,
        dest_bank_id=payload.destination_account,
        amount=payload.amount,
        currency=payload.currency,
        note=payload.note or "Inter-bank fund settlement",
        actor=current_user,
        idempotency_key=idempotency_key
    )


@router.post(
    "/stimulate",
    response_model=StimulateResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate concurrent user transactions (10 users workload generator)"
)
def stimulate_traffic(
    payload: StimulateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("telemetry.manage"))
):
    """
    Simulates concurrent transactions originating from up to 10 active banking users.
    Restricted to authorized operators/administrators.
    """
    return payment_service.simulate_concurrent_workload(
        db=db,
        user_count=payload.user_count,
        tx_count=payload.tx_count,
        min_amount=payload.min_amount,
        max_amount=payload.max_amount
    )


@router.post(
    "/benchmark",
    response_model=BenchmarkResponse,
    status_code=status.HTTP_200_OK,
    summary="Run standardized transaction benchmark (Repeatability CV Test)"
)
def run_benchmark(
    payload: BenchmarkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("telemetry.manage"))
):
    """
    Executes a batch of N identical transactions to profile measurement repeatability (target CV <= 5%).
    Restricted to authorized operators/administrators.
    """
    return payment_service.run_benchmark_batch(
        db=db,
        count=payload.count,
        amount=payload.amount,
        source_bank_id=payload.source_account,
        dest_bank_id=payload.destination_account
    )


@router.get(
    "/accounts",
    response_model=List[BankAccountResponse],
    summary="List registered bank accounts and balances"
)
def get_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns accessible bank accounts with current balances.
    """
    return payment_service.list_bank_accounts(db=db, actor=current_user)


@router.get(
    "/transactions",
    summary="Get recent audited bank transactions"
)
def get_recent_transactions(
    limit: int = 25,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns recent audited transactions with telemetry annotations.
    """
    return payment_service.list_recent_transactions(db=db, limit=limit, actor=current_user)


@router.get(
    "/transactions/{transaction_id}",
    summary="Get full audited transaction detail with telemetry"
)
def get_transaction_detail(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns detailed audit log for an individual transaction, including microservice call path,
    duration latency, energy breakdown, and cryptographic SHA-256 digest.
    """
    return payment_service.get_transaction_by_id(db=db, transaction_id=transaction_id, actor=current_user)
