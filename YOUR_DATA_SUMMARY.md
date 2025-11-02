# 📊 Your Uploaded CSV Data - Where It Is & How to Find Fraud

## ✅ Your Data Has Been Inserted!

**Location:** PostgreSQL Database
- **Database:** `frauddb`
- **Table:** `transactions`
- **Total Transactions:** 10 rows ✅
- **Accounts Created:** 10 accounts ✅

**Statistics:**
- Average Amount: $4,078.25
- Min Amount: $385.24
- Max Amount: $9,292.49

## 🔍 Where to View Your Data

### 1. **Dashboard** (Best Option!)
👉 **Open:** http://localhost:3000/dashboard

**What You'll See:**
- All your uploaded transactions
- Fraud alerts (if any detected)
- Statistics and charts
- Recent activity

### 2. **Enhanced Analytics Dashboard**
👉 **Open:** http://localhost:3000/dashboard-enhanced

**What You'll See:**
- Advanced visualizations
- Fraud trends
- Risk distribution charts
- Transaction heatmaps

### 3. **ML Model Page** (Test Fraud Detection)
👉 **Open:** http://localhost:3000/ml-model

**What You Can Do:**
- Test individual transactions for fraud risk
- Get ML-based fraud predictions
- See detailed risk explanations
- Understand why a transaction is flagged

### 4. **Direct API Access**

```bash
# View all transactions
curl "http://localhost:8000/v1/transactions?limit=100" \
  -H "X-API-Key: fgk_live_demo_api_key_12345"

# View fraud alerts
curl "http://localhost:8000/v1/alerts" \
  -H "X-API-Key: fgk_live_demo_api_key_12345"
```

## 🚨 How to Detect Fraud in Your Uploaded Data

### **Important:** CSV upload stores data but doesn't automatically run fraud detection.

### Method 1: Use ML Model Page (Easiest!)

1. Go to: http://localhost:3000/ml-model
2. Enter transaction details:
   - Amount (e.g., 2322.81)
   - Transactions last hour
   - Historical average
   - Merchant risk, etc.
3. Click **"Predict Fraud"** to see risk score
4. Click **"Explain"** for detailed breakdown

### Method 2: Check Dashboard

1. Open: http://localhost:3000/dashboard
2. Look for **"Fraud Alerts"** section
3. If you see alerts, they show:
   - Severity (HIGH/MEDIUM/LOW)
   - Rule that triggered
   - Transaction details

### Method 3: Run Analysis Script

I've created a script to analyze all uploaded transactions:

```bash
cd /Users/safalgupta/Desktop/AI_FRAUD_DETECTION/services/api
source venv/bin/activate
python3 ../../tools/analyze_uploaded_transactions.py
```

This will:
- Analyze all 10 uploaded transactions
- Run ML fraud detection on each
- Create fraud alerts for high-risk transactions
- Show results in console

### Method 4: Use API Endpoint

Test individual transactions via API:

```bash
curl -X POST http://localhost:8000/v1/ml/predict \
  -H "X-API-Key: fgk_live_demo_api_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 9292.49,
    "transactions_last_hour": 1,
    "historical_avg_amount": 4078,
    "historical_std_amount": 3000,
    "minutes_since_last_transaction": 60,
    "location_changed": false,
    "merchant_risk_score": 0.3,
    "device_changed": false,
    "ip_reputation_score": 0.5
  }'
```

## 📋 Fraud Detection Rules

The system detects fraud based on:

1. **High Amount Anomalies** - Unusually large transactions
2. **Velocity Spikes** - Too many transactions in short time
3. **Geographic Jumps** - Impossible location changes
4. **Time Patterns** - Unusual hours (midnight transactions)
5. **ML Risk Score** - Machine learning analysis (0-100 score)

**Risk Levels:**
- **HIGH** (70-100): Block immediately
- **MEDIUM** (40-70): Requires verification
- **LOW** (0-40): Process normally

## 🎯 Quick Steps Right Now

1. **View Your Transactions:**
   ```
   Open: http://localhost:3000/dashboard
   ```

2. **Test Fraud Detection:**
   ```
   Open: http://localhost:3000/ml-model
   Enter: Amount = 9292.49 (your highest transaction)
   Click: "Predict Fraud"
   ```

3. **Check for Existing Alerts:**
   ```
   Open: http://localhost:3000/dashboard
   Look for: "Fraud Alerts" section
   ```

## 💡 Your Uploaded Transactions Sample

Based on your CSV, you have transactions like:
- **$9,292.49** at Spotify (HIGH RISK - very large amount!)
- **$3,853.84** at Ola
- **$2,503.66** at Paytm
- **$2,322.81** at Amazon
- And 6 more transactions

**Recommendation:** Test the $9,292.49 transaction first - large amounts often trigger fraud alerts!

---

**Need Help?**
- Dashboard: http://localhost:3000/dashboard
- ML Model: http://localhost:3000/ml-model
- API Docs: http://localhost:8000/docs

