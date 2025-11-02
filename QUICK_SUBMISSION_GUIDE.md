# 🚀 Quick Submission Guide (1-Hour Workflow)

## ⏱️ Total Time: ~60 minutes

---

## Step 1: Start System (5 min)

```bash
cd /Users/safalgupta/Desktop/AI_FRAUD_DETECTION
make up
# Wait 2-3 minutes for containers to be healthy
make seed
```

**Verify:**
```bash
docker ps  # Should show 9 containers
```

---

## Step 2: Capture Screenshots (25 min)

### Run Interactive Helper:
```bash
./tools/capture_screenshots.sh
```

### Or Manual Capture:

1. **Docker containers** (1 min)
   ```bash
   docker ps
   # Screenshot terminal → 01-docker-containers.png
   ```

2. **Login page** (2 min)
   - Open: http://localhost:3000/login
   - Screenshot → 02-login-page.png

3. **Dashboard initial** (2 min)
   - Login: analyst@bank.com / password123
   - Note: Active Alerts, Frozen Accounts counts
   - Screenshot → 03-dashboard-initial.png

4. **API docs** (2 min)
   - Open: http://localhost:8000/docs
   - Screenshot → 04-api-documentation.png

5. **Database BEFORE** (3 min)
   ```bash
   docker exec fraud-dbms_oracle_1 sqlplus -s system/password@XE <<EOF
   SELECT account_id, status FROM app.accounts WHERE account_id = 1;
   SELECT COUNT(*) FROM app.fraud_alerts;
   EOF
   # Screenshot → 05-database-before.png
   ```

6. **CREATE transaction** (3 min)
   ```bash
   curl -X POST http://localhost:8000/v1/transactions \
     -H "x-api-key: dev-key" \
     -H "Content-Type: application/json" \
     -d '{"account_id": 1, "amount": 8000, "merchant": "ATM-CORP", "txn_time": "2025-01-15T01:30:00Z", "currency": "USD", "mcc": "6011", "channel": "ATM"}'
   # Screenshot → 06-create-transaction.png
   ```
   
   **⏳ Wait 3 seconds for triggers!**

7. **Database AFTER** (3 min)
   ```bash
   docker exec fraud-dbms_oracle_1 sqlplus -s system/password@XE <<EOF
   SELECT account_id, status FROM app.accounts WHERE account_id = 1;
   SELECT * FROM app.fraud_alerts ORDER BY alert_time DESC FETCH FIRST 1 ROWS ONLY;
   EOF
   # Screenshot → 07-database-after.png
   ```
   **✅ Account 1 should be FROZEN now!**

8. **Dashboard updated** (3 min)
   - Refresh: http://localhost:3000/dashboard
   - Wait 10 seconds for auto-update
   - Verify: Alert count increased, Frozen count +1
   - Screenshot → 08-dashboard-updated.png

9. **Grafana** (2 min)
   - Open: http://localhost:3001 (admin/admin)
   - Screenshot → 09-grafana-monitoring.png

10-12. **Optional** (4 min)
    - Network graph: http://localhost:3000/network-graph
    - ML model: http://localhost:3000/ml-model
    - Investigation: http://localhost:3000/investigation

**Save all to:** `submission/screenshots/`

---

## Step 3: Edit Document (20 min)

1. **Open document:**
   ```bash
   open DBMS_PROJECT_SUBMISSION.md
   ```

2. **Fill in (5 min):**
   - Student Name: ________________
   - Roll Number: ________________
   - Date: October 30, 2025

3. **Paste screenshots (10 min):**
   - Find: `**[PASTE SCREENSHOT HERE]**`
   - Replace with your screenshot images
   - Or add image links if using markdown

4. **Fill values (5 min):**
   - Find all: `_____`
   - Replace with actual numbers from your screenshots
   - Example: 
     - Before: Active Alerts: _____
     - After: Active Alerts: 4

---

## Step 4: Generate PDF (5 min)

```bash
./tools/generate_pdf.sh
```

**If pandoc not installed:**
- Use VS Code extension "Markdown PDF"
- Or copy to Google Docs → Download as PDF
- Or copy to Word → Save as PDF

---

## Step 5: Review & Submit (5 min)

**Checklist:**
- [ ] PDF opens correctly
- [ ] All 12 screenshots visible
- [ ] Your name and roll number present
- [ ] No `_____` placeholders remain
- [ ] CRUD sections complete
- [ ] 30-40 pages total
- [ ] File size < 20 MB

**Submit:**
- `DBMS_PROJECT_SUBMISSION.pdf`

---

## 🎯 Key Screenshots to Focus On

### Most Important (25 points):
- **#5 & #7:** Database before/after (shows trigger magic!)
- **#6:** API call creating fraud
- **#8:** Dashboard updated automatically

### Important (15 points):
- **#1:** System architecture (Docker)
- **#3:** Dashboard features
- **#4:** API documentation

### Good to Have (10 points):
- **#2:** Authentication
- **#9:** Monitoring
- **#10-12:** Optional features

---

## 💡 Pro Tips

1. **Focus on the CREATE operation** - It's the star of your submission!
2. **Show the automatic trigger** - Account FROZEN without manual intervention
3. **Compare before/after** - Make the changes obvious
4. **Highlight real-time updates** - Dashboard refreshes automatically
5. **Emphasize multi-database** - Oracle + PostgreSQL + MongoDB + Redis

---

## 🔥 What Makes Your Project Stand Out

✅ **Database Triggers:** Automatic fraud detection at DB level  
✅ **Polyglot Persistence:** 4 different database systems  
✅ **Production Ready:** Docker, monitoring, authentication  
✅ **Real-time:** Dashboard updates live  
✅ **Modern Stack:** Latest technologies  
✅ **Professional UI:** Dark mode, charts, maps  

---

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Containers not starting | `make down && make up` |
| Account already frozen | Reset: `UPDATE app.accounts SET status='ACTIVE' WHERE account_id=1` |
| Dashboard not updating | Wait 10 seconds or refresh manually |
| Can't generate PDF | Use VS Code extension or online converter |
| Screenshots not clear | Increase zoom to 125%, use PNG format |

---

## 📋 File Checklist

```
submission/
├── DBMS_PROJECT_SUBMISSION.pdf  ← SUBMIT THIS!
└── screenshots/
    ├── 01-docker-containers.png
    ├── 02-login-page.png
    ├── 03-dashboard-initial.png
    ├── 04-api-documentation.png
    ├── 05-database-before.png
    ├── 06-create-transaction.png
    ├── 07-database-after.png
    ├── 08-dashboard-updated.png
    ├── 09-grafana-monitoring.png
    ├── 10-network-graph.png
    ├── 11-ml-model.png
    └── 12-investigation.png
```

---

## ✅ Ready? Let's Go!

```bash
# 1. Start
make up && make seed

# 2. Screenshots
./tools/capture_screenshots.sh

# 3. Edit
open DBMS_PROJECT_SUBMISSION.md

# 4. PDF
./tools/generate_pdf.sh

# 5. Submit!
```

---

**Good luck! 🎉**

