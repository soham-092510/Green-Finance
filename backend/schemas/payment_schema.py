# =====================================================================
# ECO MONITOR / GREEN-FINANCE — PAYMENT_SCHEMA.PY
# Purpose: Pydantic schemas for simulated banking payments & benchmarks.
# =====================================================================

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class BankTransferRequest(BaseModel):
    source_account: str = Field(..., description="Source Bank ID (e.g. HDFC9999)")
    destination_account: str = Field(..., description="Destination Bank ID (e.g. MAH123, IDF892, SBIN456)")
    amount: float = Field(..., gt=0.0, description="Transfer amount in INR")
    currency: str = Field(default="INR", description="Currency code")
    note: Optional[str] = Field(default="Inter-bank fund settlement", description="Transfer note or description")


class BankTransferResponse(BaseModel):
    transaction_id: str
    sender_bank_id: str
    recipient_bank_id: str
    amount: float
    currency: str
    energy_joules: float
    carbon_grams: float
    fidelity_percent: float
    audit_hash: str
    timestamp: datetime
    status: str
    sender_balance: float
    description: str


class BenchmarkRequest(BaseModel):
    count: int = Field(default=50, ge=5, le=1000, description="Number of identical transactions to execute")
    amount: float = Field(default=10.0, gt=0.0, description="Amount per transaction")
    source_account: str = Field(default="HDFC9999", description="Source Bank ID")
    destination_account: str = Field(default="MAH123", description="Destination Bank ID")


class BenchmarkResponse(BaseModel):
    tx_count: int
    total_amount: float
    mean_energy_joules: float
    std_energy_joules: float
    cv_percent: float
    status: str
    duration_ms: float
    message: str


class BankAccountResponse(BaseModel):
    bank_id: str
    name: str
    username: str
    balance: float
    currency: str = "INR"


class StimulateRequest(BaseModel):
    user_count: int = Field(default=10, ge=1, le=50, description="Number of concurrent simulated users")
    tx_count: int = Field(default=10, ge=1, le=100, description="Number of transactions to execute across users")
    min_amount: float = Field(default=100.0, ge=1.0)
    max_amount: float = Field(default=5000.0, le=50000.0)


class StimulateResponse(BaseModel):
    status: str
    executed_count: int
    user_count: int
    total_amount: float
    total_energy_joules: float
    total_carbon_grams: float
    avg_latency_ms: float
    synced_to_green_finance_2: bool
    transactions: List[Dict[str, Any]]
