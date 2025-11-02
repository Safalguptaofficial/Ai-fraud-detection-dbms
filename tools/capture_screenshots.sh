#!/bin/bash

# Screenshot Capture Helper Script
# Guides you through capturing all required screenshots for DBMS submission

echo "📸 FraudGuard - Screenshot Capture Assistant"
echo "==========================================="
echo ""

PROJECT_DIR="/Users/safalgupta/Desktop/AI_FRAUD_DETECTION"
SCREENSHOT_DIR="$PROJECT_DIR/submission/screenshots"

# Create screenshots directory
mkdir -p "$SCREENSHOT_DIR"

echo "📁 Screenshots will be saved to: $SCREENSHOT_DIR"
echo ""
echo "This script will guide you through capturing all 12 screenshots."
echo "Press ENTER after capturing each screenshot to continue..."
echo ""

# Function to wait for user
wait_for_user() {
    read -p "Press ENTER when ready to continue..."
    echo ""
}

# Function to show database state
show_db_state() {
    local title=$1
    echo "=== $title ==="
    docker exec fraud-dbms_oracle_1 sqlplus -s system/password@XE <<EOF
SET PAGESIZE 50
SET LINESIZE 120
SELECT account_id, customer_id, status, balance FROM app.accounts ORDER BY account_id;
SELECT COUNT(*) as alert_count FROM app.fraud_alerts;
SELECT alert_id, account_id, rule_code, severity, status FROM app.fraud_alerts ORDER BY alert_time DESC FETCH FIRST 5 ROWS ONLY;
EOF
}

echo "🎬 Let's begin! Follow each step carefully."
echo ""

# Screenshot 1
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📷 Screenshot 1: Docker Containers Running"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Command to run:"
echo "  docker ps"
echo ""
echo "What to capture: Full terminal showing all 9 containers"
echo "Save as: $SCREENSHOT_DIR/01-docker-containers.png"
echo ""
docker ps
echo ""
echo "📸 Now capture this terminal window with Cmd+Shift+4"
wait_for_user

# Screenshot 2
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📷 Screenshot 2: Login Page"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "URL to open: http://localhost:3000/login"
echo "What to capture: Full browser window showing login page"
echo "Save as: $SCREENSHOT_DIR/02-login-page.png"
echo ""
echo "📸 Open the URL in your browser and capture with Cmd+Shift+4"
wait_for_user

# Screenshot 3
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📷 Screenshot 3: Dashboard - Initial State"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Steps:"
echo "  1. Login at http://localhost:3000/login"
echo "     Email: analyst@bank.com"
echo "     Password: password123"
echo "  2. Wait for dashboard to load (5 seconds)"
echo "  3. NOTE DOWN these numbers:"
echo "     - Active Alerts: _____"
echo "     - Frozen Accounts: _____"
echo "     - Total Accounts: _____"
echo ""
echo "Save as: $SCREENSHOT_DIR/03-dashboard-initial.png"
echo ""
echo "📸 Capture the full dashboard"
wait_for_user

# Screenshot 4
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📷 Screenshot 4: API Documentation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "URL to open: http://localhost:8000/docs"
echo "What to capture: Swagger UI showing all endpoints"
echo "Save as: $SCREENSHOT_DIR/04-api-documentation.png"
echo ""
echo "📸 Open the URL and capture the Swagger interface"
wait_for_user

# Screenshot 5
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📷 Screenshot 5: Database BEFORE Transaction"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Querying database state..."
echo ""
show_db_state "DATABASE STATE - BEFORE"
echo ""
echo "NOTE DOWN:"
echo "  - Account 1 status: _____"
echo "  - Total alerts: _____"
echo ""
echo "Save as: $SCREENSHOT_DIR/05-database-before.png"
echo ""
echo "📸 Capture this terminal output"
wait_for_user

# Screenshot 6
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📷 Screenshot 6: CREATE Transaction (API Call)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Running fraudulent transaction..."
echo ""
curl -X POST http://localhost:8000/v1/transactions \
  -H "x-api-key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "amount": 8000.00,
    "currency": "USD",
    "merchant": "ATM-CORP",
    "mcc": "6011",
    "channel": "ATM",
    "device_id": "ATM-999",
    "city": "NYC",
    "country": "US",
    "txn_time": "2025-01-15T01:30:00Z",
    "auth_code": "AUTH002"
  }' | python3 -m json.tool
echo ""
echo "Save as: $SCREENSHOT_DIR/06-create-transaction.png"
echo ""
echo "📸 Capture this terminal showing the API call and response"
echo ""
echo "⏳ Waiting 3 seconds for triggers to fire..."
sleep 3
wait_for_user

# Screenshot 7
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📷 Screenshot 7: Database AFTER Transaction"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Querying updated database state..."
echo ""
show_db_state "DATABASE STATE - AFTER (ACCOUNT FROZEN!)"
echo ""
echo "OBSERVE THE CHANGES:"
echo "  - Account 1 status: FROZEN ← CHANGED!"
echo "  - New alert created ← AUTO-CREATED!"
echo ""
echo "Save as: $SCREENSHOT_DIR/07-database-after.png"
echo ""
echo "📸 Capture this terminal showing the changes"
wait_for_user

# Screenshot 8
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📷 Screenshot 8: Dashboard Updated"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Steps:"
echo "  1. Go back to http://localhost:3000/dashboard"
echo "  2. Wait 5-10 seconds for auto-refresh"
echo "  3. Compare with Screenshot 3:"
echo "     - Active Alerts increased? _____"
echo "     - Frozen Accounts increased? _____"
echo "     - New HIGH alert visible? _____"
echo ""
echo "Save as: $SCREENSHOT_DIR/08-dashboard-updated.png"
echo ""
echo "📸 Capture the updated dashboard showing changes"
wait_for_user

# Screenshot 9
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📷 Screenshot 9: Grafana Monitoring"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "URL to open: http://localhost:3001"
echo "Login: admin / admin"
echo "What to capture: Grafana interface or dashboards"
echo "Save as: $SCREENSHOT_DIR/09-grafana-monitoring.png"
echo ""
echo "📸 Open Grafana and capture the monitoring interface"
wait_for_user

# Screenshot 10 (Optional)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📷 Screenshot 10: Network Graph (Optional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "URL to open: http://localhost:3000/network-graph"
echo "What to capture: Network visualization"
echo "Save as: $SCREENSHOT_DIR/10-network-graph.png"
echo ""
echo "📸 Capture the network graph visualization"
wait_for_user

# Screenshot 11 (Optional)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📷 Screenshot 11: ML Model (Optional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "URL to open: http://localhost:3000/ml-model"
echo "What to capture: ML prediction interface"
echo "Save as: $SCREENSHOT_DIR/11-ml-model.png"
echo ""
echo "📸 Capture the ML model interface"
wait_for_user

# Screenshot 12 (Optional)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📷 Screenshot 12: Investigation (Optional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "URL to open: http://localhost:3000/investigation"
echo "What to capture: Investigation timeline"
echo "Save as: $SCREENSHOT_DIR/12-investigation.png"
echo ""
echo "📸 Capture the investigation workspace"
wait_for_user

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Screenshot Capture Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📂 Screenshots saved to: $SCREENSHOT_DIR"
echo ""
echo "📋 Checklist:"
echo "   [ ] All 12 screenshots captured"
echo "   [ ] Images are clear and readable"
echo "   [ ] URLs visible in browser screenshots"
echo "   [ ] Terminal text is legible"
echo ""
echo "📝 Next Steps:"
echo "   1. Review all screenshots"
echo "   2. Open DBMS_PROJECT_SUBMISSION.md"
echo "   3. Paste screenshots in marked locations"
echo "   4. Fill in 'Before' and 'After' values"
echo "   5. Add your name and roll number"
echo "   6. Run: ./tools/generate_pdf.sh"
echo ""
echo "🎉 Good luck with your submission!"

