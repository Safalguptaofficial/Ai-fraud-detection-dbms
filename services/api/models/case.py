from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Note(BaseModel):
    author: str
    content: str
    createdAt: datetime


class Attachment(BaseModel):
    gridFsId: Optional[str] = None
    filename: str
    contentType: Optional[str] = None


class FraudCase(BaseModel):
    caseId: str
    accountId: int
    txnIds: Optional[List[int]] = []
    investigator: Optional[str] = None
    notes: Optional[List[Note]] = []
    attachments: Optional[List[Attachment]] = []
    status: str = Field(..., pattern="^(OPEN|INVESTIGATING|RESOLVED|ESCALATED)$")
    tags: Optional[List[str]] = []
    createdAt: datetime
    updatedAt: Optional[datetime] = None


class CaseCreate(BaseModel):
    accountId: int
    txnIds: Optional[List[int]] = []
    tags: Optional[List[str]] = []
    notes: Optional[str] = None


class NoteCreate(BaseModel):
    content: str
    author: str

