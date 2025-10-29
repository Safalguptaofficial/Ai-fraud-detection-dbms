.PHONY: help up down logs psql sqlplus mongo seed test fmt lint mypy build dev refresh-olap demo clean

help:
	@echo "Fraud DBMS - Make Commands"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make logs       - View logs"
	@echo "  make psql       - Connect to PostgreSQL"
	@echo "  make sqlplus    - Connect to Oracle"
	@echo "  make mongo      - Connect to MongoDB"
	@echo "  make seed       - Seed databases with sample data"
	@echo "  make test       - Run all tests"
	@echo "  make fmt        - Format code"
	@echo "  make lint       - Lint code"
	@echo "  make mypy       - Type check Python"
	@echo "  make build      - Build Docker images"
	@echo "  make dev        - Run development mode"
	@echo "  make refresh-olap - Refresh OLAP materialized views"
	@echo "  make demo       - Run demo scenario"
	@echo "  make clean      - Clean everything"

up:
	cd infra/docker && docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 15
	@echo "Services should be ready. Check with: make logs"

down:
	cd infra/docker && docker-compose down

logs:
	cd infra/docker && docker-compose logs -f

psql:
	docker exec -it fraud-dbms_postgres_1 psql -U postgres -d frauddb

sqlplus:
	docker exec -it fraud-dbms_oracle_1 sqlplus admin/password@XE

mongo:
	docker exec -it fraud-dbms_mongo_1 mongosh

seed:
	python tools/fake_data.py
	@echo "Waiting for triggers to fire and ETL to process..."
	@sleep 5
	@echo "Databases seeded. Check alerts: curl http://localhost:8000/v1/alerts?status=open"

test:
	pytest tests/ -v --tb=short

fmt:
	black services/ tests/ tools/
	ruff check --fix services/ tests/ tools/
	cd apps/web && npm run fmt || true

lint:
	ruff check services/ tests/ tools/
	mypy services/api services/worker
	cd apps/web && npm run lint || true

mypy:
	mypy services/api services/worker

build:
	cd infra/docker && docker-compose build

dev:
	cd infra/docker && docker-compose up

refresh-olap:
	docker exec fraud-dbms_api_1 curl -X POST http://localhost:8000/v1/admin/refresh-olap || echo "OLAP refresh triggered"

demo:
	@echo "=== Fraud Detection Demo ==="
	@echo "1. Opening dashboard at http://localhost:3000"
	@echo "2. Simulate suspicious transaction..."
	curl -X POST http://localhost:8000/v1/transactions \
		-H "x-api-key: dev-key" \
		-H "Content-Type: application/json" \
		-d '{"account_id":1,"amount":7000,"currency":"USD","merchant":"ATM-CORP","mcc":"6011","channel":"ATM","city":"NYC","country":"US","txn_time":"2025-01-15T00:15:00Z"}'
	@echo "\n3. Check alerts..."
	curl http://localhost:8000/v1/alerts?status=open
	@echo "\n4. Check analytics..."
	curl "http://localhost:8000/v1/analytics/anomalies?date_from=2025-01-01"

clean:
	cd infra/docker && docker-compose down -v
	docker system prune -f

