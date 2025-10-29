# 📸 Quick Screenshot Reference Card

## All Screenshots in Order

### 1. Docker Containers ⚙️
```bash
docker ps
# Screenshot terminal showing all 9 containers running
```

### 2. Login Page 🔐
**URL**: http://localhost:3000/login
- Screenshot entire page
- Shows: Email, Password fields, Demo credentials hint

### 3. Dashboard Initial 📊
**URL**: http://localhost:3000/dashboard (login first)
- Screenshot entire dashboard
- **Note down**: Active Alerts count, Frozen Accounts count
- Shows: 4 metric cards, severity chart, alerts table

### 4. API Docs 📚
**URL**: http://localhost:8000/docs
- Screenshot Swagger UI
- Shows: All API endpoints list

### 5. Database Before 💾
```bash
./tools/capture_db_state.sh
# Choose option 5 (Before transaction state)
# Screenshot terminal output
```
**OR manually**:
```bash
docker exec fraud-dbms_oracle_1 sqlplus -s system/password@XE <<EOF
SELECT account_id, status FROM app.accounts ORDER BY account_id;
SELECT * FROM app.fraud_alerts ORDER BY alert_time DESC FETCH FIRST 5 ROWS ONLY;
EOF
```
- **Note down**: Account 1 status, Alert count

### 6. Create Transaction 💳
```bash
curl -X POST http://localhost:8000/v1/transactions \
  -H "x-api-key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "amount": 8000,
    "merchant": "ATM-CORP",
    "txn_time": "2025-01-15T01:30:00Z"
  }' | python3 -m json.tool
```
- Screenshot terminal showing API call and response
- **Wait 3 seconds** for triggers to fire

### 7. Database After 💾
```bash
./tools/capture_db_state.sh
# Choose option 6 (After transaction state)
# Screenshot terminal output
```
**OR manually**:
```bash
docker exec fraud-dbms_oracle_1 sqlplus -s system/password@XE <<EOF
SELECT account_id, status FROM app.accounts ORDER BY account_id;
SELECT * FROM app.fraud_alerts ORDER BY alert_time DESC FETCH FIRST 6 ROWS ONLY;
EOF
```
- **Shows**: Account 1 now FROZEN, New alert created
- Compare with #5 to see the difference

### 8. Dashboard Updated 📊
**URL**: http://localhost:3000/dashboard
- Refresh page or wait 5 seconds
- Screenshot updated dashboard
- **Shows**: Alert count increased, Frozen Accounts increased
- **Compare with #3** to see changes

### 9. Grafana Monitoring 📈
**URL**: http://localhost:3001
- Login: `admin` / `admin`
- Screenshot Grafana interface
- Shows: Metrics, dashboards, monitoring

### 10. CRUD Comparisons 📋
Create a document or side-by-side screenshots showing:
- CREATE: Before/After database state (use #5 and #7)
- UPDATE: Before/After account status
- READ: API response (no DB change)
- DELETE: Cache clearing

---

## 🎯 Key Points to Show

1. **Docker**: All 9 services running healthy
2. **Login**: JWT authentication page
3. **Dashboard**: Real-time fraud detection UI
4. **API**: Swagger documentation
5. **DB Before**: Accounts ACTIVE, X alerts
6. **Transaction**: API call creating fraud
7. **DB After**: Account FROZEN, X+1 alerts (auto-triggered)
8. **Dashboard**: Updated counts (auto-refresh)
9. **Grafana**: Monitoring capabilities
10. **CRUD**: Database state changes

---

## ⚡ Quick Commands

```bash
# Helper script for database states
./tools/capture_db_state.sh

# Check system health
docker ps | grep fraud-dbms

# Test API
curl http://localhost:8000/healthz

# Create test transaction
curl -X POST http://localhost:8000/v1/transactions \
  -H "x-api-key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"account_id":1,"amount":8000,"merchant":"ATM-CORP","txn_time":"2025-01-15T01:30:00Z","currency":"USD","mcc":"6011","channel":"ATM"}'
```

---

## 📝 Screenshot Tips

- **Mac**: `Cmd + Shift + 3` (full), `Cmd + Shift + 4` (select)
- **Windows**: `Win + Shift + S` (Snipping Tool)
- **Save as**: PNG format for best quality
- **Name**: `01-docker-containers.png`, `02-login-page.png`, etc.
- **Size**: Full resolution, don't compress

**You're ready!** Follow this guide step-by-step. 🚀
