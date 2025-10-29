# Fraud DBMS - AI-Powered Fraud Detection & Financial Crime System

**One-line resume blurb:**
"Built a hybrid DBMS for real-time fraud detection integrating OLTP (Oracle), OLAP (Postgres), and unstructured data (MongoDB). Implemented PL/SQL triggers that auto-freeze suspicious accounts, OLAP anomaly queries (velocity, geo-jump, z-score), and Mongo text search for investigator case notes. End-to-end dockerized with FastAPI services, ETL worker, and CI tests."

## Quick Start (3-Minute Demo)

```bash
# 1. Clone and start services
make up

# Wait for services to be healthy, then seed data
make seed

# 2. Access the dashboard
open http://localhost:3000

# Login with any email (demo mode)

# 3. Simulate a fraud transaction
curl -X POST http://localhost:8000/v1/transactions \
  -H "x-api-key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "amount": 7000,
    "currency": "USD",
    "merchant": "ATM-CORP",
    "mcc": "6011",
    "channel": "ATM",
    "city": "NYC",
    "country": "US",
    "txn_time": "2025-01-15T00:15:00Z"
  }'

# 4. Check alerts (triggers fire automatically)
curl http://localhost:8000/v1/alerts?status=open

# 5. Query analytics
curl "http://localhost:8000/v1/analytics/anomalies?date_from=2025-01-01"

# 6. Search cases in MongoDB
curl http://localhost:8000/v1/cases/search?q=ATM
```

## Architecture

- **OLTP (Oracle)**: Real-time transaction processing with PL/SQL triggers
- **OLAP (PostgreSQL)**: Analytics with materialized views and PostGIS
- **Document Store (MongoDB)**: Unstructured case data with GridFS for attachments
- **FastAPI**: REST API backend
- **Next.js**: Web portal for analysts
- **ETL Worker**: Scheduled data pipeline and anomaly detection

## Features

### Auto-Freeze Triggers
- MIDNIGHT_5K: Transactions >$5K between 00:00-05:00
- GEO_JUMP: Travel >800km within 2 hours
- VELOCITY_SPIKE: >5 transactions in 10 minutes

### Analytics
- Time-of-day z-score outliers
- Velocity anomalies by peer group
- Geographic jump detection via PostGIS
- Materialized views for performance

### Case Management
- Text search on investigator notes
- GridFS for document attachments
- Status workflow (OPEN → INVESTIGATING → RESOLVED)

## Make Targets

```bash
make up              # Start all services
make down            # Stop all services
make seed            # Seed databases with sample data
make logs            # View logs
make test            # Run tests verified
make psql            # Connect to PostgreSQL
make sqlplus         # Connect to Oracle
make mongo           # Connect to MongoDB
make refresh-olap    # Refresh materialized views
```

## API Endpoints

### Health
- `GET /healthz` - API health check
- `GET /metrics` - Prometheus metrics

### Accounts
- `GET /v1/accounts` - List all accounts
- `POST /v1/accounts` - Create account
- `GET /v1/accounts/{id}` - Get account by ID
- `PATCH /v1/accounts/{id}` - Update account status

### Transactions
- `POST /v1/transactions` - Create transaction (triggers fraud checks)
- `GET /v1/transactions` - List transactions

### Alerts
- `GET /v1/alerts?status=open` - Get fraud alerts
- `PATCH /v1/alerts/{id}` - Mark alert as handled

### Analytics
- `GET /v1/analytics/anomalies` - Get anomaly events
- `GET /v1/analytics/geo-jumps` - Get geographic jumps
- `GET /v1/analytics/velocity-anomalies` - Get velocity spikes

### Cases
- `GET /v1/cases` - List fraud cases
- `POST /v1/cases` - Create case
- `GET /v1/cases/{id}` - Get case details
- `POST /v1/cases/{id}/notes` - Add note to case
- `POST /v1/cases/{id}/attachments` - Upload attachment
- `GET /v1/cases/search?q=...` - Full-text search

## Screenshots

The dashboard shows:
- Active alerts count
- Total accounts
- Frozen accounts
- Recent fraud alerts table

## Technologies

- **Databases**: Oracle XE, PostgreSQL 16, MongoDB 7
- **Backend**: FastAPI, Python 3.11, Pydantic v2
- **Frontend**: Next.js 14, TypeScript, TailwindCSS, TanStack Query
- **Worker**: APScheduler for ETL and analytics
- **Observability**: Prometheus, Grafana
- **Infrastructure**: Docker Compose

## Development

```bash
# Install dependencies
cd services/api && pip install -r requirements.txt
cd apps/web && npm install

# Run locally (requires databases running)
cd services/api && uvicorn main:app --reload
cd apps/web && npm run dev
```

## Security

- JWT authentication for web portal
- API keys for service-to-service auth
- Rate limiting per IP and per key
- Input validation on all endpoints
- Audit logging for sensitive actions

## License

MIT

