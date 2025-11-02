# Dashboard Real-Time Data Issues Analysis

## Issues Found:

### 1. **Periodic Refresh Doesn't Bypass Cache**
   - Line 234: `fetchData(false)` in setInterval
   - This means every 30 seconds, it fetches WITHOUT bypassing cache
   - Result: Gets same cached data repeatedly

### 2. **Cache Key Doesn't Include csv_only**
   - Backend cache key might not differentiate csv_only=true vs false
   - Same cached data served regardless of csv_only parameter

### 3. **No Cache Buster on Periodic Refresh**
   - Cache buster `_t=${Date.now()}` only added when `shouldBypassCache` is true
   - Periodic refreshes don't have cache buster, so browser cache might serve old data

### 4. **Backend Redis Cache TTL**
   - Cache might persist for 5 minutes (CACHE_TTL = 300)
   - Even with csv_only filter, if cache exists, it returns cached result

## Solutions Needed:
1. Always bypass cache on periodic refresh OR use cache buster
2. Include csv_only in cache key
3. Reduce cache TTL or force refresh more aggressively
4. Add timestamp to every request for real-time updates
