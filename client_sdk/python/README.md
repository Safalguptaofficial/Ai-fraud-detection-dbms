# FraudGuard Python SDK

Python SDK for integrating FraudGuard fraud detection into your applications.

## Installation

```bash
pip install fraudguard
```

Or from source:

```bash
cd client_sdk/python
pip install -e .
```

## Quick Start

```python
from fraudguard import FraudGuardClient

# Initialize client
client = FraudGuardClient(
    api_key="fgk_live_your_api_key_here",
    base_url="https://api.fraudguard.com"  # Or your custom URL
)

# Analyze a transaction
result = client.analyze_transaction({
    "amount": 150.00,
    "account_id": "ACC123",
    "merchant": "Example Store",
    "currency": "USD",
    "channel": "ONLINE"
})

print(f"Risk Score: {result['risk_score']}")
print(f"Risk Level: {result['risk_level']}")
print(f"Recommendation: {result['recommendation']}")

# Ingest transaction for real-time monitoring
result = client.ingest_transaction({
    "account_id": "ACC123",
    "amount": 150.00,
    "merchant": "Example Store",
    "currency": "USD"
})

print(f"Transaction ID: {result['transaction_id']}")
print(f"Fraud Score: {result['fraud_score']}")
print(f"Status: {result['status']}")
```

## Examples

See `examples/` directory for complete integration examples:
- Flask app integration
- Django middleware
- FastAPI integration
- Standalone script

## API Reference

See full documentation at: https://docs.fraudguard.com/python

