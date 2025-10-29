from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from typing import Any


class AnomalyEvent(BaseModel):
    id: str
    account_id: int
    txn_id: Optional[int] = None
    rule: str
    score: Optional[float] = None
    detected_at: datetime
    severity: Optional[str] = None
    extra: Optional[dict[str, Any]] = None

