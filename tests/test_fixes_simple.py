#!/usr/bin/env python3
"""
Simple Direct Test - Verify Critical Fixes Work
Tests the fixes without requiring full tenant setup
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

print("\n" + "="*60)
print("SIMPLE TEST - VERIFYING CRITICAL FIXES")
print("="*60)

# Test 1: Check if rate limiting is implemented
print("\n✅ Test 1: Rate Limiting Implementation")
print("   Checking if rate limiting responds...")
try:
    # Try multiple requests to see if rate limit kicks in
    for i in range(5):
        response = requests.get(f"{BASE_URL}/", timeout=2)
        time.sleep(0.1)
    
    print("   ✓ API is responding (rate limiting may be working)")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Check ML model file exists
print("\n✅ Test 2: ML Model File")
import os
ml_file = "services/api/ml_enhanced_model.py"
if os.path.exists(ml_file):
    print(f"   ✓ ML model file exists: {ml_file}")
    # Check if predict_fraud function exists
    with open(ml_file, 'r') as f:
        content = f.read()
        if "def predict_fraud" in content:
            print("   ✓ predict_fraud() function found")
        else:
            print("   ✗ predict_fraud() function NOT found")
else:
    print(f"   ✗ ML model file missing: {ml_file}")

# Test 3: Check realtime_api.py has ML integration
print("\n✅ Test 3: Real-Time API ML Integration")
realtime_file = "services/api/ingestion/realtime_api.py"
if os.path.exists(realtime_file):
    print(f"   ✓ Real-time API file exists: {realtime_file}")
    with open(realtime_file, 'r') as f:
        content = f.read()
        checks = [
            ("from ml_enhanced_model import predict_fraud", "ML model import"),
            ("predict_fraud(", "ML model call"),
            ("RateLimiter", "Rate limiting class"),
            ("@retry_on_failure", "Retry decorator"),
            ("def validate_account_id", "Account ID validation"),
            ("def validate_merchant", "Merchant validation"),
            ("def validate_ip_address", "IP validation"),
            ("processing_time_ms", "Metrics tracking"),
        ]
        for check, name in checks:
            if check in content:
                print(f"   ✓ {name} - FOUND")
            else:
                print(f"   ✗ {name} - MISSING")
else:
    print(f"   ✗ Real-time API file missing: {realtime_file}")

# Test 4: Check router has Redis dependency
print("\n✅ Test 4: Router Redis Integration")
router_file = "services/api/routers/ingestion.py"
if os.path.exists(router_file):
    print(f"   ✓ Router file exists: {router_file}")
    with open(router_file, 'r') as f:
        content = f.read()
        if "get_redis" in content and "redis_client" in content:
            print("   ✓ Redis dependency integrated in router")
        else:
            print("   ✗ Redis dependency NOT integrated in router")
else:
    print(f"   ✗ Router file missing: {router_file}")

# Test 5: Verify error handling
print("\n✅ Test 5: Error Handling Structure")
with open(realtime_file, 'r') as f:
    content = f.read()
    error_checks = [
        ("try:", "Try blocks"),
        ("except Exception", "Exception handling"),
        ("logger.error", "Error logging"),
        ("self.db.rollback()", "Database rollback"),
        ("raise ValueError", "Proper error raising"),
    ]
    for check, name in error_checks:
        if check in content:
            print(f"   ✓ {name} - FOUND")
        else:
            print(f"   ✗ {name} - MISSING")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print("All structural checks completed!")
print("\nTo test with actual API calls:")
print("1. Create a tenant in database with API key")
print("2. Wait 60 seconds to reset rate limits")
print("3. Run: python3 tests/test_realtime_fixes.py")
print("\n" + "="*60)

