"""
Flask Integration Example
Process payments with fraud detection
"""
from flask import Flask, request, jsonify
from fraudguard import FraudGuardClient, FraudGuardError

app = Flask(__name__)

# Initialize FraudGuard client
client = FraudGuardClient(
    api_key="fgk_live_your_api_key_here",
    base_url="https://api.fraudguard.com"
)

@app.route('/process_payment', methods=['POST'])
def process_payment():
    """Process a payment with fraud detection"""
    try:
        payment_data = request.json
        
        # Check fraud risk before processing
        fraud_result = client.analyze_transaction({
            "amount": payment_data['amount'],
            "account_id": payment_data['customer_id'],
            "merchant": "My Store",
            "currency": payment_data.get('currency', 'USD'),
            "channel": "ONLINE"
        })
        
        # Decision logic
        if fraud_result['risk_score'] >= 70:
            return jsonify({
                "status": "declined",
                "reason": "High fraud risk detected",
                "fraud_score": fraud_result['risk_score']
            }), 400
        
        elif fraud_result['risk_score'] >= 40:
            # Medium risk - require additional verification
            return jsonify({
                "status": "requires_verification",
                "fraud_score": fraud_result['risk_score'],
                "message": "Additional verification required"
            }), 202
        
        else:
            # Low risk - process payment
            # ... your payment processing code ...
            
            # Ingest for monitoring
            ingest_result = client.ingest_transaction({
                "account_id": payment_data['customer_id'],
                "amount": payment_data['amount'],
                "merchant": "My Store",
                "currency": payment_data.get('currency', 'USD')
            })
            
            return jsonify({
                "status": "approved",
                "transaction_id": ingest_result['transaction_id'],
                "fraud_score": ingest_result['fraud_score']
            }), 200
            
    except FraudGuardError as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)

