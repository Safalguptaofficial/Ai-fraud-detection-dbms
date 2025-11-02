# CSV Upload Real-Time Fix - Test Guide

## ✅ Fix Summary

The real-time issue where Recent Transactions didn't show uploaded CSV data has been fixed with:

1. **Enhanced Cache Clearing** - Comprehensive cache invalidation after CSV upload
2. **Automatic Dashboard Refresh** - Frontend automatically redirects and refreshes after upload
3. **Cache Bypass Logic** - Dashboard bypasses cache when coming from upload page

## 🧪 Manual Test Steps

### Prerequisites
- API server running on `http://localhost:8000`
- Frontend running (Next.js dev server)
- Database and Redis running

### Test 1: Verify Cache Clearing Works

#### Step 1: Check Initial Transaction Count
```bash
curl -s 'http://localhost:8000/v1/transactions?limit=5' \
  -H 'X-API-Key: fgk_live_demo_api_key_12345' | jq 'length'
```

Note the count (e.g., 100 transactions)

#### Step 2: Check Cache Status
```bash
curl -s 'http://localhost:8000/v1/cache/stats' \
  -H 'X-API-Key: fgk_live_demo_api_key_12345' | jq '.keys'
```

#### Step 3: Create Test CSV File
Create `test_upload.csv` with:
```csv
account_id,amount,merchant,transaction_date,currency,city,country
ACC1001,150.00,Test Store 1,2025-01-15 10:30:00,USD,New York,US
ACC1002,250.50,Test Store 2,2025-01-15 11:00:00,USD,Los Angeles,US
ACC1003,75.25,Test Store 3,2025-01-15 11:30:00,USD,Chicago,US
```

#### Step 4: Upload CSV via API
```bash
curl -X POST 'http://localhost:8000/api/v1/ingestion/files' \
  -H 'X-API-Key: fgk_live_demo_api_key_12345' \
  -F 'file=@test_upload.csv'
```

Expected response:
```json
{
  "upload_id": 123,
  "result": {
    "success": true,
    "rows_inserted": 3,
    "rows_failed": 0
  }
}
```

#### Step 5: Immediately Fetch Transactions (with bypass_cache)
```bash
curl -s 'http://localhost:8000/v1/transactions?limit=5&bypass_cache=true&_t='$(date +%s) \
  -H 'X-API-Key: fgk_live_demo_api_key_12345' | jq 'length'
```

✅ **PASS**: If count increased by 3 (or new transactions appear)

#### Step 6: Check Cache Was Cleared
```bash
curl -s 'http://localhost:8000/v1/cache/stats' \
  -H 'X-API-Key: fgk_live_demo_api_key_12345' | jq '.keys'
```

✅ **PASS**: If transaction cache keys were cleared (keys count may be 0 or reduced)

---

### Test 2: Frontend Integration Test

#### Step 1: Open Frontend
1. Navigate to `http://localhost:3000`
2. Login if needed
3. Go to Dashboard (`/dashboard`)
4. Note the current transaction count in "Recent Transactions" table

#### Step 2: Upload CSV
1. Navigate to Data Upload page (`/data/upload`)
2. Click "Download CSV Template" to see format
3. Create a CSV file with test transactions:
   ```csv
   account_id,amount,merchant,transaction_date,currency,city,country
   ACC2001,99.99,New Merchant,2025-01-15 14:00:00,USD,Seattle,US
   ACC2002,199.99,Another Store,2025-01-15 14:15:00,USD,Portland,US
   ```
4. Upload the file

#### Step 3: Verify Automatic Redirect
✅ **PASS**: If:
- Success toast appears
- Page automatically redirects to `/dashboard?refresh=true` after ~2 seconds
- Dashboard loads with fresh data

#### Step 4: Check Recent Transactions
✅ **PASS**: If:
- New transactions appear in "Recent Transactions" table immediately
- Transaction count increased
- No manual refresh needed

#### Step 5: Test Manual Refresh Button
1. Click the "Refresh" button on dashboard
2. Check browser console for: `🔄 Bypassing cache - fetching fresh data`

✅ **PASS**: If:
- Cache is bypassed (check console logs)
- Fresh data is loaded

---

### Test 3: Cache Bypass Verification

#### Test with Browser DevTools

1. Open Chrome DevTools (F12)
2. Go to Network tab
3. Navigate to Dashboard
4. Look for request: `GET /v1/transactions?...`
5. Upload CSV file
6. Navigate back to Dashboard
7. Check network request again

✅ **PASS**: If request includes:
- `bypass_cache=true` parameter
- `_t=<timestamp>` cache buster

---

## 🔍 Expected Behavior

### ✅ Working Correctly
- CSV uploads successfully
- Cache is cleared server-side after upload
- Dashboard automatically redirects after upload
- New transactions appear immediately without manual refresh
- Refresh button bypasses cache
- Console shows cache bypass messages

### ❌ Issues to Watch For
- Transactions don't appear after upload → Check cache clearing logic
- Dashboard doesn't auto-refresh → Check sessionStorage flag
- Old data still showing → Check bypass_cache parameter
- 401 errors → Check API key/authentication
- 500 errors → Check tenant exists in database

---

## 🐛 Debugging

### Check Backend Logs
Look for these log messages:
```
Cleared transactions cache after upload for tenant {tenant_id} (deleted X keys total)
```

### Check Frontend Console
Look for:
```
📥 Cleared data_uploaded flag - forcing cache bypass
🔄 Bypassing cache - fetching fresh data
```

### Check Redis Cache
```bash
# If using Docker
docker exec fraud-dbms_redis_1 redis-cli KEYS "api:*"

# Should see transaction cache keys cleared after upload
```

---

## ✅ Success Criteria

The fix is working if:
1. ✅ CSV uploads successfully return rows_inserted > 0
2. ✅ Cache stats show keys cleared after upload
3. ✅ Transactions fetched with bypass_cache=true show new data immediately
4. ✅ Frontend automatically redirects to dashboard after upload
5. ✅ Dashboard shows new transactions without manual refresh
6. ✅ Refresh button bypasses cache

---

## 📝 Notes

- The fix handles both server-side (Redis cache clearing) and client-side (cache bypass) issues
- Cache clearing uses multiple methods to ensure all transaction cache keys are removed
- Frontend uses sessionStorage to signal dashboard to bypass cache
- Manual refresh button always bypasses cache for fresh data

