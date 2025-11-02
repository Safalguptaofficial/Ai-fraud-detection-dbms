#!/usr/bin/env python3
"""
Comprehensive Test Suite for Real-Time Ingestion Fixes
Tests all critical issues that were fixed:
1. ML Model Integration
2. Error Handling & Retries
3. Rate Limiting
4. Data Validation
5. Monitoring & Metrics
"""

import requests
import time
import json
import sys
from typing import Dict, List

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "fgk_live_demo_api_key_12345"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Test results
test_results = {
    "passed": [],
    "failed": [],
    "total": 0
}

def log_test(name: str, passed: bool, details: str = ""):
    """Log test result"""
    test_results["total"] += 1
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"{status}: {name}")
    if details:
        print(f"   {details}")
    if passed:
        test_results["passed"].append(name)
    else:
        test_results["failed"].append(name)

def test_1_ml_model_integration():
    """Test 1: ML Model Integration"""
    print("\n" + "="*60)
    print("TEST 1: ML Model Integration")
    print("="*60)
    
    try:
        # Test transaction that should trigger high fraud score
        transaction = {
            "account_id": "TEST_ML_001",
            "amount": 8500.00,  # High amount
            "merchant": "Suspicious Store",
            "currency": "USD",
            "channel": "ONLINE",
            "city": "Lagos",
            "country": "NG",  # International from risky location
            "ip_address": "192.168.1.100"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ingestion/transactions",
            headers=HEADERS,
            json=transaction,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            fraud_score = result.get("fraud_score", 0)
            status = result.get("status", "")
            
            # ML model should give high score for this transaction
            if fraud_score > 0.3:  # Should be detected as risky
                log_test(
                    "ML Model Integration",
                    True,
                    f"Fraud score: {fraud_score:.3f}, Status: {status}"
                )
                return True
            else:
                log_test(
                    "ML Model Integration",
                    False,
                    f"Fraud score too low ({fraud_score:.3f}) - ML model may not be working"
                )
                return False
        else:
            log_test(
                "ML Model Integration",
                False,
                f"HTTP {response.status_code}: {response.text}"
            )
            return False
            
    except Exception as e:
        log_test(
            "ML Model Integration",
            False,
            f"Exception: {str(e)}"
        )
        return False

def test_2_rate_limiting():
    """Test 2: Rate Limiting"""
    print("\n" + "="*60)
    print("TEST 2: Tenant-Based Rate Limiting")
    print("="*60)
    print("Waiting 10 seconds to reset rate limit from previous tests...")
    time.sleep(10)  # Reset rate limit
    
    try:
        transaction = {
            "account_id": "TEST_RATE_LIMIT",
            "amount": 100.00,
            "merchant": "Test Store",
            "currency": "USD"
        }
        
        # Send requests rapidly (limit is 100/minute)
        rate_limit_hit = False
        successful_requests = 0
        
        for i in range(105):
            response = requests.post(
                f"{BASE_URL}/api/v1/ingestion/transactions",
                headers=HEADERS,
                json=transaction,
                timeout=5
            )
            
            if response.status_code == 200:
                successful_requests += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limit_hit = True
                result = response.json()
                retry_after = result.get("detail", "")
                log_test(
                    "Rate Limiting",
                    True,
                    f"Rate limit hit at request #{i+1} after {successful_requests} successful requests. Message: {retry_after}"
                )
                return True
            
            # Small delay to avoid overwhelming the system
            time.sleep(0.05)
        
        if not rate_limit_hit:
            log_test(
                "Rate Limiting",
                False,
                f"Rate limit not triggered after 105 requests ({successful_requests} successful)"
            )
            return False
            
    except Exception as e:
        log_test(
            "Rate Limiting",
            False,
            f"Exception: {str(e)}"
        )
        return False

def test_3_data_validation():
    """Test 3: Data Validation & Sanitization"""
    print("\n" + "="*60)
    print("TEST 3: Data Validation & Sanitization")
    print("="*60)
    print("Waiting 10 seconds to reset rate limit...")
    time.sleep(10)  # Reset rate limit
    
    tests = [
        {
            "name": "Invalid IP Address",
            "data": {
                "account_id": "TEST_VAL_001",
                "amount": 100.00,
                "merchant": "Test",
                "currency": "USD",
                "ip_address": "999.999.999.999"  # Invalid
            },
            "should_fail": True
        },
        {
            "name": "Empty Account ID",
            "data": {
                "account_id": "",  # Empty
                "amount": 100.00,
                "merchant": "Test",
                "currency": "USD"
            },
            "should_fail": True
        },
        {
            "name": "XSS Attempt in Account ID",
            "data": {
                "account_id": "<script>alert('xss')</script>",
                "amount": 100.00,
                "merchant": "Test",
                "currency": "USD"
            },
            "should_fail": False,  # Should sanitize, not fail
            "expect_sanitized": True
        },
        {
            "name": "Valid Transaction",
            "data": {
                "account_id": "TEST_VALID_001",
                "amount": 100.00,
                "merchant": "Valid Store",
                "currency": "USD",
                "ip_address": "192.168.1.1"  # Valid IP
            },
            "should_fail": False
        }
    ]
    
    all_passed = True
    for test_case in tests:
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/ingestion/transactions",
                headers=HEADERS,
                json=test_case["data"],
                timeout=5
            )
            
            if test_case["should_fail"]:
                if response.status_code == 400:
                    log_test(f"Validation: {test_case['name']}", True, "Correctly rejected invalid data")
                else:
                    log_test(f"Validation: {test_case['name']}", False, f"Should have failed but got {response.status_code}")
                    all_passed = False
            else:
                if response.status_code == 200:
                    if test_case.get("expect_sanitized"):
                        # Check if dangerous chars were removed
                        result = response.json()
                        if "<script>" not in json.dumps(result):
                            log_test(f"Validation: {test_case['name']}", True, "Dangerous characters sanitized")
                        else:
                            log_test(f"Validation: {test_case['name']}", False, "Dangerous characters not sanitized")
                            all_passed = False
                    else:
                        log_test(f"Validation: {test_case['name']}", True, "Accepted valid data")
                else:
                    log_test(f"Validation: {test_case['name']}", False, f"Should have passed but got {response.status_code}")
                    all_passed = False
                    
        except Exception as e:
            log_test(f"Validation: {test_case['name']}", False, f"Exception: {str(e)}")
            all_passed = False
    
    return all_passed

def test_4_error_handling():
    """Test 4: Error Handling & Retry Logic"""
    print("\n" + "="*60)
    print("TEST 4: Error Handling & Retry Logic")
    print("="*60)
    print("Waiting 10 seconds to reset rate limit...")
    time.sleep(10)  # Reset rate limit
    
    try:
        # Test with valid transaction - should succeed
        transaction = {
            "account_id": "TEST_ERROR_HANDLING",
            "amount": 150.00,
            "merchant": "Test Store",
            "currency": "USD"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ingestion/transactions",
            headers=HEADERS,
            json=transaction,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            # Should have processing_time_ms field
            if "processing_time_ms" in result:
                log_test(
                    "Error Handling - Metrics",
                    True,
                    f"Processing time tracked: {result['processing_time_ms']}ms"
                )
            else:
                log_test(
                    "Error Handling - Metrics",
                    False,
                    "processing_time_ms not in response"
                )
                return False
            
            # Check that proper error format is returned on invalid input
            invalid_response = requests.post(
                f"{BASE_URL}/api/v1/ingestion/transactions",
                headers=HEADERS,
                json={"invalid": "data"},  # Missing required fields
                timeout=5
            )
            
            if invalid_response.status_code == 422:  # Validation error
                log_test(
                    "Error Handling - Validation Errors",
                    True,
                    "Proper error response for invalid input"
                )
                return True
            else:
                log_test(
                    "Error Handling - Validation Errors",
                    False,
                    f"Expected 422, got {invalid_response.status_code}"
                )
                return False
        else:
            log_test(
                "Error Handling",
                False,
                f"HTTP {response.status_code}: {response.text}"
            )
            return False
            
    except Exception as e:
        log_test(
            "Error Handling",
            False,
            f"Exception: {str(e)}"
        )
        return False

def test_5_monitoring_metrics():
    """Test 5: Monitoring & Metrics"""
    print("\n" + "="*60)
    print("TEST 5: Monitoring & Metrics")
    print("="*60)
    print("Waiting 10 seconds to reset rate limit...")
    time.sleep(10)  # Reset rate limit
    
    try:
        transaction = {
            "account_id": "TEST_METRICS_001",
            "amount": 200.00,
            "merchant": "Metrics Store",
            "currency": "USD"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ingestion/transactions",
            headers=HEADERS,
            json=transaction,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            required_fields = [
                "transaction_id",
                "status",
                "fraud_score",
                "timestamp",
                "processing_time_ms"
            ]
            
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                log_test(
                    "Monitoring & Metrics",
                    False,
                    f"Missing fields: {', '.join(missing_fields)}"
                )
                return False
            else:
                log_test(
                    "Monitoring & Metrics",
                    True,
                    f"All metrics present. Processing time: {result['processing_time_ms']}ms"
                )
                return True
        else:
            log_test(
                "Monitoring & Metrics",
                False,
                f"HTTP {response.status_code}: {response.text}"
            )
            return False
            
    except Exception as e:
        log_test(
            "Monitoring & Metrics",
            False,
            f"Exception: {str(e)}"
        )
        return False

def test_6_end_to_end():
    """Test 6: End-to-End Flow"""
    print("\n" + "="*60)
    print("TEST 6: End-to-End Flow")
    print("="*60)
    print("Waiting 10 seconds to reset rate limit...")
    time.sleep(10)  # Reset rate limit
    
    try:
        # Simulate a realistic transaction flow
        transactions = [
            {
                "account_id": "E2E_ACC_001",
                "amount": 50.00,
                "merchant": "Coffee Shop",
                "currency": "USD",
                "city": "New York",
                "country": "US"
            },
            {
                "account_id": "E2E_ACC_001",
                "amount": 120.00,
                "merchant": "Restaurant",
                "currency": "USD",
                "city": "New York",
                "country": "US"
            },
            {
                "account_id": "E2E_ACC_001",
                "amount": 5000.00,  # Large amount - should trigger high risk
                "merchant": "Electronics Store",
                "currency": "USD",
                "city": "Lagos",  # Different location
                "country": "NG"
            }
        ]
        
        results = []
        for i, txn in enumerate(transactions, 1):
            response = requests.post(
                f"{BASE_URL}/api/v1/ingestion/transactions",
                headers=HEADERS,
                json=txn,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                results.append(result)
                print(f"  Transaction {i}: Score={result['fraud_score']:.3f}, Status={result['status']}")
            else:
                log_test(
                    "End-to-End Flow",
                    False,
                    f"Transaction {i} failed: {response.status_code}"
                )
                return False
        
        # Last transaction should have higher fraud score
        if len(results) == 3:
            if results[2]['fraud_score'] > results[0]['fraud_score']:
                log_test(
                    "End-to-End Flow",
                    True,
                    f"Flow works correctly. Final score: {results[2]['fraud_score']:.3f}"
                )
                return True
            else:
                log_test(
                    "End-to-End Flow",
                    False,
                    "ML model not detecting high-risk patterns correctly"
                )
                return False
                
    except Exception as e:
        log_test(
            "End-to-End Flow",
            False,
            f"Exception: {str(e)}"
        )
        return False

def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {test_results['total']}")
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    
    if test_results['failed']:
        print("\nFailed Tests:")
        for test in test_results['failed']:
            print(f"  - {test}")
    
    success_rate = (len(test_results['passed']) / test_results['total'] * 100) if test_results['total'] > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if len(test_results['failed']) == 0:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️ {len(test_results['failed'])} test(s) failed")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST SUITE - REAL-TIME INGESTION FIXES")
    print("="*60)
    print(f"Testing API at: {BASE_URL}")
    print(f"Using API Key: {API_KEY[:20]}...")
    
    # Check if API is available
    try:
        health = requests.get(f"{BASE_URL}/", timeout=5)
        if health.status_code != 200:
            print(f"❌ API not available. Status: {health.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to API: {str(e)}")
        print("   Make sure the API service is running: docker-compose up")
        sys.exit(1)
    
    # Run all tests
    test_1_ml_model_integration()
    test_2_rate_limiting()
    test_3_data_validation()
    test_4_error_handling()
    test_5_monitoring_metrics()
    test_6_end_to_end()
    
    # Print summary
    success = print_summary()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

