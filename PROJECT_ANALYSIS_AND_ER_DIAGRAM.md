# 🛡️ FraudGuard - Project Analysis & ER Diagram

## 📋 Executive Summary

**FraudGuard** is an enterprise-grade, AI-powered fraud detection platform that combines real-time transaction monitoring, machine learning risk assessment, and collaborative investigation tools. The system uses a multi-database architecture with Oracle for OLTP operations, PostgreSQL for analytics, and MongoDB for document-based case management.

---

## 🏗️ System Architecture Analysis

### **Tech Stack**

#### Frontend
- **Framework:** Next.js 14 (React)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Visualization:** Recharts, React Leaflet
- **State Management:** React Query

#### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Validation:** Pydantic
- **ML Libraries:** NumPy, Pandas, Scikit-learn
- **Authentication:** JWT (python-jose)
- **Monitoring:** Prometheus

#### Databases
1. **Oracle** - Primary transactional database (OLTP)
2. **PostgreSQL** - Analytics and data warehousing (OLAP)
3. **MongoDB** - Document storage for cases and investigations

---

## 🎯 Core Features

### 1. **Real-Time Fraud Detection**
- ML-powered risk scoring using ensemble models
- Transaction velocity monitoring
- Geographic anomaly detection
- Merchant category code (MCC) analysis

### 2. **Machine Learning Models**
- **Isolation Forest** (40% weight) - Anomaly detection
- **Rule-Based System** (30% weight) - Business logic rules
- **Velocity Model** (30% weight) - Transaction frequency analysis

### 3. **Investigation Workspace**
- Case management with MongoDB
- Timeline visualization
- Evidence attachment storage
- Collaborative note-taking

### 4. **Role-Based Access Control (RBAC)**
- **ADMIN** - Full system access
- **MANAGER** - Team management, approvals
- **ANALYST** - Alert review, case creation
- **VIEWER** - Read-only access

### 5. **Advanced Analytics**
- Interactive dashboards
- Fraud trends visualization
- Geographic fraud mapping
- Network graph for fraud ring detection
- Transaction heatmaps

### 6. **User Experience**
- Dark mode support
- Command palette (Cmd+K shortcuts)
- AI chatbot for natural language queries
- Bulk actions on alerts
- Professional PDF/CSV exports

---

## 📊 Database Architecture

### **Multi-Database Strategy**

#### **Oracle Database (OLTP)**
**Purpose:** Primary transactional system for high-volume, real-time operations

**Tables:**
- `accounts` - Customer account information
- `transactions` - Transaction records with device, location, and merchant data
- `fraud_alerts` - Alert records linked to transactions
- `system_logs` - Application logging

**Characteristics:**
- High write throughput
- ACID compliance
- Real-time data ingestion
- Sequence-based ID generation

#### **PostgreSQL (OLAP)**
**Purpose:** Analytics, data warehousing, and complex queries

**Schema Components:**

**Dimension Tables:**
- `dim_account` - Account dimension
- `dim_time` - Time dimension
- `dim_geo` - Geographic dimension

**Fact Tables:**
- `fact_transactions` - Partitioned by day (60-day rolling partitions)

**Materialized Views:**
- `mv_amount_buckets_hourly` - Transaction amount distribution
- `mv_velocity_by_account` - Transaction velocity metrics
- `mv_time_of_day_stats` - Time-based transaction patterns

**Special Tables:**
- `anomaly_events` - Detected anomalies with scoring
- `etl_checkpoints` - ETL process tracking

**Features:**
- PostGIS for geospatial queries
- Partitioned tables for performance
- Materialized views for fast analytics
- JSONB support for flexible data

#### **MongoDB (NoSQL)**
**Purpose:** Document storage for flexible, schema-less data

**Collections:**
- `fraud_cases` - Case management with nested documents
- `sar_reports` - Suspicious Activity Reports
- `customer_complaints` - Customer feedback and complaints
- `system_logs` - Application logs with TTL (30-day retention)

**Features:**
- Text search on case notes
- Schema validation with JSON Schema
- Array and embedded document support
- GridFS for file attachments
- TTL indexes for automatic data expiration

---

## 🔄 Data Flow

```
1. Transaction Creation
   └─> Oracle (transactions table)
       └─> Real-time ML Risk Scoring
           └─> Alert Generation (fraud_alerts table)
               └─> PostgreSQL ETL (fact_transactions)

2. Case Investigation
   └─> MongoDB (fraud_cases collection)
       └─> Evidence & Notes
           └─> SAR Report Generation

3. Analytics & Reporting
   └─> PostgreSQL (Materialized Views)
       └─> Dashboard Visualization
           └─> Trend Analysis
```

---

## 🗂️ Entity-Relationship Diagram

### **ER Diagram - Oracle OLTP Schema**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ORACLE OLTP DATABASE                              │
└─────────────────────────────────────────────────────────────────────────┘

┏━━━━━━━━━━━━━━━━━━━━━━━━┓
┃      ACCOUNTS          ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ PK  id (NUMBER)        ┃──┐
┃     customer_id        ┃  │
┃     status             ┃  │
┃     created_at         ┃  │  1
┃     updated_at         ┃  │
┗━━━━━━━━━━━━━━━━━━━━━━━━┛  │
                            │
                            │ has many
                            │
        ┌───────────────────┴────────────────────┐
        │                                        │
        │ *                                      │ *
        ▼                                        ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━┓          ┏━━━━━━━━━━━━━━━━━━━━━━━━┓
┃     TRANSACTIONS       ┃          ┃    FRAUD_ALERTS        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━┫          ┣━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ PK  id (NUMBER)        ┃──┐       ┃ PK  id (NUMBER)        ┃
┃ FK  account_id         ┃  │       ┃ FK  account_id         ┃
┃     amount             ┃  │       ┃ FK  txn_id             ┃◄──┐
┃     currency           ┃  │       ┃     rule_code          ┃   │
┃     merchant           ┃  │  1    ┃     severity           ┃   │ 1
┃     mcc                ┃  │       ┃     reason             ┃   │
┃     channel            ┃  ├──────►┃     created_at         ┃   │
┃     device_id          ┃  │   *   ┃     handled            ┃   │
┃     lat, lon           ┃  │       ┃     handled_at         ┃   │
┃     city, country      ┃  │       ┃     handled_by         ┃   │
┃     txn_time           ┃  │       ┗━━━━━━━━━━━━━━━━━━━━━━━━┛   │
┃     auth_code          ┃  │                                    │
┃     status             ┃  │       triggers                     │
┃     created_at         ┃  └────────────────────────────────────┘
┗━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━┓
┃     SYSTEM_LOGS        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ PK  id (NUMBER)        ┃
┃     level              ┃
┃     message            ┃
┃     created_at         ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### **ER Diagram - PostgreSQL OLAP Schema**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    POSTGRESQL OLAP DATABASE                              │
└─────────────────────────────────────────────────────────────────────────┘

DIMENSION TABLES:

┏━━━━━━━━━━━━━━━━━━━━━━━━┓    ┏━━━━━━━━━━━━━━━━━━━━━━━━┓    ┏━━━━━━━━━━━━━━━━━━━━━━━━┓
┃    DIM_ACCOUNT         ┃    ┃       DIM_TIME         ┃    ┃      DIM_GEO           ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━┫    ┣━━━━━━━━━━━━━━━━━━━━━━━━┫    ┣━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ PK  account_id         ┃    ┃ PK  date_key           ┃    ┃ PK  geo_key            ┃
┃     customer_id        ┃    ┃     year               ┃    ┃     city               ┃
┃     status             ┃    ┃     month              ┃    ┃     country            ┃
┃     first_txn_date     ┃    ┃     day                ┃    ┃     lat, lon           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━┛    ┃     day_of_week        ┃    ┗━━━━━━━━━━━━━━━━━━━━━━━━┛
                              ┃     is_weekend         ┃
                              ┗━━━━━━━━━━━━━━━━━━━━━━━━┛

FACT TABLE (Partitioned by Day):

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                     FACT_TRANSACTIONS                          ┃
┃                  (Partitioned by day field)                    ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ PK  txn_id, day (composite)                                   ┃
┃ FK  account_id  ────────┐                                      ┃
┃     amount              │                                      ┃
┃     currency            │                                      ┃
┃     mcc                 │                                      ┃
┃     channel             │                                      ┃
┃     geom (Geography)    │  References dim_account              ┃
┃     city, country       │                                      ┃
┃     txn_time            │                                      ┃
┃     day (generated)     │                                      ┃
┃     hour (generated)    │                                      ┃
┃     status              │                                      ┃
┃     created_at          │                                      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                          │
                          │ analyzed by
                          ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                     ANOMALY_EVENTS                             ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ PK  id (UUID)                                                  ┃
┃ FK  account_id                                                 ┃
┃ FK  txn_id                                                     ┃
┃     rule                                                       ┃
┃     score                                                      ┃
┃     detected_at                                                ┃
┃     severity                                                   ┃
┃     extra (JSONB)                                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

MATERIALIZED VIEWS (for fast analytics):

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  MV_AMOUNT_BUCKETS_HOURLY         ┃   Pre-computed aggregations
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫   for dashboard performance
┃  hour, bucket, txn_count, amount  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  MV_VELOCITY_BY_ACCOUNT           ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  account_id, hour, txn_count, p95 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  MV_TIME_OF_DAY_STATS             ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  hour, stats (avg, std, min, max) ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

ETL TRACKING:

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃      ETL_CHECKPOINTS              ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ PK  id                            ┃
┃     source_table                  ┃
┃     last_id                       ┃
┃     last_timestamp                ┃
┃     updated_at                    ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### **ER Diagram - MongoDB NoSQL Schema**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       MONGODB DOCUMENT DATABASE                          │
└─────────────────────────────────────────────────────────────────────────┘

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                           FRAUD_CASES                                  ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  _id: ObjectId                                                         ┃
┃  caseId: String (unique)                                               ┃
┃  accountId: Integer ─────┐  References Oracle accounts                ┃
┃  txnIds: [Integer]       │  References Oracle transactions            ┃
┃  investigator: String    │                                             ┃
┃  status: Enum            │                                             ┃
┃  tags: [String]          │                                             ┃
┃  notes: [                │  Embedded documents                         ┃
┃    {                     │                                             ┃
┃      author: String      │                                             ┃
┃      content: String     │                                             ┃
┃      createdAt: Date     │                                             ┃
┃    }                     │                                             ┃
┃  ]                       │                                             ┃
┃  attachments: [          │  Embedded documents                         ┃
┃    {                     │                                             ┃
┃      gridFsId: String    │  References GridFS files                   ┃
┃      filename: String    │                                             ┃
┃      contentType: String │                                             ┃
┃    }                     │                                             ┃
┃  ]                       │                                             ┃
┃  createdAt: Date         │                                             ┃
┃  updatedAt: Date         │                                             ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
                           │
                           │ can generate
                           ▼
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                          SAR_REPORTS                                   ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  _id: ObjectId                                                         ┃
┃  reportId: String (unique)                                             ┃
┃  accountId: Integer          References Oracle accounts                ┃
┃  suspiciousActivity: String                                            ┃
┃  amount: Double                                                        ┃
┃  reportDate: Date                                                      ┃
┃  filedBy: String                                                       ┃
┃  status: Enum                                                          ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                     CUSTOMER_COMPLAINTS                                ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  _id: ObjectId                                                         ┃
┃  complaintId: String (unique)                                          ┃
┃  customerId: String              References Oracle accounts            ┃
┃  accountId: Integer                                                    ┃
┃  subject: String                                                       ┃
┃  description: String                                                   ┃
┃  status: Enum                                                          ┃
┃  priority: Enum                                                        ┃
┃  createdAt: Date                                                       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                        SYSTEM_LOGS                                     ┃
┃                   (TTL Index: 30 days)                                 ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  _id: ObjectId                                                         ┃
┃  level: String                                                         ┃
┃  message: String                                                       ┃
┃  module: String                                                        ┃
┃  createdAt: Date                                                       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### **Cross-Database Relationships**

```
┌──────────────────────────────────────────────────────────────────────┐
│                    CROSS-DATABASE REFERENCES                          │
└──────────────────────────────────────────────────────────────────────┘

ORACLE                      POSTGRESQL                    MONGODB
  │                            │                            │
  │ accounts.id                │ dim_account.account_id     │ fraud_cases.accountId
  │ (Integer)                  │ (Integer)                  │ (Integer)
  ├───────────────────────────►│                            │
  └────────────────────────────┼───────────────────────────►│
                               │                            │
  │ transactions.id            │ fact_transactions.txn_id   │ fraud_cases.txnIds[]
  │ (Integer)                  │ (Integer)                  │ (Array of Integers)
  ├───────────────────────────►│                            │
  └────────────────────────────┼───────────────────────────►│
                               │                            │
  ETL Process:                 │                            │
  Oracle → PostgreSQL          │                            │
  (Scheduled batch jobs)       │                            │
                               │                            │
  Application Layer:           │                            │
  Joins data across DBs        │                            │
  via FastAPI services         │                            │
```

---

## 📐 Database Design Patterns

### **1. Polyglot Persistence**
Different databases optimized for different workloads:
- **Oracle:** ACID transactions, high write throughput
- **PostgreSQL:** Complex analytics, geospatial queries
- **MongoDB:** Flexible schemas, document storage

### **2. Star Schema (PostgreSQL)**
- Central fact table: `fact_transactions`
- Surrounding dimension tables: `dim_account`, `dim_time`, `dim_geo`
- Enables efficient OLAP queries and reporting

### **3. Partitioning Strategy**
- **Range Partitioning:** `fact_transactions` partitioned by day
- **Rolling Partitions:** Automatically creates 60-day partitions
- **Performance Benefits:** Faster queries, easier archival

### **4. Materialized Views**
- Pre-computed aggregations for dashboard performance
- Refresh on demand or scheduled
- Trade-off: Storage for query speed

### **5. ETL Pipeline**
- Extract from Oracle (OLTP)
- Transform and Load into PostgreSQL (OLAP)
- Checkpoint tracking for incremental loads
- Handles schema differences between databases

### **6. Document Embedding (MongoDB)**
- Notes and attachments embedded in `fraud_cases`
- Reduces need for joins
- Matches access patterns (cases loaded with all data)

### **7. Temporal Data Management**
- Timestamps on all tables
- TTL indexes in MongoDB for automatic cleanup
- Audit trail with `created_at`/`updated_at`

---

## 🔐 Security Architecture

### **Authentication & Authorization**
```
User Login
   │
   ├─> JWT Token Generation (python-jose)
   │   └─> Access Token (30 min expiration)
   │
   └─> Role-Based Access Control (RBAC)
       ├─> ADMIN (all permissions)
       ├─> MANAGER (approve, manage team)
       ├─> ANALYST (review, create cases)
       └─> VIEWER (read-only)
```

### **Security Features**
- Password hashing with bcrypt
- JWT token-based auth
- Role-permission mapping
- SQL injection prevention (parameterized queries)
- CORS configuration
- Audit logging

---

## 📈 Performance Optimizations

### **Database Indexes**

**Oracle:**
- `idx_txns_account_id` - Transaction lookups by account
- `idx_txns_time` - Time-based queries
- `idx_txns_amount` - Amount range searches
- `idx_alerts_unhandled` - Quick unhandled alert retrieval

**PostgreSQL:**
- `idx_fact_account_date` - Account transaction history
- `idx_fact_geo` (GIST) - Geospatial queries
- `idx_anomalies_rule` - Anomaly pattern analysis

**MongoDB:**
- Text index on `fraud_cases.notes.content` - Full-text search
- Compound index on `(status, createdAt)` - Filtered case lists
- TTL index on `system_logs` - Automatic expiration

### **Query Optimization**
- Partitioned tables reduce scan size
- Materialized views eliminate aggregation overhead
- Connection pooling in FastAPI
- Async database operations

### **Caching Strategy**
- Redis for session caching (optional)
- Client-side caching with React Query
- Materialized view refresh scheduling

---

## 🔄 Data Pipeline

### **Real-Time Pipeline**
```
Transaction Entry
   │
   ├─> Oracle Insert (accounts, transactions)
   │   └─> Trigger: Calculate velocity
   │
   ├─> ML Risk Scoring
   │   ├─> Isolation Forest (anomaly detection)
   │   ├─> Rule Engine (business logic)
   │   └─> Velocity Model (transaction frequency)
   │
   ├─> Alert Generation (if risk > threshold)
   │   └─> Oracle Insert (fraud_alerts)
   │
   └─> Real-time Dashboard Update
```

### **Batch ETL Pipeline**
```
Scheduled Job (e.g., every 5 minutes)
   │
   ├─> Read from Oracle (transactions)
   │   └─> Check etl_checkpoints for last processed ID
   │
   ├─> Transform
   │   ├─> Convert geography data
   │   ├─> Extract time dimensions
   │   └─> Calculate derived fields
   │
   ├─> Load into PostgreSQL
   │   ├─> Insert into fact_transactions
   │   ├─> Update dimension tables
   │   └─> Update etl_checkpoints
   │
   └─> Refresh Materialized Views
       ├─> mv_amount_buckets_hourly
       ├─> mv_velocity_by_account
       └─> mv_time_of_day_stats
```

---

## 🧪 Key Metrics & KPIs

### **System Performance**
- API Response Time: < 100ms (average)
- ML Prediction Time: < 50ms
- Dashboard Load: < 2s
- Concurrent Users: 100+

### **Fraud Detection Metrics**
- **True Positive Rate (TPR):** % of actual fraud detected
- **False Positive Rate (FPR):** % of legitimate transactions flagged
- **Alert Volume:** Alerts generated per hour/day
- **Case Resolution Time:** Average time to close cases
- **Risk Score Distribution:** Distribution of risk scores

### **Business Metrics**
- Total Transaction Volume
- Total Fraud Amount Prevented
- Average Investigation Time
- Alert Handling Rate
- User Activity by Role

---

## 🎯 Entity Cardinalities

| Relationship | Cardinality | Description |
|--------------|-------------|-------------|
| Account → Transaction | 1:N | One account has many transactions |
| Account → Fraud Alert | 1:N | One account can have many alerts |
| Transaction → Fraud Alert | 1:N | One transaction can trigger multiple alerts |
| Account (Oracle) → Fraud Case (MongoDB) | 1:N | One account can have multiple cases |
| Transaction (Oracle) → Fact Transaction (PostgreSQL) | 1:1 | ETL creates one fact record per transaction |
| Fraud Case → Notes | 1:N | One case has many notes (embedded) |
| Fraud Case → Attachments | 1:N | One case has many attachments (embedded) |

---

## 🚀 Scalability Considerations

### **Horizontal Scaling**
- **Application Tier:** FastAPI supports multiple workers
- **Database Tier:** 
  - PostgreSQL: Read replicas for analytics
  - MongoDB: Sharding by `accountId` or `caseId`
  - Oracle: RAC (Real Application Clusters)

### **Vertical Scaling**
- Increase database server resources
- Partition older data to separate tablespaces
- Archive historical data to cold storage

### **Caching**
- Redis for frequently accessed data
- CDN for static frontend assets
- Browser caching with appropriate headers

### **Load Balancing**
- Nginx/HAProxy for API load balancing
- Database connection pooling
- Async task queues for background jobs

---

## 🔮 Future Enhancements

### **Planned Features (v2.1.0)**
- Real-time WebSocket updates for live dashboard
- Advanced ML model training interface
- Customizable dashboards per user/role
- Multi-factor authentication (MFA)
- Email/SMS notification system

### **Data Model Extensions**
1. **User Activity Tracking**
   - New table: `user_activity_log`
   - Track user actions for audit trail

2. **Machine Learning Model Versions**
   - New table: `ml_model_versions`
   - Track model performance over time

3. **Customer Profiles**
   - New collection: `customer_profiles` (MongoDB)
   - Behavioral patterns, risk profiles

4. **Transaction Network Graph**
   - Graph database (Neo4j) integration
   - Visualize transaction networks for fraud rings

5. **Multi-Currency Support Enhancement**
   - Currency conversion rates table
   - Real-time FX API integration

---

## 📊 Data Volumes & Retention

| Data Type | Expected Volume | Retention Policy |
|-----------|----------------|------------------|
| Transactions | 1M+ per day | 7 years (compliance) |
| Fraud Alerts | 10K+ per day | 7 years |
| Fraud Cases | 100+ per day | Permanent |
| System Logs | 1GB+ per day | 30 days (MongoDB TTL) |
| Analytics Data | 100GB+ | 2 years (partitioned) |
| Attachments | Variable | As long as case exists |

---

## 🛠️ Development Workflow

```
Developer Workflow:
   │
   ├─> Local Development
   │   ├─> Docker Compose (Oracle, PostgreSQL, MongoDB)
   │   ├─> FastAPI Dev Server (port 8000)
   │   └─> Next.js Dev Server (port 3000)
   │
   ├─> Testing
   │   ├─> Backend: pytest
   │   ├─> Frontend: Jest/React Testing Library
   │   └─> Integration: API health checks
   │
   ├─> Code Quality
   │   ├─> Linting: ESLint (frontend), flake8 (backend)
   │   ├─> Type Checking: TypeScript, mypy
   │   └─> Code Formatting: Prettier, black
   │
   └─> Deployment
       ├─> Build: Docker images
       ├─> Deploy: Docker Compose or Kubernetes
       └─> Monitor: Prometheus + Grafana
```

---

## 📝 API Endpoints Summary

### **Authentication**
- `POST /auth/login` - User login, returns JWT token
- `POST /auth/register` - Create new user account

### **Transactions**
- `GET /transactions` - List transactions with filters
- `POST /transactions` - Create new transaction
- `GET /transactions/{id}` - Get transaction details

### **Fraud Alerts**
- `GET /alerts` - List fraud alerts with pagination
- `PATCH /alerts/{id}` - Update alert status
- `POST /alerts/bulk` - Bulk approve/reject alerts

### **Cases**
- `GET /cases` - List fraud cases
- `POST /cases` - Create new case
- `PATCH /cases/{id}` - Update case
- `POST /cases/{id}/notes` - Add note to case
- `POST /cases/{id}/attachments` - Upload attachment

### **Risk Scoring**
- `POST /ml/predict` - Get ML risk prediction for transaction
- `GET /ml/model-info` - Get ML model information

### **Analytics**
- `GET /analytics/trends` - Fraud trends over time
- `GET /analytics/top-merchants` - High-risk merchants
- `GET /analytics/geographic` - Geographic fraud distribution

### **Users (RBAC)**
- `GET /users` - List users (admin only)
- `POST /users` - Create user (admin only)
- `PATCH /users/{id}` - Update user (admin/manager)

---

## 🎨 UI/UX Features

### **Component Library**
- **AlertFilters:** Advanced filtering (severity, date, status)
- **BulkActions:** Multi-select and batch operations
- **CommandPalette:** Keyboard shortcuts (Cmd+K)
- **FraudChatbot:** AI-powered Q&A
- **FraudMap:** Interactive Leaflet map with clustering
- **NetworkGraph:** D3.js force-directed graph
- **TransactionModal:** Detailed transaction view
- **ThemeToggle:** Dark/light mode switcher
- **NotificationCenter:** Real-time alerts

### **Design System**
- **Colors:** Tailwind CSS custom theme
- **Typography:** Inter font family
- **Icons:** Lucide React icon library
- **Layout:** Responsive grid, mobile-first
- **Animations:** Framer Motion transitions

---

## 🔍 Code Quality & Testing

### **Backend Testing (pytest)**
```python
# services/api/tests/
├── api/
│   ├── test_cases.py       # Case management tests
│   ├── test_risk_scoring.py # ML model tests
│   ├── test_health.py      # Health check tests
│   └── test_export.py      # Export functionality tests
└── worker/
    └── test_etl.py         # ETL pipeline tests
```

### **Frontend Testing**
- Component tests with Jest
- E2E tests (future: Playwright/Cypress)
- Visual regression tests (future: Chromatic)

### **Code Coverage Goals**
- Backend: > 80% coverage
- Frontend: > 70% coverage
- Critical paths: 100% coverage

---

## 🌐 Internationalization (Future)

### **Planned i18n Support**
- Multi-language support (EN, ES, FR, DE, ZH)
- Currency formatting per locale
- Date/time formatting per timezone
- Right-to-left (RTL) language support

---

## 📚 Documentation Links

| Document | Purpose |
|----------|---------|
| [INSTALLATION.md](INSTALLATION.md) | Complete installation guide |
| [API.md](docs/API.md) | API reference documentation |
| [ARCH.md](docs/ARCH.md) | System architecture details |
| [RUNBOOK.md](docs/RUNBOOK.md) | Operational procedures |
| [PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md) | Deployment checklist |

---

## 🎓 Learning Resources

### **Technologies Used**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [PostgreSQL Tutorial](https://www.postgresql.org/docs/)
- [MongoDB Manual](https://www.mongodb.com/docs/)
- [Oracle Database Docs](https://docs.oracle.com/en/database/)

---

## 🏆 Project Highlights

### **What Makes This Project World-Class?**

1. **Multi-Database Expertise:** Polyglot persistence with Oracle, PostgreSQL, MongoDB
2. **Advanced ML:** Ensemble model with explainable AI features
3. **Modern Stack:** Next.js 14, FastAPI, TypeScript, Python 3.11+
4. **Enterprise Features:** RBAC, audit logging, bulk operations
5. **UX Excellence:** Dark mode, keyboard shortcuts, responsive design
6. **Scalable Architecture:** Partitioned tables, materialized views, async operations
7. **Professional Quality:** Comprehensive testing, documentation, monitoring

---

## 📞 Support & Contact

**For Technical Issues:**
- Check [RUNBOOK.md](docs/RUNBOOK.md) for troubleshooting
- Review [API.md](docs/API.md) for API questions
- Consult [INSTALLATION.md](INSTALLATION.md) for setup help

**For Business Questions:**
- Contact fraud-support@company.com
- Join Slack channel: #fraud-detection

---

## 📅 Project Timeline

- **v1.0.0** - Initial release with core features
- **v2.0.0** - Added ML enhancements, network graph, dark mode
- **v2.1.0** - (Planned) WebSocket updates, MFA, notifications
- **v3.0.0** - (Future) Blockchain monitoring, AR/VR visualization

---

## ✨ Credits

**Built with love by the FraudGuard Team**

Special thanks to:
- Domain experts for fraud detection logic
- UX designers for world-class interface
- DevOps team for infrastructure support

---

**Last Updated:** October 29, 2025
**Document Version:** 1.0
**Project Version:** 2.0.0

---


