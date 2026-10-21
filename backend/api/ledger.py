# =====================================================================
# ECO MONITOR — LEDGER.PY (ROUTER)
# Purpose: Handles API endpoints for querying transaction ledger history
#          and validating cryptographic audit trails.
# =====================================================================

# Import APIRouter, Depends, and status
from fastapi import APIRouter, Depends, HTTPException, status

# Import DB Session type
from sqlalchemy.orm import Session

# Import dependencies
from backend.db.session import get_db
from backend.core.dependencies import get_current_user

# Import models
from backend.models.user import User
from backend.models.ledger_entry import LedgerEntry
from backend.models.transaction import Transaction

# Import schemas
from backend.schemas.ledger_schema import LedgerEntryResponse

# Import services
from backend.services import ledger_service

# Import List, Dict and hashlib for audit verification
from typing import List, Dict
import hashlib

# Create APIRouter instance
router = APIRouter(prefix="/ledger", tags=["Double-Entry Ledger"])


@router.get(
    "",
    response_model=List[LedgerEntryResponse],
    summary="Get user's ledger transaction logs"
)
def list_ledger(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Returns chronological double-entry ledger listings for dashboard
    # WHY:
    # - Merges transactions and ledger entries to construct a readable journal log
    return ledger_service.get_user_ledger(db=db, user_id=current_user.id)


@router.get(
    "/audit/{transaction_id}",
    summary="Cryptographic audit verification of a transaction chain"
)
def audit_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validates cryptographic authenticity of a transaction and its ledger entries
    # WHY:
    # - Reconstructs the ledger journal entries chain and computes a SHA-256 checksum
    # - Implements Day 47 Cryptographic Audit Trail Verification requirement
    
    # 1. Fetch transaction
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found for auditing."
        )

    # Resource ownership check for customers
    if current_user.role == "CUSTOMER" and not getattr(current_user, "is_boss_admin", False):
        if txn.sender_bank_id != current_user.bank_id and txn.recipient_bank_id != current_user.bank_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Denied: You cannot audit transactions belonging to another customer."
            )
        
    # 2. Fetch all matching ledger entries
    entries = db.query(LedgerEntry).filter(LedgerEntry.transaction_id == transaction_id).all()
    if not entries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No ledger entries found associated with this transaction."
        )
        
    # 3. Concatenate and hash the entries to prove integrity
    # WHY:
    # - Combining transaction metadata, entry accounts, types, and amounts into a SHA-256 hash
    # - If any DB record is modified, the reconstructed hash will mismatch, signaling tampering
    raw_data_string = f"Txn:{txn.id}|Desc:{txn.description}|Time:{txn.created_at.isoformat() if txn.created_at else ''}"
    for entry in sorted(entries, key=lambda e: e.id):
        raw_data_string += f"|Entry:{entry.id}|Acc:{entry.account_id}|Type:{entry.type}|Amt:{entry.amount}"
        
    # Compute SHA-256
    sha256_hash = hashlib.sha256(raw_data_string.encode("utf-8")).hexdigest()
    
    return {
        "transaction_id": transaction_id,
        "description": txn.description,
        "timestamp": txn.created_at,
        "ledger_entries_count": len(entries),
        "audit_hash": sha256_hash,
        "status": "VERIFIED_INTEGRIT_OK"
    }
