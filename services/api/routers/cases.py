from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from pymongo.database import Database
from bson import ObjectId
from datetime import datetime
from deps import get_mongo
from models.case import FraudCase, CaseCreate, NoteCreate

router = APIRouter()


@router.get("/cases", response_model=List[FraudCase])
async def list_cases(
    status: Optional[str] = None,
    investigator: Optional[str] = None,
    mongo: Database = Depends(get_mongo)
):
    query = {}
    if status:
        query["status"] = status
    if investigator:
        query["investigator"] = investigator
    
    cases = list(mongo.fraud_cases.find(query).sort("createdAt", -1).limit(100))
    
    return [FraudCase(**case) for case in cases]


@router.post("/cases", response_model=FraudCase)
async def create_case(data: CaseCreate, mongo: Database = Depends(get_mongo)):
    import uuid
    
    case_doc = {
        "caseId": f"CASE-{uuid.uuid4().hex[:6].upper()}",
        "accountId": data.accountId,
        "txnIds": data.txnIds or [],
        "investigator": None,
        "notes": [{
            "author": "system",
            "content": data.notes or "Case created",
            "createdAt": datetime.utcnow()
        }] if data.notes else [],
        "attachments": [],
        "status": "OPEN",
        "tags": data.tags or [],
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    
    result = mongo.fraud_cases.insert_one(case_doc)
    case_doc = mongo.fraud_cases.find_one({"_id": result.inserted_id})
    
    return FraudCase(**case_doc)


@router.get("/cases/search", response_model=List[FraudCase])
async def search_cases(
    q: str = Query(..., min_length=1),
    mongo: Database = Depends(get_mongo)
):
    cases = list(mongo.fraud_cases.find(
        {"$text": {"$search": q}}
    ).sort("createdAt", -1).limit(50))
    
    return [FraudCase(**case) for case in cases]


@router.get("/cases/{case_id}", response_model=FraudCase)
async def get_case(case_id: str, mongo: Database = Depends(get_mongo)):
    case = mongo.fraud_cases.find_one({"caseId": case_id})
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return FraudCase(**case)


@router.post("/cases/{case_id}/notes")
async def add_note(
    case_id: str,
    data: NoteCreate,
    mongo: Database = Depends(get_mongo)
):
    note = {
        "author": data.author,
        "content": data.content,
        "createdAt": datetime.utcnow()
    }
    
    result = mongo.fraud_cases.update_one(
        {"caseId": case_id},
        {
            "$push": {"notes": note},
            "$set": {"updatedAt": datetime.utcnow()}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return {"message": "Note added"}


@router.post("/cases/{case_id}/attachments")
async def upload_attachment(
    case_id: str,
    file: UploadFile,
    mongo: Database = Depends(get_mongo)
):
    import gridfs
    
    fs = gridfs.GridFS(mongo)
    file_id = fs.put(file.file, filename=file.filename, content_type=file.content_type)
    
    attachment = {
        "gridFsId": str(file_id),
        "filename": file.filename,
        "contentType": file.content_type
    }
    
    result = mongo.fraud_cases.update_one(
        {"caseId": case_id},
        {
            "$push": {"attachments": attachment},
            "$set": {"updatedAt": datetime.utcnow()}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return {"message": "Attachment uploaded", "attachment": attachment}

