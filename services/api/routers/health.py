from fastapi import APIRouter, Depends
from typing import Dict
from deps import get_oracle, get_postgres, get_mongo

router = APIRouter()


@router.get("/healthz")
async def health_check() -> Dict[str, str]:
    return {"status": "healthy"}


@router.get("/health/db")
async def health_check_db(
    oracle=Depends(get_oracle),
    postgres=Depends(get_postgres),
    mongo=Depends(get_mongo)
) -> Dict[str, str]:
    return {
        "oracle": "connected",
        "postgres": "connected",
        "mongo": "connected"
    }

