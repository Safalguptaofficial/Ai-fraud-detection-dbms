# 🔍 ML Model Debugging Steps

**Issue:** Still showing 65.5 risk score regardless of input changes

**Status:** Debugging in progress

---

## 🔍 **Diagnostic Steps:**

### **1. Check Browser Console (F12)**
When you click "Predict Fraud", check the console for:

```
🚀 Sending prediction request with CURRENT values:
  Amount: [your value]
  Velocity: [your value]
  ...
```

**If you see these logs:**
- ✅ Code is running
- Check what values are shown - are they YOUR inputs?

**If you DON'T see these logs:**
- ❌ Browser is using cached old JavaScript
- **Solution:** Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

---

### **2. Check Network Tab (F12 → Network)**
1. Open browser DevTools (F12)
2. Go to "Network" tab
3. Click "Predict Fraud"
4. Look for request to `/v1/ml/predict`
5. Click on it and check:
   - **Request Payload:** Does it show YOUR current input values?
   - **Response:** What does the API return?

**If API returns error (404, 500, etc.):**
- Backend API not running or endpoint not found
- Check if backend is running: `docker-compose ps` or `curl http://localhost:8000/`

**If API returns same result:**
- ML model might have an issue
- Need to check model implementation

---

### **3. Check if Backend is Running**
```bash
cd /Users/safalgupta/Desktop/AI_FRAUD_DETECTION
docker-compose ps
```

Or test directly:
```bash
curl http://localhost:8000/
```

**Should return:** `{"service":"fraud-dbms-api",...}`

---

### **4. Hard Refresh Browser**
The browser might be using cached JavaScript:

**Chrome/Edge:**
- Windows/Linux: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

**Firefox:**
- Windows/Linux: `Ctrl + F5`
- Mac: `Cmd + Shift + R`

**Safari:**
- `Cmd + Option + R`

---

### **5. Clear Browser Cache**
1. Open DevTools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"

---

### **6. Check What the API Actually Returns**
Test the API directly:

```bash
# Low risk transaction
curl -X POST http://localhost:8000/v1/ml/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: fgk_live_demo_api_key_12345" \
  -d '{
    "amount": 100,
    "transactions_last_hour": 1,
    "historical_avg_amount": 100,
    "historical_std_amount": 20,
    "minutes_since_last_transaction": 120,
    "location_changed": false,
    "merchant_risk_score": 0.1,
    "device_changed": false,
    "ip_reputation_score": 0.9
  }'

# High risk transaction
curl -X POST http://localhost:8000/v1/ml/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: fgk_live_demo_api_key_12345" \
  -d '{
    "amount": 10000,
    "transactions_last_hour": 20,
    "historical_avg_amount": 100,
    "historical_std_amount": 20,
    "minutes_since_last_transaction": 2,
    "location_changed": true,
    "merchant_risk_score": 0.9,
    "device_changed": true,
    "ip_reputation_score": 0.1
  }'
```

**Compare the risk_score values - are they different?**

---

## 🎯 **Most Likely Causes:**

### **1. Browser Cache (Most Likely)**
- Old JavaScript code with mock data still cached
- **Fix:** Hard refresh browser

### **2. Backend Not Running**
- API endpoint not responding
- **Fix:** Start backend API

### **3. API Endpoint Not Registered**
- Router not properly included
- **Fix:** Check `main.py` router registration

### **4. Form State Not Updating**
- React state not updating when inputs change
- **Fix:** Check if inputs have proper onChange handlers

---

## ✅ **Quick Fixes to Try:**

1. **Hard refresh browser** (Ctrl+Shift+R / Cmd+Shift+R)
2. **Check console logs** - Are YOUR values being sent?
3. **Check Network tab** - What does API actually return?
4. **Restart backend** - `docker-compose restart api` or `docker-compose up -d api`

---

**Please share:**
1. What you see in browser console (F12)
2. What you see in Network tab (request/response)
3. Whether backend API is running

