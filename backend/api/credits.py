# =====================================================================
# ECO MONITOR — CREDITS.PY (ROUTER)
# Purpose: Handles API endpoints for carbon credits
# (minting, transfers, retirement).
# =====================================================================


# 🔹 FastAPI tools
from fastapi import APIRouter, Depends, status
# APIRouter → helps create API routes like /credits
# Depends → used to automatically inject things like DB & user
# status → gives HTTP status codes like 200, 201


# 🔹 Database session type
from sqlalchemy.orm import Session
# Session → used to talk to database (run queries, save data)


# 🔹 Dependencies (auto-provided things)
from backend.db.session import get_db
# get_db → gives database connection automatically

from backend.core.dependencies import get_current_user, require_permission
# get_current_user → gives logged-in user using token (JWT)


# 🔹 Models & Schemas
from backend.models.user import User
# User → database model (table structure)

from backend.schemas.credit_schema import (
    CarbonCreditCreate,      # Input when creating (minting) credit
    CarbonCreditResponse,    # Output format when returning credit
    CreditRetireRequest,     # Input when retiring credit
    CreditRetireResponse,    # Output after retiring credit
    CreditTransferRequest    # Input when transferring credit
)


# 🔹 Business logic (actual work happens here)
from backend.services import credit_service
# credit_service → contains real logic (DB operations, validations)


# 🔹 Typing for list response
from typing import List
# Used to say "this API returns a list of items"


# =====================================================================
# 🚀 Create Router
# =====================================================================

router = APIRouter(prefix="/credits", tags=["Carbon Credits"])

# prefix="/credits"
# → All APIs will start with /credits
# Example:
#   /credits
#   /credits/mint
#   /credits/transfer

# tags=["Carbon Credits"]
# → Just for grouping APIs in Swagger UI (documentation)



# =====================================================================
# 📦 GET ALL CREDITS (READ)
# =====================================================================

@router.get(
    "",
    response_model=List[CarbonCreditResponse],
    summary="Get user's carbon credits"
)
# This creates API:
# GET /credits

def list_credits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # db → database connection (auto given)
    # current_user → logged-in user (auto given)

    # WHAT THIS DOES:
    # Returns all credits of the current user

    # WHY:
    # - Shows user their credits (active + retired)
    # - Uses Redis cache (fast performance)

    return credit_service.get_user_credits(
        db=db,
        user_id=current_user.id
    )



# =====================================================================
# 🏭 MINT NEW CREDITS (CREATE)
# =====================================================================

@router.post(
    "/mint",
    response_model=CarbonCreditResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Mint new carbon credits"
)
# API:
# POST /credits/mint

def mint_credit(
    schema: CarbonCreditCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("credits.mint"))
):
    # schema → input data from user (JSON body)
    # db → database
    # current_user → logged-in user

    # WHAT THIS DOES:
    # Creates new carbon credits and assigns to user

    # WHY:
    # - Adds new verified carbon credits
    # - Automatically creates ledger entries (accounting)

    return credit_service.mint_carbon_credit(
        db=db,
        user_id=current_user.id,
        credit_type=schema.credit_type,
        amount=schema.amount,
        source=schema.source,
        vintage_year=schema.vintage_year
    )



# =====================================================================
# 🔁 TRANSFER CREDITS (SEND TO ANOTHER USER)
# =====================================================================

@router.post(
    "/transfer",
    response_model=CarbonCreditResponse,
    summary="Transfer carbon credits"
)
# API:
# POST /credits/transfer

def transfer_credit(
    schema: CreditTransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # schema → contains:
    #   - recipient username
    #   - credit id
    #   - amount

    # WHAT THIS DOES:
    # Transfers credits from one user to another

    # WHY:
    # - Enables trading of carbon credits
    # - Handles partial transfers (split credits)
    # - Maintains correct balance using ledger system

    return credit_service.transfer_carbon_credit(
        db=db,
        sender_id=current_user.id,
        recipient_username=schema.recipient_username,
        credit_id=schema.carbon_credit_id,
        transfer_amount=schema.amount
    )



# =====================================================================
# 🔥 RETIRE CREDITS (USE / BURN)
# =====================================================================

@router.post(
    "/retire",
    response_model=CreditRetireResponse,
    summary="Retire carbon credits"
)
# API:
# POST /credits/retire

def retire_credit(
    schema: CreditRetireRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # schema → contains:
    #   - credit id
    #   - amount
    #   - notes

    # WHAT THIS DOES:
    # Marks credits as USED (cannot be reused)

    # WHY:
    # - Used to offset carbon emissions
    # - Removes credits from active balance
    # - Generates proof (certificate)

    return credit_service.retire_carbon_credit(
        db=db,
        user_id=current_user.id,
        credit_id=schema.carbon_credit_id,
        retire_amount=schema.amount,
        notes=schema.notes
    )