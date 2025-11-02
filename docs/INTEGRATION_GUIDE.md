# 🔌 Integration Guide

**FraudGuard Integration Guide** - Connect your payment system to FraudGuard fraud detection

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Payment Gateway Webhooks](#payment-gateway-webhooks)
3. [API Integration](#api-integration)
4. [SDKs](#sdks)
5. [Database Connectors](#database-connectors)
6. [Examples](#examples)

---

## 🚀 Quick Start

### 1. Get Your API Key

Sign up at [FraudGuard Dashboard](https://dashboard.fraudguard.com) and get your API key:
```
fgk_live_your_api_key_here
```

### 2. Choose Integration Method

- **Webhooks** (Recommended) - Automatic transaction monitoring
- **API SDK** - Programmatic integration
- **Database Connector** - Sync from your database

---

## 💳 Payment Gateway Webhooks

### Stripe Integration

#### Step 1: Configure Webhook in Stripe Dashboard

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://api.fraudguard.com/api/v1/webhooks/stripe`
3. Select events:
   - `charge.succeeded`
   - `payment_intent.succeeded`
   - `charge.failed`

#### Step 2: Add Webhook Secret to FraudGuard

Set environment variable:
```bash
export STRIPE_WEBHOOK_SECRET="whsec_your_stripe_webhook_secret"
```

#### Step 3: Webhook Response

FraudGuard will analyze each payment and return:
```json
{
  "status": "processed",
  "transaction_id": 12345,
  "fraud_score": 0.75,
  "action": "review",
  "recommendation": "Medium fraud risk. Review before fulfillment."
}
```

**Actions:**
- `approved`: Low risk (fraud_score < 0.5)
- `review`: Medium risk (fraud_score 0.5-0.8)
- `blocked`: High risk (fraud_score > 0.8)

#### Step 4: Handle High-Risk Transactions

If `action: "blocked"`, refund the charge:

```python
import stripe

if result['action'] == 'blocked':
    stripe.Refund.create(charge=charge_id)
```

---

### PayPal Integration

#### Step 1: Configure Webhook in PayPal Developer Dashboard

1. Go to PayPal Developer → App → Webhooks
2. Add endpoint: `https://api.fraudguard.com/api/v1/webhooks/paypal`
3. Subscribe to events:
   - `PAYMENT.CAPTURE.COMPLETED`
   - `CHECKOUT.ORDER.COMPLETED`

#### Step 2: Webhook Processing

FraudGuard automatically processes PayPal payments and returns fraud scores.

---

## 🔌 API Integration

### Python SDK

```python
from fraudguard import FraudGuardClient

client = FraudGuardClient(
    api_key="fgk_live_your_key",
    base_url="https://api.fraudguard.com"
)

# Analyze transaction
result = client.analyze_transaction({
    "amount": 150.00,
    "account_id": "CUSTOMER_123",
    "merchant": "My Store",
    "currency": "USD"
})

if result['risk_score'] > 70:
    # Block transaction
    print("HIGH RISK - Blocking transaction")
else:
    # Approve transaction
    print("Transaction approved")
```

### Node.js SDK

```javascript
const { FraudGuardClient } = require('@fraudguard/sdk');

const client = new FraudGuardClient(
  'fgk_live_your_key',
  'https://api.fraudguard.com'
);

// Analyze transaction
const result = await client.analyzeTransaction({
  amount: 150.00,
  account_id: 'CUSTOMER_123',
  merchant: 'My Store',
  currency: 'USD'
});

if (result.risk_score > 70) {
  console.log('HIGH RISK - Blocking transaction');
} else {
  console.log('Transaction approved');
}
```

### REST API (Direct)

```bash
curl -X POST https://api.fraudguard.com/api/v1/ingestion/transactions \
  -H "X-API-Key: fgk_live_your_key" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "CUSTOMER_123",
    "amount": 150.00,
    "merchant": "My Store",
    "currency": "USD"
  }'
```

---

## 💾 Database Connectors

### PostgreSQL Connector

Sync transactions from your PostgreSQL database:

```python
from ingestion.db_connectors import PostgreSQLConnector

connector = PostgreSQLConnector({
    'host': 'your-db-host',
    'port': 5432,
    'database': 'your_db',
    'user': 'your_user',
    'password': 'your_password',
    'table': 'transactions',
    'columns': {
        'account_id': 'customer_id',
        'amount': 'amount',
        'merchant': 'merchant_name',
        'txn_time': 'created_at'
    }
})

# Sync data
result = await connector.sync_data(tenant_id='your_tenant_id')
```

### MySQL Connector

```python
from ingestion.db_connectors import MySQLConnector

connector = MySQLConnector({
    'host': 'your-db-host',
    'port': 3306,
    'database': 'your_db',
    'user': 'your_user',
    'password': 'your_password',
    'table': 'transactions'
})

result = await connector.sync_data(tenant_id='your_tenant_id')
```

### Scheduled Sync

Set up automatic sync:

```python
from ingestion.db_connectors import DataSyncScheduler

scheduler = DataSyncScheduler()

# Schedule daily sync at 2 AM
scheduler.schedule_sync(
    connector=connector,
    tenant_id='your_tenant_id',
    schedule='0 2 * * *'  # Cron format
)
```

---

## 📝 Examples

### Flask Integration

```python
from flask import Flask, request
from fraudguard import FraudGuardClient

app = Flask(__name__)
client = FraudGuardClient(api_key="fgk_live_your_key")

@app.route('/payment', methods=['POST'])
def process_payment():
    payment_data = request.json
    
    # Check fraud risk
    result = client.analyze_transaction({
        "amount": payment_data['amount'],
        "account_id": payment_data['customer_id'],
        "merchant": "My Store"
    })
    
    if result['risk_score'] > 70:
        return {"status": "declined", "reason": "Fraud risk detected"}, 400
    
    # Process payment...
    return {"status": "approved"}
```

### Express.js Integration

```javascript
const express = require('express');
const { FraudGuardClient } = require('@fraudguard/sdk');

const app = express();
const client = new FraudGuardClient('fgk_live_your_key');

app.post('/payment', async (req, res) => {
  const paymentData = req.body;
  
  // Check fraud risk
  const result = await client.analyzeTransaction({
    amount: paymentData.amount,
    account_id: paymentData.customer_id,
    merchant: 'My Store'
  });
  
  if (result.risk_score > 70) {
    return res.status(400).json({
      status: 'declined',
      reason: 'Fraud risk detected'
    });
  }
  
  // Process payment...
  res.json({ status: 'approved' });
});
```

---

## 🔒 Security Best Practices

1. **Never expose API keys** - Store in environment variables
2. **Use HTTPS** - Always use encrypted connections
3. **Verify webhook signatures** - Validate webhook authenticity
4. **Rate limiting** - Respect rate limits (100 requests/minute)
5. **Error handling** - Handle errors gracefully

---

## 🆘 Support

- **Documentation**: https://docs.fraudguard.com
- **Email**: support@fraudguard.com
- **Status Page**: https://status.fraudguard.com

---

**Ready to integrate?** Start with the [Quick Start](#quick-start) guide above!

