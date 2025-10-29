# 🗄️ FraudGuard - Database Relationships Visual Guide

## 📊 Complete Entity Relationship Overview

This document provides a visual reference for all database relationships across the FraudGuard system.

---

## 🎨 Entity Relationship Map

### **Legend**

```
┏━━━━━━━━━━┓  Primary entity
┃  ENTITY  ┃
┗━━━━━━━━━━┛

┌──────────┐  Secondary entity/collection
│  ENTITY  │
└──────────┘

PK = Primary Key
FK = Foreign Key
───> = One-to-Many relationship
···> = Logical/Cross-database reference
```

---

## 🏢 Oracle OLTP Database - Transactional Core

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ORACLE DATABASE                                │
│                     (Primary Transactional System)                       │
└─────────────────────────────────────────────────────────────────────────┘


                        ┏━━━━━━━━━━━━━━━━━━━━┓
                        ┃     ACCOUNTS       ┃
                        ┣━━━━━━━━━━━━━━━━━━━━┫
                        ┃ PK: id             ┃
                        ┃     customer_id    ┃
                        ┃     status ⭐      ┃
                        ┃     created_at     ┃
                        ┃     updated_at     ┃
                        ┗━━━━━━━━┯━━━━━━━━━━┛
                                 │
                                 │ 1
                                 │
             ┌───────────────────┴───────────────────┐
             │                                       │
             │                                       │
         * ┌─▼───────────────────────┐          * ┌─▼─────────────────────┐
           │    TRANSACTIONS         │            │    FRAUD_ALERTS       │
           ├─────────────────────────┤            ├───────────────────────┤
           │ PK: id                  │            │ PK: id                │
           │ FK: account_id          │            │ FK: account_id        │
           │     amount              │            │ FK: txn_id  ◄─────────┼────┐
           │     currency            │            │     rule_code         │    │
           │     merchant            │            │     severity ⚠️       │    │
           │     mcc                 │            │     reason            │    │
           │     channel             │            │     created_at        │    │
           │     device_id           │      ┌────►│     handled           │    │
           │     lat, lon 🌍         │      │     │     handled_at        │    │
           │     city, country       │      │     │     handled_by        │    │
           │     txn_time ⏰         │      │     └───────────────────────┘    │
           │     auth_code           │      │                                  │
           │     status              │      │ 1                                │
           │     created_at          │      │                                  │
           └─────────────────────────┘      │                                  │
                     │                      │                               *  │
                     └──────────────────────┘                                  │
                                                                                │
                                                                                │
┌─────────────────────────────────────────────────────────────────────────────┘
│
│  Triggers: When transaction amount > threshold or velocity spike
│            → fraud_alert record created
│
└─► Rule Examples:
    • VELOCITY_HIGH - Too many transactions in short time
    • GEO_JUMP - Geographic impossibility (e.g. NY → LA in 10 min)
    • AMOUNT_ANOMALY - Unusual transaction amount
    • TIME_ANOMALY - Transaction at unusual hour
    • DEVICE_CHANGE - Different device than usual
```

### **Key Points:**

| Table | Records/Day | Purpose | Indexes |
|-------|------------|---------|---------|
| accounts | ~1,000 | Customer account records | customer_id, status |
| transactions | ~1,000,000 | All transactions | account_id, txn_time, amount |
| fraud_alerts | ~10,000 | Suspicious transactions | account_id, handled, created_at |

---

## 📊 PostgreSQL OLAP Database - Analytics Engine

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         POSTGRESQL DATABASE                              │
│                    (Analytics & Data Warehouse)                          │
└─────────────────────────────────────────────────────────────────────────┘


        DIMENSION TABLES (Reference Data)
        ═════════════════════════════════

┌────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ DIM_ACCOUNT    │    │   DIM_TIME       │    │   DIM_GEO       │
├────────────────┤    ├──────────────────┤    ├─────────────────┤
│ PK: account_id │    │ PK: date_key     │    │ PK: geo_key     │
│     customer_id│    │     year         │    │     city        │
│     status     │    │     month        │    │     country     │
│     first_txn  │    │     day          │    │     lat, lon    │
└───────┬────────┘    │     day_of_week  │    └─────────────────┘
        │             │     is_weekend   │
        │             └──────────────────┘
        │
        │ References
        │
        │         FACT TABLE (Transaction Data)
        │         ═════════════════════════════
        │
        └──────────────────────────────────────────────────┐
                                                           │
                    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▼━━┓
                    ┃     FACT_TRANSACTIONS                 ┃
                    ┃   (Partitioned by day - 60 days)      ┃
                    ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
                    ┃ PK: txn_id, day                       ┃
                    ┃ FK: account_id                        ┃
                    ┃     amount                            ┃
                    ┃     currency                          ┃
                    ┃     mcc                               ┃
                    ┃     channel                           ┃
                    ┃     geom (PostGIS Geography)          ┃
                    ┃     city, country                     ┃
                    ┃     txn_time                          ┃
                    ┃     day (generated, partition key)    ┃
                    ┃     hour (generated)                  ┃
                    ┃     status                            ┃
                    ┗━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━┛
                                  │
                                  │ Analyzed by
                                  │
                          ┌───────▼────────┐
                          │ ANOMALY_EVENTS │
                          ├────────────────┤
                          │ PK: id (UUID)  │
                          │ FK: account_id │
                          │ FK: txn_id     │
                          │     rule       │
                          │     score      │
                          │     severity   │
                          │     extra 📝   │
                          └────────────────┘


        MATERIALIZED VIEWS (Pre-computed Analytics)
        ═══════════════════════════════════════════

┌──────────────────────────┐  ┌───────────────────────┐  ┌──────────────────────┐
│ MV_AMOUNT_BUCKETS_HOURLY │  │ MV_VELOCITY_BY_ACCOUNT│  │ MV_TIME_OF_DAY_STATS │
├──────────────────────────┤  ├───────────────────────┤  ├──────────────────────┤
│ • hour                   │  │ • account_id          │  │ • hour               │
│ • bucket (0-10, 10-50..) │  │ • hour_window         │  │ • total_txns         │
│ • txn_count              │  │ • txn_count           │  │ • avg_amount         │
│ • total_amount           │  │ • p95_amount          │  │ • std_amount         │
└──────────────────────────┘  └───────────────────────┘  │ • min/max            │
                                                          │ • median_amount      │
     Dashboard Charts             Velocity Detection      └──────────────────────┘
                                                              Time Patterns


        ETL TRACKING
        ════════════

┌─────────────────┐
│ ETL_CHECKPOINTS │
├─────────────────┤
│ PK: id          │
│     source_table│  ← "transactions"
│     last_id     │  ← Last synced transaction ID from Oracle
│     last_ts     │  ← Last sync timestamp
│     updated_at  │
└─────────────────┘
```

### **Data Flow: Oracle → PostgreSQL**

```
┌─────────────────┐
│  ETL Worker     │  Runs every 5 minutes
├─────────────────┤
│                 │
│ 1. Check last_id from etl_checkpoints
│ 2. Query Oracle: SELECT * FROM transactions WHERE id > last_id
│ 3. Transform:
│    • Convert lat/lon → PostGIS geography
│    • Extract time dimensions
│    • Calculate derived fields
│ 4. Load into fact_transactions
│ 5. Update etl_checkpoints
│ 6. Refresh materialized views
│                 │
└─────────────────┘
```

---

## 📄 MongoDB NoSQL Database - Document Store

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           MONGODB DATABASE                               │
│                  (Flexible Document Storage for Cases)                   │
└─────────────────────────────────────────────────────────────────────────┘


                    ┏━━━━━━━━━━━━━━━━━━━━━━━━━┓
                    ┃     FRAUD_CASES         ┃
                    ┣━━━━━━━━━━━━━━━━━━━━━━━━━┫
                    ┃ _id: ObjectId           ┃
                    ┃ caseId: "CASE-2025-001" ┃
                    ┃ accountId: 12345 ◄──────┼────┐ References Oracle
                    ┃ txnIds: [101, 102, ..] ◄┼────┤ ACCOUNTS.id
                    ┃ investigator: "john@co" ┃    │
                    ┃ status: "INVESTIGATING" ┃    │ References Oracle
                    ┃ tags: ["high-risk", ..] ┃    │ TRANSACTIONS.id
                    ┃                         ┃    │
                    ┃ notes: [                ┃    │
                    ┃   {                     ┃    │
                    ┃     author: "jane@co"   ┃    │
                    ┃     content: "..."      ┃    │
                    ┃     createdAt: Date     ┃    │
                    ┃   },                    ┃    │
                    ┃   ...                   ┃    │
                    ┃ ]                       ┃    │
                    ┃                         ┃    │
                    ┃ attachments: [          ┃    │
                    ┃   {                     ┃    │
                    ┃     gridFsId: "..."     ┃────┼─► GridFS (File Storage)
                    ┃     filename: "ev.pdf"  ┃    │
                    ┃     contentType: "pdf"  ┃    │
                    ┃   }                     ┃    │
                    ┃ ]                       ┃    │
                    ┃                         ┃    │
                    ┃ createdAt: Date         ┃    │
                    ┃ updatedAt: Date         ┃    │
                    ┗━━━━━━━━━┯━━━━━━━━━━━━━━━┛    │
                              │                    │
                              │ Can generate       │
                              │                    │
                    ┌─────────▼─────────┐          │
                    │   SAR_REPORTS     │          │
                    ├───────────────────┤          │
                    │ _id: ObjectId     │          │
                    │ reportId: "..."   │          │
                    │ accountId: 12345 ◄┼──────────┘
                    │ suspiciousActivity│
                    │ amount: 50000     │
                    │ reportDate: Date  │
                    │ filedBy: "..."    │
                    │ status: "DRAFT"   │
                    └───────────────────┘


┌────────────────────────┐          ┌───────────────────┐
│  CUSTOMER_COMPLAINTS   │          │   SYSTEM_LOGS     │
├────────────────────────┤          │   (TTL: 30 days)  │
│ _id: ObjectId          │          ├───────────────────┤
│ complaintId: "..."     │          │ _id: ObjectId     │
│ customerId: "..."      │          │ level: "INFO"     │
│ accountId: 12345 ◄─────┼───┐      │ message: "..."    │
│ subject: "..."         │   │      │ module: "..."     │
│ description: "..."     │   │      │ createdAt: Date   │
│ status: "OPEN"         │   │      └───────────────────┘
│ priority: "HIGH"       │   │             ▲
│ createdAt: Date        │   │             │
└────────────────────────┘   │             │ Auto-delete after 30 days
                             │             │ (MongoDB TTL Index)
                             │
                             │ References Oracle ACCOUNTS.id
                             │
```

### **Document Embedding Strategy**

```
Why embed notes[] and attachments[]?
───────────────────────────────────

✅ Advantages:
   • Single query to get complete case
   • Atomic updates
   • No joins needed
   • Matches access pattern (always load full case)

❌ When NOT to embed:
   • If notes/attachments are accessed independently
   • If array grows unbounded (>100 items)
   • If updates to sub-documents are frequent

In FraudGuard:
   ✓ Cases typically have < 50 notes
   ✓ Attachments < 20 per case
   ✓ Always accessed together
   → Perfect for embedding
```

---

## 🔗 Cross-Database Relationships

```
┌─────────────────────────────────────────────────────────────────────────┐
│              HOW DATABASES WORK TOGETHER                                 │
└─────────────────────────────────────────────────────────────────────────┘


   ORACLE (OLTP)              POSTGRESQL (OLAP)           MONGODB (NoSQL)
   ═════════════              ═════════════════           ═══════════════

┏━━━━━━━━━━━━┓                                         ┌──────────────┐
┃  ACCOUNTS  ┃ ─────ETL────► DIM_ACCOUNT              │ FRAUD_CASES  │
┃  id: 1001  ┃               account_id: 1001         │ accountId:   │
┗━━━━━━━━━━━━┛                                         │   1001       │
      │                                                └──────────────┘
      │                                                       ▲
      │ 1                                                     │
      │                                                       │
      │ *                                                     │
┏━━━━━━━━━━━━┓                                               │
┃TRANSACTIONS┃                                               │
┃  id: 5001  ┃ ─────ETL────► FACT_TRANSACTIONS              │
┃  id: 5002  ┃               txn_id: 5001                   │
┃  ...       ┃               txn_id: 5002            ┌──────────────┐
┗━━━━━━━━━━━━┛               ...                     │ FRAUD_CASES  │
                                                     │ txnIds:      │
                                                     │   [5001,     │
                                                     │    5002]     │
                                                     └──────────────┘


    REAL-TIME                 BATCH (5 min)             APPLICATION
    ─────────                 ──────────────            ────────────
    Write-heavy               Read-heavy                Flexible
    Low latency               Complex queries           Investigations


┌─────────────────────────────────────────────────────────────────────────┐
│  EXAMPLE: Creating a Fraud Case                                         │
└─────────────────────────────────────────────────────────────────────────┘

Step 1: Analyst views alert in Oracle
    SELECT * FROM fraud_alerts WHERE handled = 0 ORDER BY severity DESC;
    
Step 2: Analyst creates case in MongoDB
    db.fraud_cases.insert({
        caseId: "CASE-2025-001",
        accountId: 1001,         ← References Oracle
        txnIds: [5001, 5002],    ← References Oracle
        investigator: "analyst@co",
        status: "INVESTIGATING",
        notes: [],
        attachments: []
    })
    
Step 3: Application joins data for display
    // Fetch case from MongoDB
    case = db.fraud_cases.findOne({caseId: "CASE-2025-001"})
    
    // Fetch account from Oracle
    account = oracle.query("SELECT * FROM accounts WHERE id = ?", [case.accountId])
    
    // Fetch transactions from Oracle
    txns = oracle.query("SELECT * FROM transactions WHERE id IN (?)", [case.txnIds])
    
    // Fetch analytics from PostgreSQL
    analytics = postgres.query(
        "SELECT * FROM fact_transactions WHERE txn_id IN (?)", 
        [case.txnIds]
    )
    
    // Return combined data to UI
    return {
        case: case,
        account: account,
        transactions: txns,
        analytics: analytics
    }
```

---

## 📈 Data Volume & Growth

```
┌──────────────┬─────────────┬─────────────┬───────────────┬──────────────┐
│ Table/Coll   │ Current     │ Daily Growth│ Retention     │ Storage      │
├──────────────┼─────────────┼─────────────┼───────────────┼──────────────┤
│ transactions │ 100M        │ 1M          │ 7 years       │ 500 GB       │
│ fraud_alerts │ 10M         │ 10K         │ 7 years       │ 50 GB        │
│ fraud_cases  │ 50K         │ 100         │ Permanent     │ 5 GB         │
│ fact_txns    │ 100M        │ 1M          │ 2 years       │ 300 GB       │
│ anomalies    │ 5M          │ 5K          │ 2 years       │ 10 GB        │
│ system_logs  │ Rolling     │ 1 GB        │ 30 days       │ 30 GB        │
└──────────────┴─────────────┴─────────────┴───────────────┴──────────────┘
```

---

## 🎯 Query Patterns

### **Common Queries by Database**

**Oracle (OLTP):**
```sql
-- Get unhandled alerts
SELECT * FROM fraud_alerts 
WHERE handled = 0 
ORDER BY severity DESC, created_at DESC;

-- Get account transactions (last 30 days)
SELECT * FROM transactions 
WHERE account_id = ? 
  AND txn_time > SYSDATE - 30
ORDER BY txn_time DESC;

-- Transaction details with alert
SELECT t.*, a.rule_code, a.severity, a.reason
FROM transactions t
LEFT JOIN fraud_alerts a ON t.id = a.txn_id
WHERE t.id = ?;
```

**PostgreSQL (OLAP):**
```sql
-- Fraud trends over time
SELECT DATE(txn_time) as date, 
       COUNT(*) as fraud_count,
       SUM(amount) as fraud_amount
FROM fact_transactions f
JOIN anomaly_events a ON f.txn_id = a.txn_id
WHERE txn_time > NOW() - INTERVAL '30 days'
GROUP BY DATE(txn_time)
ORDER BY date;

-- Top risky merchants
SELECT mcc, COUNT(*) as fraud_count
FROM fact_transactions f
JOIN anomaly_events a ON f.txn_id = a.txn_id
WHERE f.txn_time > NOW() - INTERVAL '90 days'
GROUP BY mcc
ORDER BY fraud_count DESC
LIMIT 10;

-- Geographic distribution
SELECT country, city, COUNT(*) as count
FROM fact_transactions
WHERE status = 'DECLINED'
GROUP BY country, city
ORDER BY count DESC;
```

**MongoDB (NoSQL):**
```javascript
// Find open cases assigned to analyst
db.fraud_cases.find({
    investigator: "analyst@company.com",
    status: {$in: ["OPEN", "INVESTIGATING"]}
}).sort({createdAt: -1})

// Full-text search in case notes
db.fraud_cases.find({
    $text: {$search: "wire transfer"}
})

// Get cases for account
db.fraud_cases.find({
    accountId: 1001
}).sort({createdAt: -1})
```

---

## 🔍 Indexes Reference

### **Oracle Indexes**

| Index | Table | Columns | Purpose |
|-------|-------|---------|---------|
| idx_accounts_customer_id | accounts | customer_id | Customer lookup |
| idx_accounts_status | accounts | status | Filter by status |
| idx_txns_account_id | transactions | account_id | Account history |
| idx_txns_time | transactions | txn_time | Time-based queries |
| idx_txns_amount | transactions | amount | Amount range searches |
| idx_alerts_account | fraud_alerts | account_id | Alert by account |
| idx_alerts_handled | fraud_alerts | handled, created_at | Unhandled alerts |

### **PostgreSQL Indexes**

| Index | Table | Columns | Type | Purpose |
|-------|-------|---------|------|---------|
| idx_fact_account_date | fact_transactions | account_id, txn_time | B-tree | Account history |
| idx_fact_amount | fact_transactions | amount | B-tree | Amount filtering |
| idx_fact_geo | fact_transactions | geom | GIST | Geospatial queries |
| idx_fact_city | fact_transactions | city, country | B-tree | Location filtering |
| idx_anomalies_account | anomaly_events | account_id, detected_at | B-tree | Account anomalies |
| idx_anomalies_rule | anomaly_events | rule, detected_at | B-tree | Rule analysis |

### **MongoDB Indexes**

| Index | Collection | Fields | Type | Purpose |
|-------|------------|--------|------|---------|
| Text Index | fraud_cases | notes.content | Text | Full-text search |
| Compound | fraud_cases | status, createdAt | Compound | Status filtering |
| Compound | fraud_cases | accountId, createdAt | Compound | Account cases |
| Single | fraud_cases | investigator | Single | Assigned cases |
| TTL | system_logs | createdAt | TTL | Auto-deletion |

---

## 📝 Summary

### **Database Roles**

| Database | Role | Strengths | Use Cases |
|----------|------|-----------|-----------|
| **Oracle** | Primary OLTP | • ACID compliance<br>• High write throughput<br>• Enterprise reliability | • Transaction recording<br>• Real-time alerts<br>• Account management |
| **PostgreSQL** | Analytics OLAP | • Complex queries<br>• Geospatial support<br>• Materialized views | • Dashboards<br>• Trends analysis<br>• Geographic analytics |
| **MongoDB** | Document Store | • Flexible schema<br>• Embedded documents<br>• Full-text search | • Case management<br>• Investigation notes<br>• SAR reports |

### **Key Relationships**

1. **accounts (Oracle) → transactions (Oracle)** - One account has many transactions
2. **transactions (Oracle) → fraud_alerts (Oracle)** - One transaction can trigger multiple alerts
3. **accounts (Oracle) → dim_account (PostgreSQL)** - ETL synchronization
4. **transactions (Oracle) → fact_transactions (PostgreSQL)** - ETL synchronization
5. **accounts (Oracle) ↔ fraud_cases (MongoDB)** - Logical reference (application layer)
6. **transactions (Oracle) ↔ fraud_cases (MongoDB)** - Logical reference (application layer)

---

**Created:** October 29, 2025  
**Version:** 1.0  
**Project:** FraudGuard 2.0.0

