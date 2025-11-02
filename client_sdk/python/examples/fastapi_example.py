"""
FastAPI Integration Example
Integrate fraud detection into FastAPI application
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fraudguard import FraudGuardClient, FraudGuardError

app = FastAPI(title="Payment API with Fraud Detection")

# Initialize FraudGuard client
client = FraudGuardClient(
    api_key="fgk_live_your_api_key_here",
    base_url="https://api.fraudguard.com"
)

class PaymentRequest(BaseModel):
    customer_id: str
    amount: float
    currency: str = "USD"
    merchant: str = "My Store"

@app.post("/payments")
async def process_payment(payment: PaymentRequest):
    """Process payment with fraud detection"""
    try:
        # Analyze fraud risk
        fraud_result = client.analyze_transaction({
            "amount": payment.amount,
            "account_id": payment.customer_id,
            "merchant": payment.merchant,
            "currency": payment.currency
        })
        
        # High risk - decline
        if fraud_result['risk_score'] >= 70:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "declined",
                    "reason": "High fraud risk",
                    "fraud_score": fraud_result['risk_score']
                }
            )
        
        # Medium risk - require verification
        if fraud_result['risk_score'] >= 40:
            return {
                "status": "requires_verification",
                "fraud_score": fraud_result['risk_score'],
                "message": "Please complete additional verification"
            }
        
        # Low risk - approve and ingest
        ingest_result = client.ingest_transaction({
            "account_id": payment.customer_id,
            "amount": payment.amount,
            "merchant": payment.merchant,
            "currency": payment.currency
        })
        
        return {
            "status": "approved",
            "transaction_id": ingest_result['transaction_id'],
            "fraud_score": ingest_result['fraud_score']
        }
        
    except FraudGuardError as e:
        raise HTTPException(status_code=500, detail=str(e))

