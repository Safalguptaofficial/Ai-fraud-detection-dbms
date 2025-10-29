from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from ml_enhanced_model import predict_fraud, explain_fraud_prediction

router = APIRouter()

class TransactionPredict(BaseModel):
    amount: float
    merchant_id: Optional[str] = None
    transactions_last_hour: int = 1
    historical_avg_amount: float = 100
    historical_std_amount: float = 50
    minutes_since_last_transaction: int = 60
    location_changed: bool = False
    merchant_risk_score: float = 0.1
    device_changed: bool = False
    ip_reputation_score: float = 0.5

@router.post("/ml/predict")
async def predict_transaction(transaction: TransactionPredict):
    """
    Predict fraud risk for a transaction using ML model
    
    Returns risk score, fraud probability, and triggered rules
    """
    try:
        prediction = predict_fraud(transaction.dict())
        return prediction
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ml/explain")
async def explain_transaction(transaction: TransactionPredict):
    """
    Get detailed explanation of fraud prediction
    
    Returns full analysis with feature contributions and recommendations
    """
    try:
        explanation = explain_fraud_prediction(transaction.dict())
        return explanation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ml/model-info")
async def get_model_info():
    """Get ML model information"""
    return {
        "model_type": "Ensemble (Isolation Forest + Rules + Velocity)",
        "version": "1.0.0",
        "features": [
            "amount", "velocity", "amount_zscore", "time_since_last",
            "location_change", "merchant_risk", "hour_of_day",
            "is_weekend", "device_change", "ip_reputation"
        ],
        "ensemble_weights": {
            "isolation_forest": 0.4,
            "rule_based": 0.3,
            "velocity_model": 0.3
        },
        "thresholds": {
            "high_risk": 70,
            "medium_risk": 40,
            "low_risk": 0
        }
    }

@router.post("/ml/batch-predict")
async def batch_predict(transactions: list[TransactionPredict]):
    """Predict fraud risk for multiple transactions"""
    try:
        predictions = []
        for txn in transactions:
            pred = predict_fraud(txn.dict())
            predictions.append({
                "transaction": txn.dict(),
                "prediction": pred
            })
        
        # Summary statistics
        high_risk_count = sum(1 for p in predictions if p['prediction']['risk_level'] == 'HIGH')
        medium_risk_count = sum(1 for p in predictions if p['prediction']['risk_level'] == 'MEDIUM')
        low_risk_count = sum(1 for p in predictions if p['prediction']['risk_level'] == 'LOW')
        avg_risk_score = sum(p['prediction']['risk_score'] for p in predictions) / len(predictions)
        
        return {
            "predictions": predictions,
            "summary": {
                "total": len(transactions),
                "high_risk": high_risk_count,
                "medium_risk": medium_risk_count,
                "low_risk": low_risk_count,
                "average_risk_score": round(avg_risk_score, 2)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

