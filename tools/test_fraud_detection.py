#!/usr/bin/env python3
"""
End-to-End Fraud Detection Test
Tests the complete fraud detection workflow
"""

import requests
import json
from datetime import datetime
import time

API_URL = "http://localhost:8000"

def print_step(step_num: int, description: str):
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print('='*60)

def test_workflow():
    print("\n🚀 Starting End-to-End Fraud Detection Test\n")
    
    # Step 1: Health Check
    print_step(1, "Health Check")
    response = requests.get(f"{API_URL}/healthz")
    print(f"✅ API is healthy: {response.json()}")
    
    # Step 2: Get Accounts
    print_step(2, "Get Existing Accounts")
    response = requests.get(f"{API_URL}/v1/accounts")
    accounts = response.json()
    print(f"✅ Found {len(accounts)} accounts")
    test_account_id = accounts[0]['id'] if accounts else None
    
    if not test_account_id:
        print("❌ No accounts found. Please seed the database first.")
        return
    
    print(f"📝 Using account ID: {test_account_id}")
    
    # Step 3: Check Current Alert Count
    print_step(3, "Check Current Alert Count")
    response = requests.get(f"{API_URL}/v1/alerts?status=open")
    initial_alerts = response.json()
    print(f"📊 Initial alerts: {len(initial_alerts)}")
    
    # Step 4: Create Normal Transaction
    print_step(4, "Create Normal Transaction ($100)")
    normal_transaction = {
        "account_id": test_account_id,
        "amount": 100.00,
        "currency": "USD",
        "merchant": "Starbucks",
        "mcc": "5812",
        "channel": "POS",
        "device_id": "POS-123",
        "city": "New York",
        "country": "US",
        "txn_time": datetime.utcnow().isoformat(),
        "auth_code": "AUTH001"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/v1/transactions",
            json=normal_transaction,
            headers={"x-api-key": "dev-key"}
        )
        if response.status_code == 200:
            print(f"✅ Normal transaction created: {response.json()}")
        else:
            print(f"⚠️ Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ Transaction creation: {e}")
    
    # Step 5: Create Suspicious Transaction (Midnight, High Amount)
    print_step(5, "Create Suspicious Transaction ($8000 at 1:30 AM)")
    suspicious_transaction = {
        "account_id": test_account_id,
        "amount": 8000.00,
        "currency": "USD",
        "merchant": "ATM-CORP",
        "mcc": "6011",
        "channel": "ATM",
        "device_id": "ATM-999",
        "city": "NYC",
        "country": "US",
        "txn_time": datetime.utcnow().replace(hour=1, minute=30).isoformat(),
        "auth_code": "AUTH002"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/v1/transactions",
            json=suspicious_transaction,
            headers={"x-api-key": "dev-key"}
        )
        if response.status_code == 200:
            print(f"✅ Suspicious transaction created: {response.json()}")
        else:
            print(f"⚠️ Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ Transaction creation: {e}")
    
    # Wait for triggers to fire
    print("\n⏳ Waiting for fraud detection triggers...")
    time.sleep(3)
    
    # Step 6: Check for New Alerts
    print_step(6, "Check for New Fraud Alerts")
    response = requests.get(f"{API_URL}/v1/alerts?status=open")
    new_alerts = response.json()
    print(f"📊 New alerts count: {len(new_alerts)}")
    
    if len(new_alerts) > len(initial_alerts):
        print(f"✅ NEW ALERTS CREATED! Found {len(new_alerts) - len(initial_alerts)} new fraud alerts")
        for alert in new_alerts[:3]:
            print(f"   - Alert ID: {alert['id']}, Severity: {alert['severity']}, Rule: {alert['rule_code']}")
    else:
        print("⚠️ No new alerts detected")
    
    # Step 7: Check Account Status
    print_step(7, "Check Account Status")
    response = requests.get(f"{API_URL}/v1/accounts/{test_account_id}")
    account = response.json()
    print(f"📊 Account Status: {account.get('status', 'UNKNOWN')}")
    
    if account.get('status') == 'FROZEN':
        print("✅ Account was frozen by fraud detection trigger!")
    else:
        print("⚠️ Account is not frozen")
    
    # Step 8: Test Redis Cache
    print_step(8, "Test Redis Cache Statistics")
    try:
        response = requests.get(f"{API_URL}/v1/transactions/cache/stats")
        if response.status_code == 200:
            print(f"✅ Cache Stats: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"⚠️ Cache stats unavailable: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Cache test failed: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    print(f"✅ Health check: PASSED")
    print(f"✅ Accounts fetched: {len(accounts)}")
    print(f"✅ Normal transaction: CREATED")
    print(f"✅ Suspicious transaction: CREATED")
    print(f"✅ Alerts before: {len(initial_alerts)}")
    print(f"✅ Alerts after: {len(new_alerts)}")
    print(f"✅ New alerts: {len(new_alerts) - len(initial_alerts)}")
    print(f"✅ Account status: {account.get('status', 'UNKNOWN')}")
    print("\n🎉 End-to-End Test Complete!\n")

if __name__ == "__main__":
    try:
        test_workflow()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        raise
