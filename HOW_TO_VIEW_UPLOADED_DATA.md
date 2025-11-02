# 📊 How to View Your Uploaded CSV Data and Find Fraud

## ✅ Your Data is Here!

**Location:** PostgreSQL Database
- **Table:** `transactions`
- **Rows Inserted:** 10 transactions
- **Accounts Created:** 10 accounts

## 🔍 Where to View Your Data

### 1. **Dashboard** (Recommended)
👉 **URL:** http://localhost:3000/dashboard

**What you'll see:**
- All fraud alerts (if any detected)
- Recent transactions
- Fraud statistics
- Transaction details

### 2. **Enhanced Analytics Dashboard**
👉 **URL:** http://localhost:3000/dashboard-enhanced

**What you'll see:**
- Advanced charts and visualizations
- Fraud trends over time
- Risk distribution
- Transaction heatmaps

### 3. **ML Model Page**
👉 **URL:** http://localhost:3000/ml-model

**What you can do:**
- Test fraud predictions on individual transactions
- Get ML-based fraud explanations
- See risk scores and factors

### 4. **API Endpoints** (Direct Database Access)

```bash
# View all transactions
curl http://localhost:8000/v1/transactions?limit=100 \
  -H "X-API-Key: fgk_live_demo_api_key_12345"

# View fraud alerts
curl http://localhost:8000/v1/alerts?status=open \
  -H "X-API-Key: fgk_live_demo_api_key_12345"
```

## 🚨 How Fraud Detection Works

### Automatic Detection (Real-time API)
When transactions are created via the real-time API (`/api/v1/ingestion/transactions`), fraud detection runs automatically.

### For CSV Uploads
CSV uploads store the data but don't automatically run fraud detection. To detect fraud in uploaded transactions:

**Option 1: Use ML Model Page**
1. Go to http://localhost:3000/ml-model
2. Enter transaction details manually
3. Click "Predict Fraud" to see risk score
4. Click "Explain" for detailed breakdown

**Option 2: Run Analysis Script**
```bash
cd /Users/safalgupta/Desktop/AI_FRAUD_DETECTION
cd services/api
source venv/bin/activate
python3 ../../tools/analyze_uploaded_transactions.py
```

This will:
- Analyze all uploaded transactions
- Run ML fraud detection
- Create fraud alerts for high-risk transactions
- Store alerts in the database

**Option 3: Use API to Analyze**
```bash
# For each transaction, call the ML predict endpoint
curl -X POST http://localhost:8000/v1/ml/predict \
  -H "X-API-Key: fgk_live_demo_api_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 2322.81,
    "transactions_last_hour": 1,
    "historical_avg_amount": 1000,
    "historical_std_amount": 500,
    "minutes_since_last_transaction": 60,
    "merchant_risk_score": 0.2,
    "device_changed": false,
    "ip_reputation_score": 0.5
  }'
```

## 📋 Fraud Detection Rules

The system detects fraud based on:

1. **Amount Anomalies** - Transactions significantly higher than normal
2. **Velocity** - Too many transactions in short time
3. **Geographic Jumps** - Location changes that are impossible
4. **Time Patterns** - Unusual transaction times (e.g., midnight)
5. **ML Risk Score** - Machine learning model analysis

## 🎯 Quick Steps to Find Fraud

1. **View Dashboard:**
   - Open http://localhost:3000/dashboard
   - Check "Fraud Alerts" section
   - Look for HIGH/MEDIUM severity alerts

2. **Run ML Analysis:**
   - Go to http://localhost:3000/ml-model
   - Test individual transactions
   - Review risk scores

3. **Check Alerts API:**
   ```bash
   curl http://localhost:8000/v1/alerts?status=open \
     -H "X-API-Key: fgk_live_demo_api_key_12345"
   ```

4. **View All Transactions:**
   ```bash
   curl http://localhost:8000/v1/transactions?limit=100 \
     -H "X-API-Key: fgk_live_demo_api_key_12345"
   ```

## 💡 Next Steps

After uploading CSV:
1. ✅ Data is stored in `transactions` table
2. ⚠️ Fraud detection needs to be run (use ML Model page or analysis script)
3. ✅ Alerts will appear in Dashboard once detected

---

**Need Help?** Check:
- Dashboard: http://localhost:3000/dashboard
- API Docs: http://localhost:8000/docs
- ML Model: http://localhost:3000/ml-model

