from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FraudAlert(BaseModel):
    id: int
    account_id: int
    txn_id: Optional[int] = None
    rule_code: str
    severity: str = Field(..., pattern="^(LOW|MEDIUM|HIGH)$")
    reason: Optional[str] = None
    created_at: datetime
    handled: bool = False
    handled_at: Optional[datetime] = None
    handled_by: Optional[str] = None


class AlertUpdate(BaseModel):
    handled: bool
    handled_by: Optional[str] = None

