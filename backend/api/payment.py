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

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.db.session import get_db
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
    db: Session = Depends(get_db)
):
    """
    Executes an atomic bank transfer with double-entry ledger bookkeeping.
    Captures container energy, attributes carbon, records SHA-256 audit hash,
    and streams telemetry trace to Green-Finance-2 in real time.
    """
    return payment_service.execute_bank_transfer(
        db=db,
        source_bank_id=payload.source_account,
        dest_bank_id=payload.destination_account,
        amount=payload.amount,
        currency=payload.currency,
        note=payload.note or "Inter-bank fund settlement"
    )


@router.post(
    "/stimulate",
    response_model=StimulateResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate concurrent user transactions (10 users workload generator)"
)
def stimulate_traffic(
    payload: StimulateRequest,
    db: Session = Depends(get_db)
):
    """
    Simulates concurrent transactions originating from up to 10 active banking users.
    Generates real backend workload, commits double-entry transactions, and streams
    live telemetry traces to the Green-Finance-2 Enterprise Platform.
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
    db: Session = Depends(get_db)
):
    """
    Executes a batch of N identical transactions to profile measurement repeatability (target CV <= 5%).
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
def get_accounts(db: Session = Depends(get_db)):
    """
    Returns registered bank accounts (HDFC9999, MAH123, IDF892, SBIN456) with current balances.
    """
    return payment_service.list_bank_accounts(db=db)


@router.get(
    "/transactions",
    summary="Get recent audited bank transactions"
)
def get_recent_transactions(limit: int = 25, db: Session = Depends(get_db)):
    """
    Returns recent audited transactions with telemetry annotations.
    """
    return payment_service.list_recent_transactions(db=db, limit=limit)


@router.get(
    "/transactions/{transaction_id}",
    summary="Get full audited transaction detail with telemetry"
)
def get_transaction_detail(transaction_id: str, db: Session = Depends(get_db)):
    """
    Returns detailed audit log for an individual transaction, including microservice call path,
    duration latency, energy breakdown, and cryptographic SHA-256 digest.
    """
    return payment_service.get_transaction_by_id(db=db, transaction_id=transaction_id)
