# Fraud DBMS - AI-Powered Fraud Detection & Financial Crime System

**One-line resume blurb:**
"Built a hybrid DBMS for real-time fraud detection integrating OLTP (Oracle), OLAP (Postgres), and unstructured data (MongoDB). Implemented PL/SQL triggers that auto-freeze suspicious accounts, OLAP anomaly queries (velocity, geo-jump, z-score), and Mongo text search for investigator case notes. End-to-end dockerized with FastAPI services, ETL worker, and CI tests."

## 🎯 Project Overview

A production-ready hybrid database management system for AI-powered fraud detection and financial crime prevention. This system integrates multiple database technologies to provide real-time fraud detection, automated account freezing, and comprehensive case management.

### Key Highlights
- 🔒 **Secure**: JWT authentication, rate limiting, security headers
- ⚡ **Real-time**: Auto-updating dashboard with 5-second polling
- 📊 **Hybrid Database**: Oracle (OLTP), PostgreSQL (OLAP), MongoDB (unstructured)
- 🤖 **AI-Powered**: Automated fraud detection with PL/SQL triggers
- 📈 **Monitoring**: Grafana dashboards and Prometheus metrics
- 💾 **Performance**: Redis caching layer for optimized queries
- 🧪 **Tested**: Comprehensive end-to-end test suite

## 🚀 Quick Start (3-Minute Demo)

```bash
# 1. Clone and start services
git clone https://github.com/Safalguptaofficial/Ai-fraud-detection-dbms.git
cd Ai-fraud-detection-dbms
make up

# 2. Wait for services to be healthy, then seed data
make seed

# 3. Access the dashboard
open http://localhost:3000
```

### Login Credentials
- **Email**: `analyst@bank.com`
- **Password**: `password123`

## 📁 Project Structure

```
fraud-dbms/
├── apps/web/                    # Next.js Frontend
│   ├── app/
│   │   ├── dashboard/          # Real-time fraud dashboard
│   │   ├── login/               # JWT authentication
│   │   └── utils/               # Auth utilities
│   └── package.json
├── services/
│   ├── api/                     # FastAPI Backend
│   │   ├── routers/             # API endpoints
│   │   │   ├── auth.py          # JWT authentication
│   │   │   ├── accounts.py      # Account CRUD operations
│   │   │   ├── transactions.py  # Transaction processing
│   │   │   ├── alerts.py        # Fraud alerts
│   │   │   ├── analytics.py     # Analytics endpoints
│   │   │   └── cases.py         # Case management
│   │   ├── deps.py              # Dependencies (DB, Redis)
│   │   ├── main.py              # FastAPI app with security
│   │   └── models/              # Pydantic models
│   └── worker/                   # ETL Worker
│       └── main.py              # Data pipeline
├── db/
│   ├── oracle/                  # Oracle OLTP schema
│   │   ├── schema.sql           # Table definitions
│   │   ├── triggers.sql         # PL/SQL fraud triggers
│   │   └── seed.sql             # Sample data
│   ├── postgres/                # PostgreSQL OLAP schema
│   │   ├── schema.sql           # Analytics tables
│   │   └── seed.sql             # Sample data
│   └── mongo/                   # MongoDB collections
│       └── collections.js        # Case management schema
├── infra/docker/                # Docker Compose
│   ├── docker-compose.yml       # Service orchestration
│   ├── prometheus.yml           # Metrics configuration
│   └── grafana/                 # Monitoring dashboards
│       ├── dashboard.json       # Fraud detection dashboard
│       └── datasource.yml       # Prometheus connection
├── docs/                        # Documentation
│   ├── README.md                # Detailed guide
│   ├── ARCH.md                  # Architecture docs
│   ├── API.md                   # API documentation
│   ├── RUNBOOK.md               # Operations guide
│   ├── IMPLEMENTATION_SUMMARY.md # Features summary
│   ├── PRODUCTION_CHECKLIST.md  # Deployment guide
│   └── SUBMISSION_GUIDE.md      # Screenshot guide
└── tools/
    └── test_fraud_detection.py  # End-to-end tests
```

## 🏗️ Architecture

### Database Layer
- **Oracle XE (OLTP)**: Real-time transaction processing
  - Automatic fraud detection via PL/SQL triggers
  - Account status management (ACTIVE, FROZEN, CLOSED)
  - Transaction logging and audit trail
  
- **PostgreSQL (OLAP)**: Analytics and reporting
  - Materialized views for performance
  - PostGIS for geographic analysis
  - Anomaly detection queries
  
- **MongoDB**: Unstructured case management
  - Investigator notes and documentation
  - Full-text search capabilities
  - Case status workflow
  
- **Redis**: Performance caching
  - Transaction result caching (5-minute TTL)
  - Query result optimization
  - Cache statistics and management

### Application Layer
- **FastAPI Backend**: REST API with:
  - JWT authentication
  - Rate limiting (100 req/min)
  - Security headers
  - Prometheus metrics
  - Redis caching
  
- **Next.js Frontend**: Analyst portal with:
  - Real-time updates (5-second polling)
  - Interactive charts and visualizations
  - Protected routes
  - User session management
  
- **ETL Worker**: Background processing
  - Scheduled data pipeline
  - Anomaly detection scoring
  - Database synchronization

### Security Features
- ✅ JWT-based authentication
- ✅ Rate limiting per IP
- ✅ CORS protection
- ✅ Security headers (XSS, X-Frame, Content-Type)
- ✅ Input validation
- ✅ Structured error handling
- ✅ Audit logging

## 🔥 Features

### Auto-Freeze Triggers
- **MIDNIGHT_5K**: Transactions >$5K between 00:00-05:00
- **GEO_JUMP**: Travel >800km within 2 hours
- **VELOCITY_SPIKE**: >5 transactions in 10 minutes

### Real-Time Fraud Detection
- Automatic alert generation
- Account status updates
- Severity classification (HIGH, MEDIUM, LOW)
- Rule-based detection

### Analytics
- Time-of-day z-score outliers
- Velocity anomalies by peer group
- Geographic jump detection via PostGIS
- Materialized views for performance

### Case Management
- Text search on investigator notes
- Status workflow (OPEN → INVESTIGATING → RESOLVED)
- Attachment management
- Audit trail

### Dashboard
- Live fraud alerts with auto-refresh
- Severity distribution charts
- Account status overview
- System health monitoring
- Interactive data visualization

## 🔧 Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **OLTP Database** | Oracle XE | 21slim |
| **OLAP Database** | PostgreSQL | 16 |
| **Document Store** | MongoDB | 7 |
| **Cache** | Redis | 7-alpine |
| **Backend** | FastAPI | 0.104.1 |
| **Frontend** | Next.js | 14 |
| **Language** | Python | 3.11 |
| **Container** | Docker Compose | Latest |
| **Monitoring** | Prometheus | Latest |
| **Visualization** | Grafana | Latest |

## 📊 API Endpoints

### Authentication
- `POST /v1/auth/login` - Login with JWT
- `GET /v1/auth/me` - Get current user
- `POST /v1/auth/verify` - Verify token

### Accounts
- `GET /v1/accounts` - List all accounts
- `POST /v1/accounts` - Create account
- `GET /v1/accounts/{id}` - Get account by ID
- `PATCH /v1/accounts/{id}` - Update account status

### Transactions
- `POST /v1/transactions` - Create transaction (triggers fraud checks)
- `GET /v1/transactions` - List transactions (cached)
- `GET /v1/transactions/cache/stats` - Redis cache statistics

### Alerts
- `GET /v1/alerts?status=open` - Get fraud alerts
- `GET /v1/alerts/{id}` - Get alert details
- `PATCH /v1/alerts/{id}` - Update alert status

### Analytics
- `GET /v1/analytics/anomalies` - Get anomaly events
- `GET /v1/analytics/geo-jumps` - Get geographic jumps
- `GET /v1/analytics/velocity-anomalies` - Get velocity spikes

### Cases
- `GET /v1/cases` - List fraud cases
- `POST /v1/cases` - Create case
- `GET /v1/cases/{id}` - Get case details
- `POST /v1/cases/{id}/notes` - Add note to case
- `GET /v1/cases/search?q=...` - Full-text search

## 🎯 CRUD Operations

### Create (C)
```bash
# Create Account
curl -X POST http://localhost:8000/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{"account_id":"ACC001","customer_id":"CUST001","account_type":"CHECKING"}'

# Create Transaction (triggers fraud detection)
curl -X POST http://localhost:8000/v1/transactions \
  -H "x-api-key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "amount": 8000,
    "merchant": "ATM-CORP",
    "txn_time": "2025-01-15T00:30:00Z"
  }'
```

### Read (R)
```bash
# List Accounts
curl http://localhost:8000/v1/accounts

# Get Fraud Alerts
curl http://localhost:8000/v1/alerts?status=open

# Get Transaction Analytics
curl http://localhost:8000/v1/analytics/anomalies
```

### Update (U)
```bash
# Update Account Status
curl -X PATCH http://localhost:8000/v1/accounts/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "FROZEN"}'

# Update Alert Status
curl -X PATCH http://localhost:8000/v1/alerts/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "INVESTIGATING"}'
```

### Delete (D)
```bash
# Clear Cache
curl -X POST http://localhost:8000/v1/transactions/cache/clear

# Delete transactions (via database)
# Implemented through database-level deletions
```

## 📸 Screenshot Guide

See [docs/SUBMISSION_GUIDE.md](docs/SUBMISSION_GUIDE.md) for:
- Dashboard screenshots
- Database state changes
- CRUD operation comparisons
- System architecture diagrams

## 🧪 Testing

```bash
# Run end-to-end tests
python3 tools/test_fraud_detection.py

# Test API endpoints
curl http://localhost:8000/healthz

# Test authentication
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"analyst@bank.com","password":"password123"}'
```

## 📈 Monitoring

### Access Dashboards
- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **API Metrics**: http://localhost:8000/metrics

### Metrics Tracked
- HTTP request rate and duration
- Error rates by endpoint
- Database connection status
- Cache hit/miss rates
- Fraud alert generation rate

## 🚀 Deployment

See [docs/PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md) for production deployment steps.

## 📚 Documentation

- [README](docs/README.md) - Quick start and features
- [ARCH.md](docs/ARCH.md) - System architecture
- [API.md](docs/API.md) - Complete API documentation
- [RUNBOOK.md](docs/RUNBOOK.md) - Operations guide
- [IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md) - All features
- [PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md) - Deployment guide
- [SUBMISSION_GUIDE.md](docs/SUBMISSION_GUIDE.md) - Screenshot guide

## 🤝 Contributing

This is a demonstration project showcasing:
- Multi-database architecture
- Real-time fraud detection
- Production-ready security
- Comprehensive monitoring
- Full-stack development

## 📝 License

MIT

---

**Built with**: Oracle, PostgreSQL, MongoDB, Redis, FastAPI, Next.js, Docker, Prometheus, Grafana