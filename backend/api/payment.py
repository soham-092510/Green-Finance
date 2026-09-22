# =====================================================================
# ECO MONITOR / GREEN-FINANCE — PAYMENT.PY (API ROUTER)
# Purpose: Endpoints for Simulated Banking Microservices:
#          - POST /payment/transfer: Atomic double-entry transfer (DR = CR)
#          - POST /payment/benchmark: Batch standardized transfers (repeatability test)
#          - GET /payment/accounts: List active bank accounts and balances
#          - GET /payment/transactions: Recent audited transactions with Kepler telemetry
# =====================================================================

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Dict
from backend.db.session import get_db
from backend.schemas.payment_schema import (
    BankTransferRequest,
    BankTransferResponse,
    BenchmarkRequest,
    BenchmarkResponse,
    BankAccountResponse
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
    Captures container energy, attributes carbon, and records SHA-256 audit hash.
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
def get_recent_transactions(limit: int = 20, db: Session = Depends(get_db)):
    """
    Returns recent audited transactions with telemetry annotations.
    """
    return payment_service.list_recent_transactions(db=db, limit=limit)
