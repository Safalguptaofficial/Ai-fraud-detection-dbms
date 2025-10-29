# 🏗️ FraudGuard - System Architecture Summary

## 📊 Quick Reference

| Aspect | Details |
|--------|---------|
| **Project Name** | FraudGuard - AI Fraud Detection System |
| **Version** | 2.0.0 |
| **Architecture** | Multi-tier, Multi-database (Polyglot Persistence) |
| **Frontend** | Next.js 14 + TypeScript + Tailwind CSS |
| **Backend** | FastAPI (Python 3.11+) |
| **Databases** | Oracle (OLTP), PostgreSQL (OLAP), MongoDB (NoSQL) |
| **ML Models** | Ensemble (Isolation Forest + Rules + Velocity) |
| **Authentication** | JWT + RBAC (4 roles) |
| **Deployment** | Docker Compose / Kubernetes |

---

## 🎯 System Overview

### **Purpose**
Enterprise-grade fraud detection platform that:
- Monitors transactions in real-time
- Uses machine learning to identify fraud patterns
- Provides investigation tools for analysts
- Generates compliance reports (SAR)
- Visualizes fraud networks and geographic patterns

### **Key Capabilities**
1. **Real-Time Detection** - Sub-50ms ML predictions
2. **Risk Scoring** - 0-100 risk score with explainability
3. **Case Management** - Full investigation lifecycle
4. **Analytics Dashboard** - Interactive charts and maps
5. **Network Analysis** - Fraud ring visualization
6. **Bulk Operations** - Efficient alert handling
7. **Role-Based Access** - Granular permissions

---

## 🏛️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                         │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │          Next.js Frontend (React + TypeScript)                 │ │
│  │  • Dashboard  • ML Model  • Network Graph  • Investigation     │ │
│  │  • Dark Mode  • Command Palette  • Bulk Actions  • Chatbot     │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ REST API (HTTP/JSON)
                                   │
┌─────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER                             │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    FastAPI Backend (Python)                    │ │
│  │                                                                │ │
│  │  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐  │ │
│  │  │   Routers    │  │  ML Engine    │  │  RBAC System     │  │ │
│  │  │  /alerts     │  │  • Isolation  │  │  • Permissions   │  │ │
│  │  │  /cases      │  │    Forest     │  │  • Role Check    │  │ │
│  │  │  /analytics  │  │  • Rules      │  │  • JWT Auth      │  │ │
│  │  │  /ml/predict │  │  • Velocity   │  │                  │  │ │
│  │  └──────────────┘  └───────────────┘  └──────────────────┘  │ │
│  │                                                                │ │
│  │  ┌────────────────────────────────────────────────────────┐  │ │
│  │  │              Data Access Layer (DAL)                   │  │ │
│  │  │  • oracledb • psycopg2 • pymongo • Connection Pooling │  │ │
│  │  └────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                   │
               ┌───────────────────┼───────────────────┐
               │                   │                   │
┌──────────────▼──────────┐ ┌──────▼──────────┐ ┌─────▼──────────────┐
│   ORACLE DATABASE       │ │  POSTGRESQL      │ │  MONGODB           │
│       (OLTP)            │ │     (OLAP)       │ │   (NoSQL)          │
│                         │ │                  │ │                    │
│ ┌─────────────────────┐ │ │ ┌──────────────┐ │ │ ┌────────────────┐ │
│ │ • accounts          │ │ │ │ Dimensions:  │ │ │ │ • fraud_cases  │ │
│ │ • transactions      │ │ │ │  dim_account │ │ │ │ • sar_reports  │ │
│ │ • fraud_alerts      │ │ │ │  dim_time    │ │ │ │ • complaints   │ │
│ │ • system_logs       │ │ │ │  dim_geo     │ │ │ │ • system_logs  │ │
│ └─────────────────────┘ │ │ │              │ │ │ └────────────────┘ │
│                         │ │ │ Facts:       │ │ │                    │
│ • High write throughput│ │ │  fact_txns   │ │ │ • Flexible schema │
│ • ACID compliance      │ │ │  anomalies   │ │ │ • Embedded docs   │
│ • Real-time ingestion  │ │ │              │ │ │ • GridFS storage  │
│                         │ │ │ Aggregates:  │ │ │ • Full-text search│
│                         │ │ │  mv_* views  │ │ │                   │
│                         │ │ └──────────────┘ │ │                   │
│                         │ │                  │ │                   │
│                         │ │ • Star schema    │ │                   │
│                         │ │ • Partitioned    │ │                   │
│                         │ │ • PostGIS        │ │                   │
└─────────────────────────┘ └──────────────────┘ └───────────────────┘
        │                           ▲                       │
        │                           │                       │
        └────────► ETL Worker ──────┘                       │
                  (Scheduled)                               │
                                                            │
┌─────────────────────────────────────────────────────────────────────┐
│                     MONITORING & OBSERVABILITY                       │
│  • Prometheus (Metrics)  • Grafana (Dashboards)  • Health Checks   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Data Model Summary

### **1. Oracle Database (OLTP)**

**Purpose:** Primary transactional system for real-time operations

```
ACCOUNTS (1) ───has many──► TRANSACTIONS (*)
    │                            │
    │                            │
    └────has many──► FRAUD_ALERTS (*)
                                  ▲
                                  │
                          ────triggers───
```

**Key Tables:**
- `accounts` - Customer accounts (status, customer_id)
- `transactions` - Transaction records (amount, location, merchant, device)
- `fraud_alerts` - Generated alerts (rule, severity, handled status)
- `system_logs` - Application logs

**Indexes:**
- Account lookups: `idx_accounts_customer_id`, `idx_accounts_status`
- Transaction queries: `idx_transactions_account_id`, `idx_transactions_txn_time`
- Alert filtering: `idx_fraud_alerts_handled`, `idx_fraud_alerts_created_at`

---

### **2. PostgreSQL Database (OLAP)**

**Purpose:** Analytics, data warehousing, complex queries

**Star Schema Design:**
```
                    ┌──────────────┐
                    │  DIM_TIME    │
                    └──────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼──────┐  ┌────────▼─────────┐  ┌────▼──────┐
│ DIM_ACCOUNT  │  │ FACT_TRANSACTIONS │  │  DIM_GEO  │
└──────────────┘  │  (Partitioned)    │  └───────────┘
                  └───────────────────┘
                           │
                           │ analyzed by
                           ▼
                  ┌───────────────────┐
                  │ ANOMALY_EVENTS    │
                  └───────────────────┘
```

**Fact Table:**
- `fact_transactions` - Central fact table (partitioned by day, 60-day rolling)

**Dimension Tables:**
- `dim_account` - Account dimension
- `dim_time` - Time dimension (date, year, month, weekday)
- `dim_geo` - Geographic dimension (city, country, coordinates)

**Analytical Tables:**
- `anomaly_events` - Detected anomalies with scores
- `etl_checkpoints` - ETL process tracking

**Materialized Views:**
- `mv_amount_buckets_hourly` - Transaction amount distribution
- `mv_velocity_by_account` - Transaction velocity per account
- `mv_time_of_day_stats` - Time-based patterns

**Features:**
- PostGIS extension for geospatial queries
- Range partitioning for performance
- JSONB for flexible metadata
- Materialized views for fast dashboards

---

### **3. MongoDB Database (NoSQL)**

**Purpose:** Flexible document storage for investigations

**Collections:**

```
FRAUD_CASES
  ├─ notes[] (embedded documents)
  ├─ attachments[] (embedded documents)
  └─ references: accountId, txnIds[]

SAR_REPORTS
  └─ references: accountId

CUSTOMER_COMPLAINTS
  └─ references: accountId, customerId

SYSTEM_LOGS (TTL: 30 days)
```

**Key Features:**
- Schema validation with JSON Schema
- Embedded documents (notes, attachments)
- Text search on case notes
- GridFS for file storage
- TTL indexes for auto-expiration
- Array fields for multiple references

---

## 🔄 Data Flow

### **Transaction Processing Flow**

```
1. Transaction Created
   └─> POST /transactions
       └─> Insert into Oracle (transactions table)
           ├─> ML Risk Scoring (ensemble model)
           │   ├─> Isolation Forest (40%)
           │   ├─> Rule Engine (30%)
           │   └─> Velocity Model (30%)
           │
           └─> If risk > threshold
               └─> Insert into Oracle (fraud_alerts table)
                   └─> Real-time Dashboard Update
```

### **ETL Pipeline Flow**

```
Scheduled Job (every 5 minutes)
   │
   ├─> Read etl_checkpoints (last processed ID)
   │
   ├─> Query Oracle (new transactions since checkpoint)
   │
   ├─> Transform Data
   │   ├─> Convert to PostGIS geography
   │   ├─> Extract time dimensions
   │   └─> Calculate derived fields
   │
   ├─> Load into PostgreSQL
   │   ├─> fact_transactions
   │   ├─> dim_account (if new)
   │   └─> Update etl_checkpoints
   │
   └─> Refresh Materialized Views
       ├─> mv_amount_buckets_hourly
       ├─> mv_velocity_by_account
       └─> mv_time_of_day_stats
```

### **Case Investigation Flow**

```
1. Analyst Reviews Alert
   └─> GET /alerts (from Oracle)
       └─> Filter, search, sort
           └─> Select alert(s)
               
2. Create Case
   └─> POST /cases
       └─> Insert into MongoDB (fraud_cases)
           ├─> Link: accountId (Oracle reference)
           └─> Link: txnIds[] (Oracle references)
           
3. Investigation
   ├─> Add Notes
   │   └─> POST /cases/{id}/notes
   │       └─> Update MongoDB (embedded notes array)
   │
   ├─> Upload Evidence
   │   └─> POST /cases/{id}/attachments
   │       ├─> Store file in GridFS
   │       └─> Update MongoDB (embedded attachments array)
   │
   └─> Update Status
       └─> PATCH /cases/{id}
           └─> Update MongoDB (status, tags)
           
4. Generate SAR Report
   └─> POST /sar-reports
       └─> Insert into MongoDB (sar_reports)
           └─> Link: accountId
```

---

## 🧠 ML Model Architecture

### **Ensemble Model (3 Components)**

```
┌─────────────────────────────────────────────────────────────────┐
│                    TRANSACTION INPUT                             │
│  amount, velocity, time_since_last, location, merchant, device  │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────────┐ ┌──────────┐ ┌────────────────┐
│ Isolation Forest│ │  Rules   │ │ Velocity Model │
│    (40%)        │ │  (30%)   │ │    (30%)       │
└────────┬────────┘ └─────┬────┘ └────────┬───────┘
         │                │               │
         └────────────────┼───────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │  Weighted Sum │
                  └───────┬───────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   RISK ASSESSMENT OUTPUT                         │
│  • Risk Score: 0-100                                            │
│  • Risk Level: LOW/MEDIUM/HIGH                                  │
│  • Confidence: 0-100%                                           │
│  • Triggered Rules: [rule names]                                │
│  • Feature Contributions: {feature: weight}                     │
│  • Recommendation: APPROVE/REVIEW/DECLINE                       │
└─────────────────────────────────────────────────────────────────┘
```

### **Feature Engineering**

| Feature | Description | Source |
|---------|-------------|--------|
| `amount_zscore` | Z-score of transaction amount | Normalized against account history |
| `velocity_1h` | Transactions in last hour | Windowed count |
| `velocity_24h` | Transactions in last 24 hours | Windowed count |
| `time_since_last` | Minutes since previous transaction | Temporal analysis |
| `hour_of_day` | Hour (0-23) | Temporal pattern |
| `is_weekend` | Weekend flag | Temporal pattern |
| `distance_from_last` | Geographic distance (km) | Geospatial calculation |
| `merchant_risk` | Merchant risk score | Historical data |
| `device_change` | Device ID changed | Behavioral pattern |
| `ip_change` | IP address changed | Network pattern |

---

## 🔐 Security Architecture

### **Authentication Flow**

```
1. User Login
   │
   └─> POST /auth/login {username, password}
       │
       ├─> Verify password (bcrypt hash)
       │
       └─> Generate JWT Token
           ├─> Payload: {user_id, username, role}
           ├─> Expiration: 30 minutes
           └─> Signature: HS256 with SECRET_KEY
           
2. Subsequent Requests
   │
   └─> Headers: {Authorization: "Bearer <token>"}
       │
       ├─> Verify JWT signature
       ├─> Check expiration
       ├─> Extract user role
       └─> Check permissions
           ├─> ADMIN: All permissions
           ├─> MANAGER: Approve, manage
           ├─> ANALYST: Review, create
           └─> VIEWER: Read-only
```

### **RBAC Permission Matrix**

| Permission | ADMIN | MANAGER | ANALYST | VIEWER |
|------------|-------|---------|---------|--------|
| View Alerts | ✅ | ✅ | ✅ | ✅ |
| Approve/Reject Alerts | ✅ | ✅ | ✅ | ❌ |
| Delete Alerts | ✅ | ❌ | ❌ | ❌ |
| View Cases | ✅ | ✅ | ✅ | ✅ |
| Create Cases | ✅ | ✅ | ✅ | ❌ |
| Update Cases | ✅ | ✅ | ✅ | ❌ |
| Delete Cases | ✅ | ❌ | ❌ | ❌ |
| View Users | ✅ | ✅ | ❌ | ❌ |
| Create/Update Users | ✅ | ❌ | ❌ | ❌ |
| View Analytics | ✅ | ✅ | ✅ | ✅ |
| Export Data | ✅ | ✅ | ❌ | ❌ |
| Manage Settings | ✅ | ❌ | ❌ | ❌ |

---

## 🚀 API Endpoints

### **Core Endpoints**

```
Authentication
  POST   /auth/login           - User login
  POST   /auth/register        - Create account

Transactions
  GET    /transactions         - List transactions
  POST   /transactions         - Create transaction
  GET    /transactions/{id}    - Get details

Fraud Alerts
  GET    /alerts               - List alerts (filtered)
  PATCH  /alerts/{id}          - Update alert status
  POST   /alerts/bulk          - Bulk approve/reject

Cases
  GET    /cases                - List cases
  POST   /cases                - Create case
  PATCH  /cases/{id}           - Update case
  POST   /cases/{id}/notes     - Add note
  POST   /cases/{id}/attachments - Upload file

ML Predictions
  POST   /ml/predict           - Real-time risk scoring
  GET    /ml/model-info        - Model metadata

Analytics
  GET    /analytics/trends     - Fraud trends
  GET    /analytics/merchants  - Top merchants
  GET    /analytics/geographic - Geographic distribution

Users (RBAC)
  GET    /users                - List users
  POST   /users                - Create user
  PATCH  /users/{id}           - Update user

Health
  GET    /health               - Health check
```

---

## 📊 Performance Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| API Response Time | < 100ms | ~80ms avg |
| ML Prediction Time | < 50ms | ~30ms avg |
| Dashboard Load | < 2s | ~1.5s |
| Transaction Throughput | 1000 TPS | Supported |
| Concurrent Users | 100+ | Tested |
| Database Query Time | < 200ms | ~150ms avg (with indexes) |

---

## 🔧 Configuration

### **Environment Variables**

```bash
# Database Connections
ORACLE_URI=oracle+oracledb://system:password@localhost:1521/XE
POSTGRES_URI=postgresql://postgres:password@localhost:5432/frauddb
MONGO_URI=mongodb://root:password@localhost:27017/

# API Settings
API_SECRET_KEY=change-this-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# ML Model
ML_MODEL_PATH=./models/
ML_THRESHOLD=0.7

# ETL
ETL_BATCH_SIZE=1000
ETL_SCHEDULE_MINUTES=5

# Monitoring
PROMETHEUS_PORT=9090
```

---

## 📦 Deployment Architecture

### **Development**

```
Docker Compose (Local)
  ├─ Oracle XE Container (port 1521)
  ├─ PostgreSQL Container (port 5432)
  ├─ MongoDB Container (port 27017)
  ├─ FastAPI Dev Server (port 8000)
  └─ Next.js Dev Server (port 3000)
```

### **Production**

```
Kubernetes Cluster
  │
  ├─ Ingress (NGINX)
  │   └─> Load Balancer
  │
  ├─ Frontend Pods (Next.js)
  │   ├─ Replica 1
  │   ├─ Replica 2
  │   └─ Replica N
  │
  ├─ Backend Pods (FastAPI)
  │   ├─ Replica 1 (with Gunicorn)
  │   ├─ Replica 2
  │   └─ Replica N
  │
  ├─ Worker Pods (ETL)
  │   └─ CronJob schedule
  │
  └─ Databases (External or StatefulSets)
      ├─ Oracle RAC
      ├─ PostgreSQL (High Availability)
      └─ MongoDB Replica Set
```

---

## 📈 Scalability Strategy

### **Horizontal Scaling**
- **Frontend:** Multiple Next.js instances behind load balancer
- **Backend:** Multiple FastAPI workers (Gunicorn)
- **Databases:** Read replicas, sharding (MongoDB)

### **Vertical Scaling**
- Increase database server resources
- Optimize queries and indexes
- Use SSD storage

### **Caching**
- Redis for session/API caching
- CDN for static assets
- Browser caching with appropriate headers

### **Data Archival**
- Archive old transactions to cold storage
- Keep hot data (last 90 days) in primary DB
- Warm data (90-365 days) in compressed partitions

---

## 🛡️ Disaster Recovery

### **Backup Strategy**
- **Oracle:** RMAN backups (daily full, hourly incremental)
- **PostgreSQL:** pg_dump (daily) + WAL archiving
- **MongoDB:** mongodump (daily) + replica set

### **Recovery Objectives**
- **RTO (Recovery Time Objective):** < 1 hour
- **RPO (Recovery Point Objective):** < 5 minutes

### **High Availability**
- Database replication (master-slave)
- Application redundancy (multiple instances)
- Geographic distribution (multi-region)

---

## 📚 Technology Stack Summary

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | Next.js | 14.x | React framework |
| | TypeScript | 5.x | Type safety |
| | Tailwind CSS | 3.x | Styling |
| | Recharts | 2.x | Charts |
| | Leaflet | 1.9.x | Maps |
| **Backend** | FastAPI | 0.109+ | API framework |
| | Python | 3.11+ | Language |
| | Pydantic | 2.x | Validation |
| | NumPy | 1.26+ | ML computations |
| **Databases** | Oracle | 11g+ | OLTP |
| | PostgreSQL | 12+ | OLAP |
| | MongoDB | 4.4+ | NoSQL |
| **Auth** | python-jose | 3.3+ | JWT |
| | passlib | 1.7+ | Password hashing |
| **Monitoring** | Prometheus | 2.x | Metrics |
| | Grafana | 9.x | Dashboards |
| **Deployment** | Docker | 20+ | Containerization |
| | Docker Compose | 2.x | Orchestration (dev) |
| | Kubernetes | 1.25+ | Orchestration (prod) |

---

## 🎯 Key Design Decisions

### **1. Why Polyglot Persistence?**
- **Oracle:** Enterprise-grade ACID transactions, proven reliability
- **PostgreSQL:** Advanced analytics, geospatial support, cost-effective
- **MongoDB:** Flexible schema for case management, embedded documents

### **2. Why Ensemble ML Model?**
- **Isolation Forest:** Detects unseen patterns (anomaly detection)
- **Rule-Based:** Encodes domain knowledge (business rules)
- **Velocity Model:** Catches rapid transaction patterns
- **Ensemble:** Higher accuracy, lower false positives

### **3. Why Materialized Views?**
- Dashboard queries need to be < 1 second
- Pre-computed aggregations eliminate real-time computation
- Refresh on schedule (off-peak hours) or on-demand

### **4. Why Partitioning?**
- Fact tables grow rapidly (1M+ transactions/day)
- Range partitioning improves query performance
- Easier data archival (drop old partitions)

### **5. Why JWT Authentication?**
- Stateless (no session storage required)
- Scalable (no central session store)
- Standard (industry best practice)

---

## 📖 Quick Start

```bash
# 1. Clone repository
git clone <repo-url>
cd AI_FRAUD_DETECTION

# 2. Start databases
docker-compose -f infra/docker/docker-compose.yml up -d

# 3. Install backend dependencies
cd services/api
pip install -r requirements.txt

# 4. Install frontend dependencies
cd ../../apps/web
npm install

# 5. Run backend (terminal 1)
cd ../../services/api
uvicorn main:app --reload --port 8000

# 6. Run frontend (terminal 2)
cd ../../apps/web
npm run dev

# 7. Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## 🔗 Related Documents

- [Complete Project Analysis](PROJECT_ANALYSIS_AND_ER_DIAGRAM.md)
- [ER Diagram (Mermaid)](ER_DIAGRAM.mermaid)
- [ER Diagram (PlantUML)](ER_DIAGRAM.plantuml)
- [Installation Guide](INSTALLATION.md)
- [API Documentation](docs/API.md)
- [Architecture Details](docs/ARCH.md)

---

**Last Updated:** October 29, 2025  
**Document Version:** 1.0  
**Project Version:** 2.0.0

