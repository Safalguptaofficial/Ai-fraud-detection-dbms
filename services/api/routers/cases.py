from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from pymongo.database import Database
from bson import ObjectId
from datetime import datetime
from deps import get_mongo
from models.case import FraudCase, CaseCreate, NoteCreate
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def convert_objectid_to_str(doc):
    """Convert MongoDB ObjectId to string for JSON serialization
    Note: Keeps datetime objects as-is for Pydantic model validation"""
    from bson.int64 import Int64
    from bson.decimal128 import Decimal128
    
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime):
                # Keep datetime as datetime for Pydantic (it will serialize to ISO string in JSON)
                result[key] = value
            elif isinstance(value, (Int64, int)):
                # Handle BSON Int64/Long types
                try:
                    result[key] = int(value)
                except (ValueError, OverflowError):
                    result[key] = str(value)
            elif isinstance(value, Decimal128):
                result[key] = float(value.to_decimal())
            elif isinstance(value, list):
                result[key] = [convert_objectid_to_str(item) for item in value]
            elif isinstance(value, dict):
                result[key] = convert_objectid_to_str(value)
            elif value is None:
                result[key] = None
            else:
                # For any other type, keep as-is
                result[key] = value
        return result
    elif isinstance(doc, (Int64, int)):
        try:
            return int(doc)
        except (ValueError, OverflowError):
            return str(doc)
    elif isinstance(doc, list):
        return [convert_objectid_to_str(item) for item in doc]
    elif isinstance(doc, datetime):
        # Keep datetime for Pydantic
        return doc
    return doc


@router.get("/cases", response_model=List[FraudCase])
async def list_cases(
    status: Optional[str] = None,
    investigator: Optional[str] = None,
    mongo: Database = Depends(get_mongo)
):
    try:
        # Check if MongoDB connection is available
        if mongo is None:
            logger.error("MongoDB connection is None")
            raise HTTPException(status_code=503, detail="MongoDB service unavailable. Please check if MongoDB is running.")
        
        query = {}
        if status:
            query["status"] = status.upper()  # Normalize status to uppercase
        if investigator:
            query["investigator"] = investigator
        
        try:
            cases = list(mongo.fraud_cases.find(query).sort("createdAt", -1).limit(100))
        except Exception as db_error:
            logger.error(f"MongoDB query error: {db_error}", exc_info=True)
            raise HTTPException(
                status_code=503, 
                detail=f"MongoDB query failed: {str(db_error)}. Please check MongoDB connection and collection."
            )
        
        # Convert ObjectId to string for JSON serialization
        cases_serialized = []
        for case in cases:
            if case is None:
                continue
            try:
                case_dict = convert_objectid_to_str(case)
                
                # Ensure all required fields exist with proper types
                if 'notes' not in case_dict or case_dict['notes'] is None:
                    case_dict['notes'] = []
                else:
                    # Ensure notes have proper structure - notes should already be converted by convert_objectid_to_str
                    # Convert note datetimes if they're still datetime objects
                    processed_notes = []
                    for n in case_dict['notes']:
                        # Handle both dict and other types
                        if isinstance(n, dict):
                            note_dict = n
                        else:
                            # Convert to dict if it's some other type
                            note_dict = dict(n) if hasattr(n, '__dict__') else {'author': 'system', 'content': str(n), 'createdAt': datetime.utcnow()}
                        
                        created_at = note_dict.get('createdAt')
                        # Keep as datetime object for Pydantic (it can parse datetime objects)
                        if not isinstance(created_at, datetime):
                            if isinstance(created_at, str):
                                try:
                                    # Try to parse ISO string back to datetime
                                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                except:
                                    created_at = datetime.utcnow()
                            else:
                                created_at = datetime.utcnow()
                        
                        processed_notes.append({
                            'author': note_dict.get('author', 'system'),
                            'content': note_dict.get('content', ''),
                            'createdAt': created_at  # Keep as datetime for Pydantic
                        })
                    case_dict['notes'] = processed_notes
                
                if 'attachments' not in case_dict or case_dict['attachments'] is None:
                    case_dict['attachments'] = []
                else:
                    # Ensure attachments have proper structure - skip invalid ones
                    processed_attachments = []
                    for a in case_dict['attachments']:
                        if isinstance(a, dict):
                            att_dict = a
                        else:
                            att_dict = dict(a) if hasattr(a, '__dict__') else {}
                        
                        # Only include attachments with a filename (required by model)
                        filename = att_dict.get('filename')
                        if filename:
                            processed_attachments.append({
                                'gridFsId': att_dict.get('gridFsId'),
                                'filename': filename,
                                'contentType': att_dict.get('contentType')
                            })
                    case_dict['attachments'] = processed_attachments
                
                if 'txnIds' not in case_dict or case_dict['txnIds'] is None:
                    case_dict['txnIds'] = []
                else:
                    # Convert txnIds to integers
                    case_dict['txnIds'] = [int(tid) for tid in case_dict['txnIds'] if tid is not None]
                
                if 'tags' not in case_dict or case_dict['tags'] is None:
                    case_dict['tags'] = []
                
                if 'investigator' not in case_dict:
                    case_dict['investigator'] = None
                
                # Convert accountId to int if it's a Long or string
                if 'accountId' in case_dict:
                    try:
                        case_dict['accountId'] = int(case_dict['accountId'])
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid accountId for case {case_dict.get('caseId')}: {case_dict['accountId']}")
                        continue
                
                # Ensure updatedAt exists
                if 'updatedAt' not in case_dict or case_dict['updatedAt'] is None:
                    case_dict['updatedAt'] = case_dict.get('createdAt', datetime.utcnow())
                
                # Validate with Pydantic model
                fraud_case = FraudCase(**case_dict)
                cases_serialized.append(fraud_case)
            except Exception as e:
                logger.warning(f"Skipping invalid case (ID: {case.get('caseId', 'unknown')}): {e}")
                import traceback
                logger.error(f"Error details: {traceback.format_exc()}")
                continue
        
        return cases_serialized
    except HTTPException:
        # Re-raise HTTP exceptions (like from get_mongo)
        raise
    except Exception as e:
        logger.error(f"Error fetching cases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch cases: {str(e)}")


@router.post("/cases", response_model=FraudCase)
async def create_case(data: CaseCreate, mongo: Database = Depends(get_mongo)):
    try:
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
        
        # Convert ObjectId to string
        case_doc_serialized = convert_objectid_to_str(case_doc)
        
        return FraudCase(**case_doc_serialized)
    except Exception as e:
        logger.error(f"Error creating case: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create case: {str(e)}")


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

