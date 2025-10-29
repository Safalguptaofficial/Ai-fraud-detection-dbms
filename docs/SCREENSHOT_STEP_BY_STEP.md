# Step-by-Step Screenshot Capture Guide

This guide provides detailed instructions for capturing each required screenshot for your submission.

## Prerequisites

```bash
# 1. Start the system
cd /Users/safalgupta/Desktop/AI\ FRAUD\ DETECTION
make up

# 2. Wait for all services to be healthy (2-3 minutes)
docker ps  # Check all containers are "Up" and "healthy"

# 3. Seed the database
make seed

# 4. Wait for seeding to complete
```

---

## Screenshot Checklist

### [ ] 1. Docker Containers Running

**What to capture**: Docker containers status showing all services

**Steps**:
```bash
# Open Terminal and run:
docker ps

# Screenshot the entire terminal output showing:
# - fraud-dbms_oracle_1
# - fraud-dbms_postgres_1  
# - fraud-dbms_mongo_1
# - fraud-dbms_redis_1
# - fraud-dbms_api_1
# - fraud-dbms_web_1
# - fraud-dbms_worker_1
# - fraud-dbms_prometheus_1
# - fraud-dbms_grafana_1
```

**Expected Output**:
```
CONTAINER ID   IMAGE                      STATUS
...            fraud-dbms_oracle_1        Up X minutes (healthy)
...            fraud-dbms_postgres_1      Up X minutes (healthy)
...            fraud-dbms_api_1           Up X minutes
...            (and 6 more containers)
```

**Mac Screenshot**: `Cmd + Shift + 4`, drag to select terminal window

**Explanation**:
"This screenshot shows all 9 Docker containers running healthy, 
demonstrating the complete multi-service architecture: 
Oracle, PostgreSQL, MongoDB, Redis, API, Web, Worker, Prometheus, and Grafana."

---

### [ ] 2. Login Page

**What to capture**: JWT authentication login page

**Steps**:
1. Open browser (Chrome/Safari)
2. Navigate to: http://localhost:3000/login
3. Screenshot the entire login page

**What to show**:
- "Fraud Detection Portal" title
- Email input field
- Password input field
- "Demo: analyst@bank.com / password123" hint
- Sign in button
- Entire page layout

**Mac Screenshot**: `Cmd + Shift + 3` (full screen) or `Cmd + Shift + 4` (select area)

**Explanation**:
"This is the JWT authentication login page. Users must authenticate 
with valid credentials to access the fraud detection dashboard. 
The system uses secure JWT tokens for session management."

---

### [ ] 3. Dashboard (Initial State)

**What to capture**: Dashboard showing initial state before any operations

**Steps**:
1. Login to http://localhost:3000/login with:
   - Email: `analyst@bank.com`
   - Password: `password123`
2. After login, you'll be redirected to http://localhost:3000/dashboard
3. Wait for data to load (5 seconds)
4. Screenshot the entire dashboard

**What to show**:
- Header: "Fraud Detection Dashboard"
- Welcome message with user info
- 4 metric cards:
  - Active Alerts (shows number, e.g., 4)
  - Total Accounts (shows number, e.g., 5)
  - Frozen Accounts (shows number, e.g., 0)
  - Active Accounts (shows number, e.g., 5)
- Alert Severity Distribution chart (HIGH, MEDIUM, LOW counts)
- Recent Fraud Alerts table with data
- "Last updated: [time]" with green pulse indicator
- Logout button

**Mac Screenshot**: `Cmd + Shift + 3` or `Cmd + Shift + 4`

**Note the numbers**: Write down or screenshot:
- Initial Active Alerts count: ______
- Initial Total Accounts: ______
- Initial Frozen Accounts: ______

**Explanation**:
"This is the real-time fraud detection dashboard showing the initial 
state before any operations. It displays live fraud alerts, account 
statistics, severity distribution, and recent alerts table. The green 
pulse indicator shows the system is receiving live updates every 5 seconds."

---

### [ ] 4. API Documentation

**What to capture**: Swagger/OpenAPI documentation interface

**Steps**:
1. Open new browser tab (keep dashboard tab open)
2. Navigate to: http://localhost:8000/docs
3. Wait for page to load
4. Screenshot the entire API documentation page

**What to show**:
- Swagger UI interface
- "Fraud Detection API" title
- Available endpoints list:
  - `/v1/auth/login`
  - `/v1/accounts`
  - `/v1/transactions`
  - `/v1/alerts`
  - `/v1/analytics`
  - `/v1/cases`
- Expand one endpoint to show request/response schemas

**Optional**: Click "Try it out" on one endpoint and show the interactive form

**Mac Screenshot**: `Cmd + Shift + 3` or scroll and take multiple screenshots

**Explanation**:
"This is the interactive API documentation (Swagger UI) showing all 
available REST endpoints for the fraud detection system. It includes 
authentication, CRUD operations for accounts, transactions, alerts, 
and analytics endpoints with request/response schemas."

---

### [ ] 5. Database Before Transaction

**What to capture**: Oracle database state before creating a fraudulent transaction

**Steps**:
```bash
# Open Terminal and run:
docker exec fraud-dbms_oracle_1 sqlplus -s system/password@XE <<EOF
SET PAGESIZE 50
SET LINESIZE 120

PROMPT === ACCOUNTS TABLE ===
SELECT account_id, customer_id, status, balance 
FROM app.accounts 
ORDER BY account_id;

PROMPT === FRAUD ALERTS TABLE ===
SELECT alert_id, account_id, rule_code, severity, status, 
       TO_CHAR(alert_time, 'YYYY-MM-DD HH24:MI:SS') as alert_time
FROM app.fraud_alerts 
ORDER BY alert_time DESC 
FETCH FIRST 5 ROWS ONLY;

PROMPT === TRANSACTION COUNT ===
SELECT COUNT(*) as total_transactions FROM app.transactions;
EOF
```

**Screenshot the terminal output** showing:
- Accounts table with statuses (mostly ACTIVE)
- Current fraud alerts count
- Transaction count

**Note the values**: Write down:
- Number of accounts: ______
- Number of fraud alerts: ______
- Account 1 status: ______ (should be ACTIVE or CLOSED)
- Transaction count: ______

**Mac Screenshot**: `Cmd + Shift + 4`, select terminal window

**Explanation**:
"This shows the Oracle database state before any operations. We can see 
accounts with their status, current fraud alerts, and transaction count. 
Account 1 is currently [ACTIVE/CLOSED], ready for testing."

---

### [ ] 6. Create Fraudulent Transaction

**What to capture**: API call and response for creating a fraudulent transaction

**Steps**:
```bash
# Open Terminal and run:
curl -X POST http://localhost:8000/v1/transactions \
  -H "x-api-key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "amount": 8000.00,
    "currency": "USD",
    "merchant": "ATM-CORP",
    "mcc": "6011",
    "channel": "ATM",
    "device_id": "ATM-999",
    "city": "NYC",
    "country": "US",
    "txn_time": "2025-01-15T01:30:00Z",
    "auth_code": "AUTH002"
  }' | python3 -m json.tool
```

**Screenshot the terminal** showing:
- The curl command
- The JSON response with transaction details
- Status code (200 OK)

**Alternative**: Use Postman or browser to show the request/response

**Mac Screenshot**: `Cmd + Shift + 4`, select terminal

**Explanation**:
"This shows the API call creating a suspicious transaction ($8000 at 1:30 AM).
The transaction will trigger Oracle PL/SQL fraud detection triggers 
automatically, causing the account to be frozen and an alert to be created."

**Wait 2-3 seconds** after this for triggers to fire before next screenshot.

---

### [ ] 7. Database After Transaction (Account FROZEN)

**What to capture**: Oracle database state showing account was frozen

**Steps**:
```bash
# In Terminal, run the same query as #5:
docker exec fraud-dbms_oracle_1 sqlplus -s system/password@XE <<EOF
SET PAGESIZE 50
SET LINESIZE 120

PROMPT === ACCOUNTS TABLE (AFTER TRANSACTION) ===
SELECT account_id, customer_id, status, balance 
FROM app.accounts 
ORDER BY account_id;

PROMPT === NEW FRAUD ALERTS ===
SELECT alert_id, account_id, rule_code, severity, status,
       TO_CHAR(alert_time, 'YYYY-MM-DD HH24:MI:SS') as alert_time,
       reason
FROM app.fraud_alerts 
ORDER BY alert_time DESC 
FETCH FIRST 6 ROWS ONLY;

PROMPT === SYSTEM LOGS (ACCOUNT FROZEN EVENT) ===
SELECT log_id, account_id, event_type, 
       TO_CHAR(event_time, 'YYYY-MM-DD HH24:MI:SS') as event_time
FROM app.system_logs 
WHERE event_type LIKE '%FROZEN%'
ORDER BY event_time DESC 
FETCH FIRST 3 ROWS ONLY;
EOF
```

**Screenshot the terminal output** showing:
- Account 1 status changed to **FROZEN**
- New fraud alert created (alert_id should be highest number)
- Alert rule_code: "AMOUNT_GT_5000_MIDNIGHT"
- Severity: HIGH
- System log entry showing ACCOUNT_FROZEN event

**Compare with Screenshot #5** - show the difference:
- Before: Account 1 status = ACTIVE
- After: Account 1 status = FROZEN ✅
- Before: X alerts
- After: X+1 alerts ✅

**Mac Screenshot**: `Cmd + Shift + 4`, select terminal

**Explanation**:
"This demonstrates the automatic database state change after a fraudulent 
transaction. The PL/SQL trigger fired automatically, changing account 1 
from ACTIVE to FROZEN, and created a new HIGH-severity fraud alert with 
rule 'AMOUNT_GT_5000_MIDNIGHT'. This shows real-time fraud detection 
working automatically without manual intervention."

---

### [ ] 8. Dashboard Updated (New Alert)

**What to capture**: Dashboard showing updated state after fraud detection

**Steps**:
1. Go back to dashboard tab: http://localhost:3000/dashboard
2. Wait 5-10 seconds for auto-refresh (or click "Refresh" button)
3. Screenshot the updated dashboard

**What to show**:
- Increased "Active Alerts" count (went from X to X+1)
- "Frozen Accounts" increased from 0 to 1 (or +1 if already had frozen)
- New alert in the "Recent Fraud Alerts" table
- The new alert should show:
  - Rule: AMOUNT_GT_5000_MIDNIGHT
  - Severity: HIGH (red badge)
  - Account: 1

**Optional**: Take a side-by-side screenshot showing before (#3) and after (#8)

**Mac Screenshot**: `Cmd + Shift + 3` or `Cmd + Shift + 4`

**Explanation**:
"This shows the dashboard automatically updated after fraud detection. 
The Active Alerts count increased, Frozen Accounts count increased, 
and a new HIGH-severity alert appeared in the table. This demonstrates 
the real-time nature of the system - the dashboard refreshes every 
5 seconds, automatically showing new fraud alerts without page reload."

---

### [ ] 9. Grafana Monitoring

**What to capture**: Grafana dashboard showing system metrics

**Steps**:
1. Open new browser tab
2. Navigate to: http://localhost:3001
3. Login with:
   - Username: `admin`
   - Password: `admin`
4. After login, look for "Fraud Detection System Dashboard" or create one:
   - Click "+" → "Import dashboard"
   - Or go to "Dashboards" → "Browse"
5. If no dashboard exists, show the default Grafana home
6. Screenshot the Grafana interface

**What to show** (if dashboard exists):
- System health metrics
- HTTP request rates
- Database connection status
- Error rates
- Performance graphs

**What to show** (if no dashboard):
- Grafana home page
- Navigation menu
- Data sources showing Prometheus connected
- Any available metrics

**Mac Screenshot**: `Cmd + Shift + 3` or `Cmd + Shift + 4`

**Explanation**:
"This is the Grafana monitoring dashboard showing system observability. 
It displays Prometheus metrics including HTTP request rates, response 
times, database health, and error tracking. This demonstrates 
production-ready monitoring capabilities for the fraud detection system."

---

### [ ] 10. CRUD Operation Comparisons

**What to capture**: Side-by-side comparison of database changes

**Create a document** showing before/after for each CRUD operation:

#### CREATE Operation Comparison

**Before State** (use Screenshot #5):
```
Accounts: 5 records, all ACTIVE
Alerts: 4 records
```

**Operation**: POST /v1/transactions (fraudulent)

**After State** (use Screenshot #7):
```
Accounts: 5 records, 1 FROZEN (auto-changed)
Alerts: 5 records (1 new alert auto-created)
```

**Take screenshot** of:
- Side-by-side terminal outputs
- Or create a comparison table/document

#### UPDATE Operation Comparison

**Before State**:
```bash
# Check account status
curl http://localhost:8000/v1/accounts/1 | python3 -m json.tool
# Screenshot: Shows status="ACTIVE" (or current status)
```

**Operation**:
```bash
# Update account status
curl -X PATCH http://localhost:8000/v1/accounts/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "FROZEN"}' | python3 -m json.tool
```

**After State**:
```bash
# Verify change
curl http://localhost:8000/v1/accounts/1 | python3 -m json.tool
# Screenshot: Shows status="FROZEN"
```

**Screenshot both responses** side-by-side

**Explanation**:
"This demonstrates the UPDATE operation. The account status was 
manually changed from ACTIVE to FROZEN, showing direct database 
modification through the API. Compare this with the automatic trigger 
in the CREATE operation."

#### READ Operation

**Operation**:
```bash
# List accounts
curl http://localhost:8000/v1/accounts | python3 -m json.tool
```

**Screenshot** showing:
- JSON response with all accounts
- Note: No database changes (READ only)

**Explanation**:
"This shows a READ operation. The query retrieves data without 
modifying the database state. Subsequent requests may be served from 
Redis cache for improved performance."

---

## 📦 Organizing Your Screenshots

Create a folder structure:

```bash
mkdir -p submission/screenshots
```

Save screenshots with descriptive names:
```
submission/screenshots/
├── 01-docker-containers.png
├── 02-login-page.png
├── 03-dashboard-initial.png
├── 04-api-documentation.png
├── 05-db-before-transaction.png
├── 06-create-transaction-api.png
├── 07-db-after-frozen.png
├── 08-dashboard-updated.png
├── 09-grafana-monitoring.png
└── 10-crud-comparisons.png
```

---

## 🎬 Complete Screenshot Workflow

**Recommended Order**:
1. Start system: `make up && make seed`
2. Screenshot #1: Docker containers
3. Screenshot #2: Login page
4. Screenshot #3: Dashboard initial
5. Screenshot #4: API docs
6. Screenshot #5: Database before
7. Screenshot #6: Create transaction (API call)
8. **Wait 3 seconds for triggers**
9. Screenshot #7: Database after (FROZEN account)
10. Screenshot #8: Dashboard updated
11. Screenshot #9: Grafana
12. Screenshot #10: CRUD comparisons

**Total Time**: ~15-20 minutes

---

## 💡 Pro Tips

1. Use consistent browser zoom (100% or 125%)
2. Clean browser (close unnecessary tabs)
3. Terminal size: Make terminal wider for better readability
4. Multiple tabs: Keep all browser tabs open
5. Annotation: Add text annotations if needed
6. Quality: Use PNG format for better quality

---

## ✅ Final Checklist

- [ ] All 10 screenshots captured
- [ ] Screenshots saved with descriptive names
- [ ] Each screenshot has explanation written
- [ ] Database states clearly show before/after differences
- [ ] CRUD operations documented with comparisons
- [ ] Screenshots show actual data (not just empty states)
- [ ] All URLs visible in screenshots where relevant
- [ ] Images are clear and readable

**You're ready for submission!** 🎉
