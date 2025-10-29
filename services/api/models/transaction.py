from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Transaction(BaseModel):
    id: int
    account_id: int
    amount: float
    currency: str
    merchant: Optional[str] = None
    mcc: Optional[str] = None
    channel: Optional[str] = None
    device_id: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    city: Optional[str] = None
    country: Optional[str] = None
    txn_time: datetime
    auth_code: Optional[str] = None
    status: str = Field(..., pattern="^(APPROVED|DECLINED|REVIEW)$")
    created_at: datetime


class TransactionCreate(BaseModel):
    account_id: int
    amount: float = Field(..., gt=0)
    currency: str = "USD"
    merchant: Optional[str] = None
    mcc: Optional[str] = None
    channel: Optional[str] = None
    device_id: Optional[str] = None
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    city: Optional[str] = None
    country: Optional[str] = None
    txn_time: datetime
    auth_code: Optional[str] = None

