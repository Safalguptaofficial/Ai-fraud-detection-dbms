# Architecture Documentation

## Context Diagram

```
┌─────────────────────────────────────────────────────────┐
│                   Fraud Analyst                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
            ┌────────────────┐
            │  Next.js Web   │
            │     (UI)       │
            └────────┬───────┘
                     │ HTTP/REST
                     ▼
        ┌────────────────────────┐
        │    FastAPI Backend     │
        └─────┬──────────┬───────┘
              │          │
    ┌─────────▼───┐  ┌──▼────────────┐
    │   Oracle    │  │   PostgreSQL  │
    │   (OLTP)    │  │    (OLAP)     │
    └─────────────┘  └───────────────┘
                     │
                     ▼
            ┌────────────────┐
            │   MongoDB      │
            │  (Documents)   │
            └────────────────┘

            ┌────────────────┐
            │   Worker       │
            │  (ETL/Jobs)    │
            └────────────────┘
```

## Component Diagram

### Backend Services

**FastAPI Service**
- **routes/**: REST API handlers
- **models/**: Pydantic schemas
- **deps/**: Dependency injection (DB connections)
- **middleware/**: Logging, CORS, rate limiting

**Worker Service**
- **etl/**: Elise pays to LabantDB
- **scheduler/**: APScheduler jobs
- **analytics/**: Anomaly detection logic

### Frontend Services

**Next.js App**
- **pages/**: Route components
  - `/dashboard` - Main dashboard
  - `/transactions` - Transaction table
  - `/alerts` - Fraud alerts
  - `/cases` - Case management
- **components/**: Reusable UI components
- **lib/**: API client, utilities

## Database Schema

### Oracle (OLTP)

```
accounts(id, customer_id, status, created_at)
  └─ transactions(id, account_id, amount, merchant, lat, lon, txn_time, status)
      └─ fraud_alerts(id, account_id, txn_id, rule_code, severity, reason, handled)
```

**Triggers**:
- `trg_txn_insert_after`: Fires on transaction insert, checks rules, creates alerts, freezes accounts

### PostgreSQL (OLAP)

```
fact_transactions (partitioned by day)
  ├─ dim_account
  ├─ dim_time
  └─ dim_geo

anomaly_events (id, account_id, txn_id, rule, score, detected_at, severity, extra)

Materialized Views:
├─ mv_amount_buckets_hourly
├─ mv_velocity_by_account
└─ mv_time_of_day_stats
```

### MongoDB (Documents)

```javascript
fraud_cases {
  caseId, accountId, txnIds[],
  investigator, notes[], attachments[],
  status, tags[], createdAt, updatedAt
}

sar_reports {
  reportId, accountId, suspiciousActivity,
  amount, reportDate, filedBy, status
}
```

## Sequence Diagrams

### Transaction with Fraud Detection

```
Client → API → Oracle (INSERT transaction)
                   ↓
              Trigger fires
                   ↓
              Check rules (midnight, geo, velocity)
                   ↓
              Create fraud_alerts
                   ↓
              Update account status to FROZEN
                   ↓
              Return response with alert
Client ← API ← Oracle
```

### ETL Pipeline

```
Worker (scheduled)
    ↓
Read from etl_checkpoints
    ↓
Oracle: SELECT transactions WHERE id > last_id
    ↓
Postgres: INSERT INTO fact_transactions
    ↓
Refresh materialized views
    ↓
Run analytics functions
    ↓
INSERT INTO anomaly_events
    ↓
Update checkpoint
```

## Deployment

Development uses Docker Compose with:
- All databases in separate containers
- API and worker as separate services
- Web frontend in Next.js dev mode
- Prometheus and Grafana for monitoring

Production considerations:
- Use RDS/Oracle Cloud for databases
- Deploy API and worker to ECS/GKE
- Use VPC for network isolation
- CloudWatch/Datadog for logs and metrics
- Secrets Manager for credentials

