# Runbook

## Starting the System

```bash
# 1. Ensure Docker is running
docker --version

# 2. Start all services
make up

# 3. Wait for health checks (about 30-60 seconds for Oracle)
docker-compose ps

# 4. Seed databases
make seed

# 5. Verify services
curl http://localhost:8000/healthz
curl http://localhost:3000
```

## Stopping the System

```bash
# Graceful shutdown
make down

# Force remove volumes (clears all data)
docker-compose down -v
```

## Database Access

### PostgreSQL
```bash
make psql

# Or directly:
docker exec -it fraud-dbms_postgres_1 psql -U postgres -d frauddb
```

### Oracle
```bash
make sqlplus

# Or directly:
docker exec -it fraud-dbms_oracle_1 sqlplus admin/password@XE
```

### MongoDB
```bash
make mongo

# Or directly:
docker exec -it fraud-dbms_mongo_1 mongosh frauddb
```

## Common Tasks

### View Logs
```bash
# All services
make logs

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
```

### Refresh OLAP Analytics
```bash
make refresh-olap

# Or manually in Postgres:
psql -c "SELECT refresh_all_materialized_views();"
```

### Run ETL Manually
```bash
docker exec fraud-dbms_worker_1 python -c "from main import etl_oracle_to_postgres; etl_oracle_to_postgres()"
```

### Simulate Fraud
```bash
# Trigger midnight high-amount alert
curl -X POST http://localhost:8000/v1/transactions \
  -H "x-api-key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "amount": 7500,
    "currency": "USD",
    "txn_time": "'$(date -u +"%Y-%m-%dT00:30:00Z")'"
  }'
```

## Troubleshooting

### Oracle Container Not Starting
```bash
# Check logs
docker-compose logs oracle

# Oracle XE can take 2-3 minutes to initialize
# Wait and retry healthcheck
```

### API Connection Errors
```bash
# Verify DB connectivity
curl http://localhost:8000/health/db

# Restart API
docker-compose restart api
```

### Worker Not Processing ETL
```bash
# Check worker logs
docker-compose logs worker

# Verify scheduler is running
docker exec fraud-dbms_worker_1 ps aux | grep python
```

### Mongo ReplicaSet Error
```bash
# Initialize replicaset
docker exec -it fraud-dbms_mongo_1 mongosh --eval "rs.initiate()"
```

## Backups

### Oracle Data Export
```bash
docker exec fraud-dbms_oracle_1 expdp admin/password@XE \
  schemas=FRAUD_SCHEMA directory=DATA_PUMP_DIR \
  dumpfile=fraud_backup.dmp
```

### PostgreSQL Backup
```bash
docker exec fraud-dbms_postgres_1 pg_dump -U postgres frauddb > backup.sql
```

### MongoDB Backup
```bash
docker exec fraud-dbms_mongo_1 mongodump --out /backup
```

## Monitoring

- **Grafana**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **API Metrics**: http://localhost:8000/metrics

## Secrets Management

### Change JWT Secret
```bash
# Update in docker-compose.yml
# Restart API service
docker-compose restart api
```

### Rotate API Keys
1. Update `API_KEY_WORKER` in environment
2. Restart API and worker services
3. Update any external clients

## Scaling

```bash
# Scale API instances
docker-compose up -d --scale api=3

# Scale worker instances
docker-compose up -d --scale worker=2
```

## Maintenance Windows

1. **Backup databases**
2. **Stop services**: `make down`
3. **Apply schema migrations**
4. **Restart services**: `make up`
5. **Verify health checks**

