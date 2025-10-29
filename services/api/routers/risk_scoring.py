from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg import Connection
from deps import get_postgres
from ml_risk_scorer import risk_scorer

router = APIRouter()


class TransactionRiskRequest(BaseModel):
    account_id: int
    amount: float
    currency: str
    merchant: str
    mcc: str
    channel: str
    city: str | None = None
    country: str | None = None
    lat: float | None = None
    lon: float | None = None
    txn_time: str


class RiskScoreResponse(BaseModel):
    risk_score: float
    risk_level: str
    factors: Dict[str, Any]
    recommendation: str


@router.post("/risk-score", response_model=RiskScoreResponse)
async def calculate_risk_score(
    request: TransactionRiskRequest,
    postgres: Connection = Depends(get_postgres)
):
    """Calculate ML-based risk score for a transaction"""
    
    # Get account history for velocity analysis
    with postgres.cursor() as cursor:
        cursor.execute("""
            SELECT id, amount, txn_time, merchant, channel
            FROM transactions
            WHERE account_id = %s
              AND txn_time > NOW() - INTERVAL '1 hour'
            ORDER BY txn_time DESC
            LIMIT 20
        """, (request.account_id,))
        
        history = cursor.fetchall()
    
    # Prepare transaction data
    transaction_data = {
        'account_id': request.account_id,
        'amount': request.amount,
        'currency': request.currency,
        'merchant': request.merchant,
        'mcc': request.mcc,
        'channel': request.channel,
        'city': request.city,
        'country': request.country,
        'lat': request.lat,
        'lon': request.lon,
        'txn_time': request.txn_time,
    }
    
    # Calculate risk score
    risk_score = risk_scorer.calculate_risk_score(
        transaction_data,
        history
    )
    
    # Get explanation
    explanation = risk_scorer.explain_score(transaction_data, risk_score)
    
    return RiskScoreResponse(**explanation)


@router.get("/risk-distribution")
async def get_risk_distribution(postgres: Connection = Depends(get_postgres)):
    """Get distribution of risk scores across recent transactions"""
    
    # This would calculate risk scores for recent transactions
    # For now, return mock data
    return {
        "distribution": [
            {"range": "0-20", "count": 150, "percentage": 45},
            {"range": "21-40", "count": 80, "percentage": 24},
            {"range": "41-60", "count": 50, "percentage": 15},
            {"range": "61-80", "count": 35, "percentage": 11},
            {"range": "81-100", "count": 18, "percentage": 5},
        ],
        "total_transactions": 333,
        "high_risk_count": 53,
        "high_risk_percentage": 16
    }


@router.get("/risk-trends")
async def get_risk_trends():
    """Get risk score trends over time"""
    
    return {
        "trends": [
            {"date": "2025-10-23", "avg_risk": 32.5, "high_risk_count": 12},
            {"date": "2025-10-24", "avg_risk": 35.2, "high_risk_count": 15},
            {"date": "2025-10-25", "avg_risk": 28.7, "high_risk_count": 8},
            {"date": "2025-10-26", "avg_risk": 41.3, "high_risk_count": 22},
            {"date": "2025-10-27", "avg_risk": 38.9, "high_risk_count": 18},
            {"date": "2025-10-28", "avg_risk": 33.1, "high_risk_count": 14},
            {"date": "2025-10-29", "avg_risk": 36.4, "high_risk_count": 16},
        ]
    }

