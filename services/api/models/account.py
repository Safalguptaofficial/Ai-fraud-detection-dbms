from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Account(BaseModel):
    id: int
    customer_id: str
    status: str = Field(..., pattern="^(ACTIVE|FROZEN|CLOSED)$")
    created_at: datetime
    updated_at: Optional[datetime] = None


class AccountCreate(BaseModel):
    customer_id: str = Field(..., min_length=3, max_length=64)


class AccountUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(ACTIVE|FROZEN|CLOSED)$")

