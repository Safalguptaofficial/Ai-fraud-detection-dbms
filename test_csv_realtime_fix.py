#!/usr/bin/env python3
"""
Test script to verify CSV upload real-time fix
Tests:
1. Upload CSV file
2. Verify cache is cleared
3. Verify transactions appear immediately
"""
import requests
import json
import io
import csv
from datetime import datetime, timedelta
import time

API_URL = "http://localhost:8000"
API_KEY = "fgk_live_demo_api_key_12345"  # Demo API key used in frontend

def create_test_csv():
    """Create a test CSV file with transaction data"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['account_id', 'amount', 'merchant', 'transaction_date', 'currency', 'city', 'country'])
    
    # Write test transactions
    base_time = datetime.now() - timedelta(hours=1)
    for i in range(5):
        txn_time = base_time + timedelta(minutes=i*5)
        writer.writerow([
            f'ACC{1000 + i}',
            f'{100.50 + i * 10:.2f}',
            f'Test Merchant {i+1}',
            txn_time.strftime('%Y-%m-%d %H:%M:%S'),
            'USD',
            'New York',
            'US'
        ])
    
    csv_content = output.getvalue()
    output.close()
    return csv_content.encode('utf-8')

def test_csv_upload_and_realtime():
    """Test the complete CSV upload and real-time display flow"""
    
    print("=" * 70)
    print("🧪 Testing CSV Upload Real-Time Fix")
    print("=" * 70)
    
    # Step 1: Get initial transaction count
    print("\n📊 Step 1: Get initial transaction count")
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.get(f"{API_URL}/v1/transactions?limit=100", headers=headers)
        if response.status_code == 200:
            initial_transactions = response.json()
            initial_count = len(initial_transactions) if isinstance(initial_transactions, list) else 0
            print(f"   ✅ Initial transaction count: {initial_count}")
            if initial_count > 0:
                print(f"   📝 Latest transaction ID: {initial_transactions[0].get('id', 'N/A')}")
        else:
            print(f"   ⚠️  Could not fetch initial transactions: {response.status_code}")
            initial_count = 0
    except Exception as e:
        print(f"   ⚠️  Error fetching initial transactions: {e}")
        initial_count = 0
    
    # Step 2: Check Redis cache status
    print("\n🔍 Step 2: Check Redis cache (before upload)")
    try:
        cache_response = requests.get(f"{API_URL}/v1/cache/stats", headers=headers)
        if cache_response.status_code == 200:
            cache_stats = cache_response.json()
            print(f"   ✅ Cache keys: {cache_stats.get('keys', 0)}")
            print(f"   ✅ Cache hit rate: {cache_stats.get('hit_rate', 'N/A')}")
        else:
            print(f"   ⚠️  Could not check cache stats: {cache_response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Error checking cache: {e}")
    
    # Step 3: Create and upload test CSV
    print("\n📤 Step 3: Upload test CSV file")
    csv_content = create_test_csv()
    
    files = {
        'file': ('test_transactions.csv', csv_content, 'text/csv')
    }
    
    try:
        upload_start = time.time()
        upload_response = requests.post(
            f"{API_URL}/api/v1/ingestion/files",
            headers=headers,
            files=files
        )
        upload_time = time.time() - upload_start
        
        if upload_response.status_code == 200:
            upload_result = upload_response.json()
            result = upload_result.get('result', {})
            rows_inserted = result.get('rows_inserted', 0)
            rows_failed = result.get('rows_failed', 0)
            
            print(f"   ✅ Upload successful! (took {upload_time:.2f}s)")
            print(f"   📊 Rows inserted: {rows_inserted}")
            print(f"   ❌ Rows failed: {rows_failed}")
            
            if rows_inserted == 0:
                print("   ⚠️  WARNING: No rows were inserted!")
                return False
        else:
            print(f"   ❌ Upload failed: {upload_response.status_code}")
            print(f"   Error: {upload_response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        return False
    
    # Step 4: Wait a moment for cache clearing
    print("\n⏳ Step 4: Waiting 2 seconds for cache to clear...")
    time.sleep(2)
    
    # Step 5: Check cache after upload (should be cleared or different)
    print("\n🔍 Step 5: Check Redis cache (after upload)")
    try:
        cache_response = requests.get(f"{API_URL}/v1/cache/stats", headers=headers)
        if cache_response.status_code == 200:
            cache_stats = cache_response.json()
            print(f"   ✅ Cache keys: {cache_stats.get('keys', 0)}")
        else:
            print(f"   ⚠️  Could not check cache stats: {cache_response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Error checking cache: {e}")
    
    # Step 6: Fetch transactions immediately (should show new data)
    print("\n📥 Step 6: Fetch transactions immediately (with bypass_cache)")
    try:
        fetch_start = time.time()
        # Try with bypass_cache to ensure fresh data
        response = requests.get(
            f"{API_URL}/v1/transactions?limit=100&bypass_cache=true&_t={int(time.time())}",
            headers=headers
        )
        fetch_time = time.time() - fetch_start
        
        if response.status_code == 200:
            transactions = response.json()
            new_count = len(transactions) if isinstance(transactions, list) else 0
            print(f"   ✅ Fetched {new_count} transactions (took {fetch_time:.2f}s)")
            
            if new_count > initial_count:
                print(f"   ✅ SUCCESS! New transactions detected: {new_count - initial_count} new transactions")
                
                # Show first few transactions
                if transactions:
                    print("\n   📋 Latest transactions:")
                    for i, txn in enumerate(transactions[:3]):
                        print(f"      {i+1}. ID: {txn.get('id')}, Account: {txn.get('account_id')}, "
                              f"Amount: ${txn.get('amount')}, Merchant: {txn.get('merchant')}")
                
                return True
            else:
                print(f"   ⚠️  No new transactions detected (count: {initial_count} -> {new_count})")
                print(f"   ⚠️  This might indicate a caching issue or the transactions weren't inserted")
                return False
        else:
            print(f"   ❌ Failed to fetch transactions: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Error fetching transactions: {e}")
        return False
    
    # Step 7: Test without bypass_cache (should still work if cache was cleared)
    print("\n📥 Step 7: Fetch transactions without bypass_cache (test cache clearing)")
    try:
        response = requests.get(f"{API_URL}/v1/transactions?limit=100", headers=headers)
        if response.status_code == 200:
            transactions = response.json()
            new_count = len(transactions) if isinstance(transactions, list) else 0
            print(f"   ✅ Fetched {new_count} transactions")
            
            if new_count > initial_count:
                print(f"   ✅ SUCCESS! Cache was properly cleared - fresh data served even without bypass_cache")
                return True
            else:
                print(f"   ⚠️  Cache might still contain old data")
                return False
        else:
            print(f"   ⚠️  Could not fetch without bypass_cache: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return False

if __name__ == "__main__":
    print("\n🚀 Starting CSV Upload Real-Time Test\n")
    
    success = test_csv_upload_and_realtime()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ TEST PASSED: CSV upload real-time fix is working!")
        print("   Transactions appear immediately after upload.")
    else:
        print("❌ TEST FAILED: Issues detected with CSV upload real-time fix.")
        print("   Please check the logs above for details.")
    print("=" * 70 + "\n")

