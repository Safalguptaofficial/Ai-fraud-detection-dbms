# Submission Guide - Screenshots & CRUD Operations

This guide provides instructions for creating the required screenshots and CRUD operation comparisons for your project submission.

## 📸 Screenshot Requirements

### 1. Dashboard Screenshots with Explanations

#### Screenshot 1: Login Page
**Where to capture**: http://localhost:3000/login
**What to show**:
- Login form with email and password fields
- "Fraud Detection Portal" branding
- Demo credentials hint

**Explanation**:
```
"This is the JWT authentication login page. Users must authenticate 
with valid credentials (analyst@bank.com / password123) to access 
the fraud detection dashboard. The system uses JWT tokens for secure 
session management."
```

#### Screenshot 2: Main Dashboard
**Where to capture**: http://localhost:3000/dashboard (after login)
**What to show**:
- Fraud Detection Dashboard header
- 4 metric cards (Active Alerts, Total Accounts, Frozen Accounts, Active Accounts)
- Alert Severity Distribution chart
- Recent Fraud Alerts table
- Last updated timestamp with green pulse indicator

**Explanation**:
```
"This is the real-time fraud detection dashboard. It shows:
- Live fraud alerts with auto-refresh every 5 seconds
- Account statistics (total, active, frozen)
- Severity distribution across HIGH, MEDIUM, and LOW alerts
- Recent fraud alerts table with rule codes and timestamps
- Last update indicator showing the system is receiving live data"
```

#### Screenshot 3: API Documentation
**Where to capture**: http://localhost:8000/docs
**What to show**:
- Swagger/OpenAPI documentation interface
- Available endpoints list
- Authentication section

**Explanation**:
```
"This is the interactive API documentation (Swagger UI) showing all 
available endpoints for the fraud detection system. It includes 
authentication, CRUD operations for accounts, transactions, alerts, 
and analytics endpoints."
```

#### Screenshot 4: Grafana Monitoring
**Where to capture**: http://localhost:3001 (admin/admin)
**What to show**:
- System health metrics
- HTTP request rates
- Database connection status

**Explanation**:
```
"Grafana dashboard showing system monitoring and observability:
- Prometheus metrics integration
- HTTP request rates and response times
- Database health checks (Oracle, PostgreSQL, MongoDB)
- Error tracking and system performance metrics"
```

### 2. Database State Screenshots

#### Screenshot 5: Oracle Database (Before Transaction)
**Command**: 
```bash
docker exec fraud-dbms_oracle_1 sqlplus -s system/password@XE <<EOF
SELECT account_id, status, balance FROM app.accounts ORDER BY account_id;
SELECT alert_id, account_id, rule_code, severity FROM app.fraud_alerts ORDER BY alert_time DESC FETCH FIRST 5 ROWS ONLY;
EOF
```

**What to show**:
- Account statuses (ACTIVE)
- Current alert count

#### Screenshot 6: Oracle Database (After Fraudulent Transaction)
**Command**: Same as above after creating suspicious transaction
**What to show**:
- Account status changed to FROZEN
- New fraud alert created

**Explanation**:
```
"This demonstrates the database state change after a fraudulent 
transaction is detected. The account status automatically changes 
from ACTIVE to FROZEN, and a new fraud alert is created. This 
shows the PL/SQL trigger working in real-time."
```

## 🔄 CRUD Operation Comparison

### Template for Each CRUD Operation

Create a comparison table showing:
- **Before**: Database state before operation
- **Operation**: The CRUD operation performed
- **After**: Database state after operation
- **Trigger Effects**: Any automated changes (fraud alerts, account status, etc.)

### Example: CREATE Operation

#### Before State
```
Database Tables:
- accounts: 5 records (all status='ACTIVE')
- fraud_alerts: 4 records (4 open alerts)
```

#### Operation Performed
```bash
POST /v1/transactions
{
  "account_id": 1,
  "amount": 8000,
  "merchant": "ATM-CORP",
  "txn_time": "2025-01-15T01:30:00Z"
}
```

#### After State
```
Database Tables:
- accounts: 5 records (1 status='FROZEN', 4 status='ACTIVE')
- fraud_alerts: 5 records (new alert created)
- transactions: New transaction record added

Trigger Effects:
✓ Account automatically frozen (PL/SQL trigger fired)
✓ Fraud alert created with severity='HIGH'
✓ Alert reason: "AMOUNT_GT_5000_MIDNIGHT"
```

### Document Each Operation

#### 1. CREATE Operations
- Create Account
- Create Transaction (triggers fraud detection)
- Create Fraud Alert (automatic)

#### 2. READ Operations
- List All Accounts
- Get Account by ID
- List Open Fraud Alerts
- Get Transactions with Pagination

#### 3. UPDATE Operations
- Update Account Status (ACTIVE → FROZEN)
- Update Alert Status (OPEN → INVESTIGATING)
- Update Transaction Status (PENDING → COMPLETED)

#### 4. DELETE Operations
- Soft delete (status changes)
- Cache clearing operations

## 📋 Step-by-Step Screenshot Instructions

### Step 1: Start the System
```bash
cd /Users/safalgupta/Desktop/AI\ FRAUD\ DETECTION
make up
make seed
```

### Step 2: Take Base Screenshots
1. Open http://localhost:3000 and login
2. Screenshot the dashboard showing initial state
3. Note the current alert count and account statistics

### Step 3: Perform CRUD Operations
Use the following commands to perform operations:

```bash
# READ: Get accounts
curl http://localhost:8000/v1/accounts | jq

# CREATE: Create suspicious transaction
curl -X POST http://localhost:8000/v1/transactions \
  -H "x-api-key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "amount": 8000,
    "currency": "USD",
    "merchant": "ATM-CORP",
    "mcc": "6011",
    "channel": "ATM",
    "city": "NYC",
    "country": "US",
    "txn_time": "2025-01-15T01:30:00Z",
    "auth_code": "AUTH001"
  }'

# UPDATE: Check account status
curl http://localhost:8000/v1/accounts/1 | jq

# Check alerts
curl http://localhost:8000/v1/alerts?status=open | jq
```

### Step 4: Capture Changes
1. Refresh the dashboard
2. Screenshot showing the new alert count
3. Screenshot showing frozen account
4. Check database directly to show state changes

## 🎬 Suggested Screenshot Sequence

### Set 1: System Overview
1. Docker containers running (`docker ps`)
2. Database services healthy
3. API health check response
4. Login page

### Set 2: Dashboard Functionality
5. Dashboard before any operations
6. Creating a transaction (API call + response)
7. Dashboard after transaction (showing changes)
8. Real-time update indicator

### Set 3: Database Changes
9. Oracle database before transaction
10. Oracle database after transaction showing FROZEN account
11. New fraud alert in database
12. Account status comparison

### Set 4: Advanced Features
13. Grafana monitoring dashboard
14. API documentation
15. Prometheus metrics
16. Redis cache statistics

## 📝 Documentation Format

For each screenshot, include:

1. **Screenshot Image** (PNG/JPG, high quality)
2. **Title**: Brief description
3. **Description**: What is shown
4. **Purpose**: Why this screenshot is important
5. **Technical Details**: Relevant code/configuration

### Example Entry

```
## Screenshot 7: Real-Time Dashboard Update

![Dashboard Update](screenshots/dashboard-update.png)

**Description**: Dashboard showing live fraud alert count update

**What it Shows**:
- Active alerts increased from 4 to 5
- Account status changed to FROZEN
- New alert in the recent fraud alerts table

**Technical Details**:
- Auto-refresh mechanism: Polls API every 5 seconds
- Data source: Oracle database via FastAPI
- Real-time indicator: Green pulse shows live connection

**Purpose**: Demonstrates the real-time nature of the fraud 
detection system and automatic trigger execution.
```

## 🛠️ Tools to Use

### Screenshots
- Use **Cmd+Shift+4** (Mac) or **Snipping Tool** (Windows)
- Save as high-resolution PNG
- Include timestamps or watermarks if needed

### Database Queries
```bash
# Oracle
docker exec fraud-dbms_oracle_1 sqlplus system/password@XE

# PostgreSQL
docker exec fraud-dbms_postgres_1 psql -U postgres -d frauddb

# MongoDB
docker exec fraud-dbms_mongo_1 mongosh
```

### API Testing
- Use **Postman** or **curl** for API calls
- Show request/response JSON
- Include authentication headers

## ✅ Checklist

- [ ] Login page screenshot
- [ ] Dashboard before operations
- [ ] Dashboard after fraud detection
- [ ] API documentation screenshot
- [ ] Grafana monitoring screenshot
- [ ] Database before transaction
- [ ] Database after transaction (account FROZEN)
- [ ] CRUD operation comparisons
- [ ] Before/After screenshots for each operation
- [ ] Explanations for each screenshot
- [ ] Code snippets showing operations
- [ ] Architecture diagram (optional)

## 📦 Submission Package

Organize your submission as follows:

```
submission/
├── README.md                    # This file
├── screenshots/
│   ├── 01-login.png
│   ├── 02-dashboard-initial.png
│   ├── 03-dashboard-updated.png
│   ├── 04-api-docs.png
│   ├── 05-grafana.png
│   ├── 06-db-before.png
│   ├── 07-db-after.png
│   └── ...
├── crud-comparisons/
│   ├── CREATE-operation.md
│   ├── READ-operation.md
│   ├── UPDATE-operation.md
│   └── DELETE-operation.md
└── README.md                    # Summary document
```

## 🎯 Quick Start for Submissions

Run these commands to prepare your submission:

```bash
# 1. Start the system
make up && make seed

# 2. Take all screenshots following the guide above

# 3. Run the demonstration script
python3 tools/test_fraud_detection.py

# 4. Document the results
```

Good luck with your submission! 🚀
