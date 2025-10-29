#!/bin/bash
# Database State Capture Helper Script
# This script helps capture database states for before/after comparisons

echo "=== Database State Capture Helper ==="
echo ""
echo "This script will help you capture database states for screenshots"
echo ""

# Function to show accounts
show_accounts() {
    echo "📊 ACCOUNTS TABLE:"
    echo "-------------------"
    docker exec fraud-dbms_oracle_1 sqlplus -s system/password@XE <<EOF
SET PAGESIZE 50
SET LINESIZE 120
SELECT account_id, customer_id, status, balance 
FROM app.accounts 
ORDER BY account_id;
EOF
    echo ""
}

# Function to show alerts
show_alerts() {
    echo "🚨 FRAUD ALERTS TABLE:"
    echo "----------------------"
    docker exec fraud-dbms_oracle_1 sqlplus -s system/password@XE <<EOF
SET PAGESIZE 50
SET LINESIZE 120
SELECT alert_id, account_id, rule_code, severity, status,
       TO_CHAR(alert_time, 'YYYY-MM-DD HH24:MI:SS') as alert_time
FROM app.fraud_alerts 
ORDER BY alert_time DESC 
FETCH FIRST 5 ROWS ONLY;
EOF
    echo ""
}

# Function to show transaction count
show_transaction_count() {
    echo "💳 TRANSACTION COUNT:"
    echo "--------------------"
    docker exec fraud-dbms_oracle_1 sqlplus -s system/password@XE <<EOF
SELECT COUNT(*) as total_transactions FROM app.transactions;
EOF
    echo ""
}

# Menu
echo "Select what to capture:"
echo "1. Full database state (accounts + alerts + count)"
echo "2. Accounts only"
echo "3. Alerts only"
echo "4. Transaction count only"
echo "5. Before transaction state (for screenshot)"
echo "6. After transaction state (for screenshot)"
echo ""
read -p "Enter choice (1-6): " choice

case $choice in
    1)
        echo "📸 CAPTURE THIS ENTIRE OUTPUT:"
        echo "================================"
        show_accounts
        show_alerts
        show_transaction_count
        echo "================================"
        ;;
    2)
        show_accounts
        ;;
    3)
        show_alerts
        ;;
    4)
        show_transaction_count
        ;;
    5)
        echo "📸 BEFORE TRANSACTION STATE"
        echo "================================"
        echo "Take a screenshot of this output for 'Database Before Transaction'"
        echo ""
        show_accounts
        show_alerts
        show_transaction_count
        echo ""
        echo "✅ Note down these values for comparison:"
        echo "   - Number of accounts:"
        echo "   - Account 1 status:"
        echo "   - Number of fraud alerts:"
        echo "================================"
        ;;
    6)
        echo "📸 AFTER TRANSACTION STATE"
        echo "================================"
        echo "Take a screenshot of this output for 'Database After Transaction'"
        echo ""
        show_accounts
        show_alerts
        show_transaction_count
        echo ""
        echo "✅ Compare with 'Before' screenshot to see:"
        echo "   - Account status changed (ACTIVE → FROZEN)"
        echo "   - New fraud alert created"
        echo "   - Alert shows rule: AMOUNT_GT_5000_MIDNIGHT"
        echo "================================"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "💡 Tip: Use Cmd+Shift+4 (Mac) or Snipping Tool (Windows) to capture"
echo "💡 Save screenshot with descriptive name like 'db-before-transaction.png'"
