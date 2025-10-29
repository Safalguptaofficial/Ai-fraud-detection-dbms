# CRUD Operations - Database State Comparison

This document demonstrates how the database state changes after each CRUD operation in the fraud detection system.

## CREATE Operations

### Example 1: Create Account

#### Before:
```sql
-- accounts table
account_id | customer_id | status  | balance
-----------|-------------|---------|----------
1          | CUST001     | ACTIVE  | 10000.00
2          | CUST002     | ACTIVE  | 25000.00
3          | CUST003     | ACTIVE  | 15000.00
```

#### Operation:
```bash
POST /v1/accounts
{
  "account_id": "ACC004",
  "customer_id": "CUST004",
  "account_type": "CHECKING",
  "balance": 5000.00
}
```

#### After:
```sql
-- accounts table
account_id | customer_id | status  | balance
-----------|-------------|---------|----------
1          | CUST001     | ACTIVE  | 10000.00
2          | CUST002     | ACTIVE  | 25000.00
3          | CUST003     | ACTIVE  | 15000.00
4          | CUST004     | ACTIVE  | 5000.00  ← NEW
```

**Database Changes**:
- ✅ New row inserted in `accounts` table
- ✅ Status set to 'ACTIVE' by default
- ✅ Sequence incremented

---

### Example 2: Create Transaction (Normal)

#### Before:
```sql
-- transactions table count: 100
-- accounts table
account_id | status
-----------|----------
1          | ACTIVE

-- fraud_alerts table count: 4
```

#### Operation:
```bash
POST /v1/transactions
{
  "account_id": 1,
  "amount": 100.00,
  "merchant": "Starbucks",
  "txn_time": "2025-01-15T14:30:00Z"
}
```

#### After:
```sql
-- transactions table count: 101  ← +1
-- accounts table (no change)
account_id | status
-----------|----------
1          | ACTIVE

-- fraud_alerts table count: 4 (no change)
```

**Database Changes**:
- ✅ New transaction record inserted
- ✅ Transaction status: 'PENDING'
- ✅ No fraud detected (amount < $5000, normal time)
- ✅ No account status change
- ✅ Redis cache invalidated for `/v1/transactions` endpoint

---

### Example 3: Create Transaction (Fraudulent) - TRIGGER FIRES ⚠️

#### Before:
```sql
-- transactions table count: 101
-- accounts table
account_id | status
-----------|----------
1          | ACTIVE

-- fraud_alerts table count: 4
alert_id | account_id | rule_code      | severity | status
---------|------------|----------------|----------|----------
1        | 2          | VELOCITY_HIGH  | HIGH     | OPEN
2        | 1          | GEO_JUMP       | MEDIUM   | OPEN
3        | 3          | AMOUNT_ANOMALY | HIGH     | OPEN
4        | 4          | TIME_ANOMALY   | LOW      | OPEN
```

#### Operation:
```bash
POST /v1/transactions
{
  "account_id": 1,
  "amount": 8000.00,        ← Suspicious: High amount
  "merchant": "ATM-CORP",
  "txn_time": "2025-01-15T01:30:00Z",  ← Suspicious: Midnight
  "auth_code": "AUTH002"
}
```

#### After (Automatically Triggered by PL/SQL):
```sql
-- transactions table count: 102  ← +1

-- accounts table (AUTOMATIC CHANGE)
account_id | status
-----------|----------
1          | FROZEN   ← CHANGED FROM ACTIVE

-- fraud_alerts table (AUTOMATIC INSERTION)
alert_id | account_id | rule_code                | severity | status  | reason
---------|------------|--------------------------|----------|---------|-------------------
1        | 2          | VELOCITY_HIGH            | HIGH     | OPEN    | 
2        | 1          | GEO_JUMP                 | MEDIUM   | OPEN    | 
3        | 3          | AMOUNT_ANOMALY           | HIGH     | OPEN    | 
4        | 4          | TIME_ANOMALY             | LOW      | OPEN    | 
5        | 1          | AMOUNT_GT_5000_MIDNIGHT  | HIGH     | OPEN    | ← NEW ALERT

-- system_logs table (AUTOMATIC)
log_id | account_id | event_type | event_time
-------|------------|------------|------------------
...    | 1          | ACCOUNT_FROZEN | 2025-01-15 01:30:15
```

**Database Changes**:
- ✅ New transaction record inserted
- ✅ **PL/SQL Trigger AUTOMATICALLY fired**
- ✅ Account status changed from ACTIVE to FROZEN
- ✅ New fraud alert created with severity=HIGH
- ✅ Alert reason: "AMOUNT_GT_5000_MIDNIGHT"
- ✅ System log entry created for audit trail
- ✅ Frontend dashboard automatically updates (within 5 seconds)

**Trigger Logic**:
```sql
-- Simplified trigger logic
IF transaction_amount > 5000 AND transaction_time BETWEEN '00:00' AND '05:00' THEN
    UPDATE accounts SET status = 'FROZEN' WHERE account_id = :account_id;
    INSERT INTO fraud_alerts (...) VALUES (...);
END IF;
```

---

## READ Operations

### Example 1: List All Accounts

#### Operation:
```bash
GET /v1/accounts
```

#### Response:
```json
[
  {
    "account_id": "ACC001",
    "customer_id": "CUST001",
    "status": "ACTIVE",
    "balance": 10000.00
  },
  {
    "account_id": "ACC002",
    "customer_id": "CUST002",
    "status": "FROZEN",
    "balance": 0.00
  }
]
```

**Database State**: No changes (READ operation)

**Cache Behavior**:
- ✅ First request hits database
- ✅ Result cached in Redis for 5 minutes
- ✅ Subsequent requests served from cache
- ✅ Cache automatically invalidated when data changes

---

### Example 2: Get Fraud Alerts with Filter

#### Operation:
```bash
GET /v1/alerts?status=open&severity=HIGH
```

#### Response:
```json
[
  {
    "id": 1,
    "account_id": 2,
    "rule_code": "VELOCITY_HIGH",
    "severity": "HIGH",
    "status": "OPEN",
    "created_at": "2025-01-15T06:14:40Z"
  },
  {
    "id": 5,
    "account_id": 1,
    "rule_code": "AMOUNT_GT_5000_MIDNIGHT",
    "severity": "HIGH",
    "status": "OPEN",
    "created_at": "2025-01-15T01:30:15Z"
  }
]
```

**Database State**: No changes (READ operation)

---

## UPDATE Operations

### Example 1: Update Account Status

#### Before:
```sql
-- accounts table
account_id | status
-----------|----------
1          | ACTIVE
```

#### Operation:
```bash
PATCH /v1/accounts/1
{
  "status": "FROZEN"
}
```

#### After:
```sql
-- accounts table
account_id | status
-----------|----------
1          | FROZEN   ← UPDATED
```

**Database Changes**:
- ✅ Account status updated in database
- ✅ Audit log entry created
- ✅ Frontend dashboard updates on next refresh
- ✅ Cache cleared for this account

**Use Case**: Manual freeze of account by analyst due to investigation

---

### Example 2: Update Alert Status (Investigation Started)

#### Before:
```sql
-- fraud_alerts table
alert_id | status
---------|----------
5        | OPEN
```

#### Operation:
```bash
PATCH /v1/alerts/5
{
  "status": "INVESTIGATING",
  "assigned_to": "analyst@bank.com"
}
```

#### After:
```sql
-- fraud_alerts table
alert_id | status
---------|----------
5        | INVESTIGATING   ← UPDATED

-- case_assignments table
case_id | alert_id | assigned_to | assigned_at
--------|----------|-------------|------------------
1       | 5        | analyst@bank.com | 2025-01-15 10:00:00
```

**Database Changes**:
- ✅ Alert status updated
- ✅ Investigation record created
- ✅ Workflow moved to next stage
- ✅ Available for case management

---

## DELETE Operations

### Example 1: Clear Redis Cache (Soft Delete)

#### Operation:
```bash
POST /v1/transactions/cache/clear
```

#### Before:
```redis
KEYS api:*
→ api:/transactions:None_100_0 (TTL: 280)
→ api:/transactions:1_100_0 (TTL: 150)
→ api:/accounts:None_100_0 (TTL: 300)
```

#### After:
```redis
KEYS api:*
→ (empty)
```

**Database State**: No changes to actual data (cache cleared)

**Effect**: Next requests will query database fresh

---

### Example 2: Account Closure (Status Change)

#### Operation:
```bash
PATCH /v1/accounts/2
{
  "status": "CLOSED"
}
```

#### Before:
```sql
-- accounts table
account_id | status
-----------|----------
2          | FROZEN
```

#### After:
```sql
-- accounts table
account_id | status
-----------|----------
2          | CLOSED   ← UPDATED

-- archived_accounts table
account_id | closed_at | closed_by
-----------|-----------|-----------
2          | 2025-01-15 | system
```

**Database Changes**:
- ✅ Account status updated to CLOSED
- ✅ Account archived to separate table
- ✅ Historical data preserved
- ✅ Active transactions cancelled

---

## Summary Table

| Operation | Before | Action | After | Trigger Effects |
|-----------|--------|--------|-------|-----------------|
| **CREATE** | 5 accounts | Insert account | 6 accounts | ✅ New record |
| **CREATE** | 101 txns | Insert txn (normal) | 102 txns | ✅ New record only |
| **CREATE** | 101 txns<br>1 ACTIVE account<br>4 alerts | Insert txn (fraud) | 102 txns<br>1 FROZEN account<br>5 alerts | ✅ New record<br>⚠️ Status change<br>⚠️ Alert created |
| **READ** | Any | Query data | No change | ✅ Cache on 2nd request |
| **UPDATE** | Status=ACTIVE | Update to FROZEN | Status=FROZEN | ✅ Audit log |
| **UPDATE** | Status=OPEN | Update to INVESTIGATING | Status=INVESTIGATING | ✅ Case assignment |
| **DELETE** | Cache populated | Clear cache | Cache empty | ✅ Fresh queries |

---

## Key Observations

1. **Automatic Trigger Execution**: Fraudulent transactions trigger multiple database changes automatically
2. **Cascade Effects**: Account status changes affect alert creation and audit logging
3. **Audit Trail**: All operations are logged in `system_logs` table
4. **Cache Invalidation**: Updates automatically clear related cache
5. **Real-time Updates**: Frontend receives changes within 5 seconds via polling

This demonstrates the power of the hybrid DBMS approach with automatic fraud detection!
