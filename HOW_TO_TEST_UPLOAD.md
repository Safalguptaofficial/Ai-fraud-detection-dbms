# How to Test the Upload Fix

## Quick Test Steps

### 1. Refresh Your Browser
- Open your browser and go to `http://localhost:3000`
- Press `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac) to do a hard refresh
- This ensures you get the latest frontend code with the fixed API key

### 2. Navigate to Upload Page
- Go to the Upload Data page: `http://localhost:3000/data/upload`
- You should see the file upload interface

### 3. Download the CSV Template (Optional)
- Click "Download CSV Template" button
- This gives you a properly formatted CSV file to test with

### 4. Upload a Test File
You can either:
- Use the downloaded template and add some test data
- Or create your own CSV file with these required columns:
  ```
  account_id,amount,merchant,transaction_date
  ```

Example CSV content:
```csv
account_id,amount,merchant,transaction_date,currency,mcc,channel,city,country
ACC001,150.50,Test Store,2025-11-01 10:30:00,USD,5411,ONLINE,New York,US
ACC002,89.99,Coffee Shop,2025-11-01 09:15:00,USD,5812,POS,Los Angeles,US
```

### 5. Verify Upload Success
After uploading, you should see:
- ✅ "Successfully uploaded! X rows inserted" message
- Upload results showing:
  - Total rows processed
  - Rows inserted
  - Rows failed (should be 0)
- Automatic redirect to dashboard after a few seconds

### 6. View Uploaded Data
- Go to the Dashboard: `http://localhost:3000/dashboard`
- You should see your uploaded transactions in the "Recent Transactions" table
- Charts should update with your new data

## Troubleshooting

### If Upload Still Fails:

1. **Check Browser Console**
   - Open Developer Tools (F12)
   - Look for errors in the Console tab
   - Look for the log message: `✅ Using API key for auth`

2. **Verify Services are Running**
   ```bash
   docker ps | grep fraud-dbms
   ```
   You should see these containers running:
   - fraud-dbms_api_1
   - fraud-dbms_web_1
   - fraud-dbms_postgres_1

3. **Check API Logs**
   ```bash
   docker logs fraud-dbms_api_1 --tail 50
   ```
   Look for authentication or upload-related errors

4. **Test API Directly**
   ```bash
   curl -H "X-API-Key: fgk_live_xj2twCjoRDv2q9ReBlNkf1wxvte-e8Jhz5cOj_kh5ik" http://localhost:8000/
   ```
   Should return: `{"service":"fraud-dbms-api",...}`

## Expected Behavior

### Success Flow:
1. Select CSV file → File appears in upload area
2. Click "Upload File" → Button shows "Uploading..." with spinner
3. Upload completes → Success toast notification
4. Results appear → Shows rows processed/inserted
5. Auto-redirect → Dashboard shows new transactions

### What You'll See in Console:
```
🔵 Button onClick triggered
📤 Starting file upload...
✅ Using API key for authentication
📥 Received response: {status: 200, ok: true}
✅ Upload successful
```

## Still Having Issues?

If the upload still doesn't work after following these steps:

1. **Clear Browser Cache & Cookies**
2. **Try in Incognito/Private Mode**
3. **Restart Docker Services**:
   ```bash
   cd /Users/safalgupta/Desktop/AI_FRAUD_DETECTION/infra/docker
   docker-compose restart api web
   ```

## Additional Notes

- Maximum file size: 50MB
- Supported formats: CSV, XLSX, XLS
- Required columns: `account_id`, `amount`, `merchant`, `transaction_date`
- Optional columns: `currency`, `mcc`, `channel`, `city`, `country`, `device_id`

---
**Last Updated:** November 2, 2025

