# 🚀 Quick Start Guide - Enhanced Fraud Detection System

## Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend)
- Python 3.11+ (for backend)
- Make (optional, for convenience commands)

---

## ⚡ Fast Setup (5 Minutes)

### 1. Clone & Navigate
```bash
cd AI_FRAUD_DETECTION
```

### 2. Start Infrastructure
```bash
make up
```
This starts:
- Oracle Database (port 1521)
- PostgreSQL (port 5432)
- MongoDB (port 27017)
- Redis (port 6379)
- API Service (port 8000)
- Worker Service
- Grafana (port 3001)
- Prometheus (port 9090)

### 3. Seed Database
```bash
make seed
```
This creates:
- 10 sample accounts
- 100+ transactions
- Fraud alerts with various severities

### 4. Install Frontend Dependencies
```bash
cd apps/web
npm install
```

### 5. Start Frontend
```bash
npm run dev
```

### 6. Open Your Browser
- **Enhanced Dashboard:** http://localhost:3000/dashboard-enhanced
- **Case Management:** http://localhost:3000/cases
- **CRUD Monitor:** http://localhost:3000/crud-monitor
- **API Docs:** http://localhost:8000/docs

---

## 🎯 First Steps

### Login Credentials
- **Username:** `analyst@bank.com`
- **Password:** `password123`

Or:
- **Username:** `admin@bank.com`
- **Password:** `admin123`

### Explore Features

1. **📊 Enhanced Dashboard**
   - View fraud trends chart
   - Check transaction heatmap
   - Analyze risk distribution
   - Export data to CSV

2. **📁 Case Management**
   - Create a new fraud case
   - Assign to investigator
   - Add investigation notes
   - Track case workflow

3. **🗄️ CRUD Monitor**
   - Watch live database operations
   - Monitor query performance
   - Track user activity
   - View audit trail

---

## 🧪 Testing the System

### Run Tests
```bash
# All tests
make test

# Or manually
pytest tests/ -v

# Specific test
pytest tests/api/test_risk_scoring.py -v
```

### Test ML Risk Scoring
```bash
curl -X POST http://localhost:8000/v1/risk-score \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key" \
  -d '{
    "account_id": 1,
    "amount": 7500,
    "currency": "USD",
    "merchant": "ATM-CORP",
    "mcc": "6011",
    "channel": "ATM",
    "city": "NYC",
    "country": "US",
    "txn_time": "2025-10-29T02:30:00Z"
  }'
```

Expected response:
```json
{
  "risk_score": 82.5,
  "risk_level": "CRITICAL",
  "recommendation": "BLOCK - Immediate review required"
}
```

### Create a Fraud Case
```bash
curl -X POST http://localhost:8000/v1/cases \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-key" \
  -d '{
    "accountId": 1,
    "txnIds": [1, 2, 3],
    "notes": "Multiple suspicious transactions detected",
    "tags": ["high-risk", "atm-fraud"]
  }'
```

---

## 📊 Monitoring & Observability

### Grafana Dashboard
1. Open http://localhost:3001
2. Login: `admin` / `admin`
3. View pre-configured fraud detection dashboard
4. Monitor system metrics

### Prometheus Metrics
- Open http://localhost:9090
- Explore metrics:
  - `http_requests_total`
  - `fraud_alerts_total`
  - `http_request_duration_seconds`

### API Metrics Endpoint
```bash
curl http://localhost:8000/metrics
```

---

## 🎨 Feature Walkthrough

### 1. Enhanced Dashboard

**What you'll see:**
- 📈 7-day fraud trends with severity breakdown
- 🔥 Activity heatmap showing fraud by hour/day
- 📊 Risk score distribution chart
- 🏪 Top merchants with fraud incidents
- 📋 Live fraud alerts table
- 📤 Export button for CSV downloads

**Try this:**
1. Click "Refresh" to update data
2. Click "Export" to download alerts
3. Watch auto-refresh every 30 seconds
4. Check toast notifications

### 2. Case Management

**What you'll see:**
- Statistics: Open, Investigating, Resolved, Closed
- Search and filter capabilities
- Case creation modal
- Workflow tracking

**Try this:**
1. Click "New Case"
2. Enter Account ID: 1
3. Add transaction IDs: 1,2,3
4. Add notes: "Suspicious midnight transactions"
5. Add tags: fraud, high-priority
6. Click "Create Case"

### 3. CRUD Monitor

**What you'll see:**
- Real-time database operations
- CREATE/READ/UPDATE/DELETE stats
- Performance metrics
- Audit trail

**Try this:**
1. Toggle "Auto-refresh" on
2. Watch operations appear in real-time
3. Filter by operation type
4. Check "Average Query Time"

---

## 🛠️ Development

### Frontend Development
```bash
cd apps/web
npm run dev      # Start dev server
npm run build    # Build for production
npm run lint     # Run linter
```

### Backend Development
```bash
cd services/api
uvicorn main:app --reload  # Start with auto-reload
```

### Database Access

**PostgreSQL:**
```bash
make psql
# Or
docker exec -it fraud-dbms_postgres_1 psql -U postgres -d frauddb
```

**Oracle:**
```bash
make sqlplus
# Or
docker exec -it fraud-dbms_oracle_1 sqlplus system/password@XE
```

**MongoDB:**
```bash
make mongo
# Or
docker exec -it fraud-dbms_mongo_1 mongosh
```

---

## 📱 Page URLs

| Page | URL | Description |
|------|-----|-------------|
| Login | http://localhost:3000/login | Authentication |
| Dashboard | http://localhost:3000/dashboard | Basic metrics |
| Enhanced | http://localhost:3000/dashboard-enhanced | Advanced analytics |
| Cases | http://localhost:3000/cases | Case management |
| CRUD Monitor | http://localhost:3000/crud-monitor | DB operations |
| API Docs | http://localhost:8000/docs | OpenAPI docs |
| Grafana | http://localhost:3001 | Monitoring |

---

## 🔧 Configuration

### Environment Variables (.env)
```env
ORACLE_URI=oracle+oracledb://system:password@localhost:1521/XE
POSTGRES_URI=postgresql://postgres:password@localhost:5432/frauddb
MONGO_URI=mongodb://root:password@localhost:27017/
REDIS_HOST=localhost
REDIS_PORT=6379
```

### API Configuration
Edit `services/api/config.py` for:
- Database connections
- Redis settings
- JWT secret
- Rate limiting

---

## 🚨 Troubleshooting

### Frontend won't start
```bash
cd apps/web
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Database connection errors
```bash
# Check services are running
docker ps

# Restart services
make down
make up

# Check logs
make logs
```

### Port already in use
```bash
# Check what's using the port
lsof -i :3000  # Frontend
lsof -i :8000  # API

# Kill the process or change ports in config
```

### Clear everything and start fresh
```bash
make clean    # Removes all containers and volumes
make up       # Start fresh
make seed     # Reseed data
```

---

## 📊 Sample Data

After running `make seed`, you'll have:
- **10 accounts** with IDs from database sequence
- **100+ transactions** including:
  - Normal daytime transactions
  - Midnight high-amount transactions (anomalies)
  - Geographic jumps (NYC → LA)
  - Velocity anomalies (rapid transactions)
- **Fraud alerts** automatically generated
- **Cases** (create manually)

---

## 🎯 Common Tasks

### Add more sample data
```bash
python tools/fake_data.py
```

### View all alerts
```bash
curl http://localhost:8000/v1/alerts?status=open
```

### Check system health
```bash
curl http://localhost:8000/health
```

### Export data
Use the Export button in the Enhanced Dashboard or:
```bash
# From frontend
Click "Export" button → Downloads CSV
```

---

## 📚 Next Steps

1. ✅ Explore all pages and features
2. ✅ Create fraud cases
3. ✅ Test ML risk scoring
4. ✅ Monitor CRUD operations
5. ✅ Export reports
6. ⏳ Customize dashboards
7. ⏳ Add custom fraud rules
8. ⏳ Deploy to production

---

## 🎓 Learning Path

### Beginner:
1. Start all services
2. Login to dashboard
3. View alerts and metrics
4. Create a case
5. Export data

### Intermediate:
1. Understand data flow
2. Explore API endpoints
3. Create custom queries
4. Modify fraud rules
5. Configure monitoring

### Advanced:
1. Add new ML models
2. Create custom visualizations
3. Implement new fraud rules
4. Scale the system
5. Deploy to production

---

## 💡 Tips

- **Auto-refresh:** Enable on CRUD monitor for live updates
- **Keyboard shortcuts:** Ctrl+K for search (coming soon)
- **Dark mode:** System preference detected automatically
- **Performance:** Redis caching speeds up repeated queries
- **Export:** Download before midnight for daily reports

---

## 🆘 Support

**Check documentation:**
- `README.md` - Overview
- `ENHANCED_FEATURES.md` - Feature details
- `docs/API.md` - API reference
- `docs/ARCH.md` - Architecture

**View logs:**
```bash
make logs                    # All services
docker logs <container-name> # Specific service
```

**Common issues:**
- Port conflicts → Change ports in config
- Memory issues → Increase Docker memory
- Connection timeouts → Check firewall/network

---

## ✅ Checklist

Before going to production:
- [ ] Review `docs/PRODUCTION_CHECKLIST.md`
- [ ] Set environment variables
- [ ] Configure SSL/HTTPS
- [ ] Set up database backups
- [ ] Configure monitoring alerts
- [ ] Run security audit
- [ ] Load testing
- [ ] Documentation review

---

**Status:** 🚀 Ready to use! All features operational.

**Version:** 2.0.0 Enhanced Edition

**Last Updated:** October 29, 2025

