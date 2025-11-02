# Dashboard Real-Time Data Issues - Analysis & Fixes

## 🔍 Issues Found

### 1. **Periodic Refresh Not Using Cache Buster** ❌
**Problem:**
- Cache buster `&_t=${Date.now()}` was only added when `shouldBypassCache` was true
- Periodic refresh (every 30s) called `fetchData(false)`, which didn't add cache buster
- Result: Browser/backend served stale cached data repeatedly

**Location:** `apps/web/app/dashboard/page.tsx:102`

**Fix:**
- Always add cache buster timestamp to URL
- Ensures every request is unique and bypasses browser cache
- Backend still respects `bypass_cache` flag for Redis cache

---

### 2. **Backend Caching CSV-Only Requests** ❌
**Problem:**
- When `csv_only=true`, backend was still checking/using Redis cache
- Cache didn't differentiate between `csv_only=true` vs `csv_only=false`
- Result: Stale CSV-filtered data was served from cache

**Location:** `services/api/routers/transactions.py:110`

**Fix:**
- Skip Redis cache when `csv_only=true` (always fetch fresh)
- Skip cache when `bypass_cache=true` (manual refresh)
- Only cache standard transaction requests (without filters)

---

### 3. **No Cache Busting on Periodic Refresh** ❌
**Problem:**
- Periodic refresh every 30 seconds didn't include cache buster
- Browser might cache responses even with different URLs
- Backend Redis cache was serving stale data

**Location:** `apps/web/app/dashboard/page.tsx:234-236`

**Fix:**
- Cache buster now added to ALL requests (not just forced refreshes)
- Every request gets unique timestamp: `&_t=${Date.now()}`
- Backend bypasses cache for `csv_only=true` requests

---

### 4. **Cache Key Logic Issue** ❌
**Problem:**
- Cache key generation included `csv_only` parameter
- But cache was still checked even when `csv_only=true`
- Created inconsistent caching behavior

**Location:** `services/api/routers/transactions.py:111`

**Fix:**
- Explicit `should_cache` flag
- Only cache when: `not bypass_cache AND not csv_only`
- Clear logging of cache decisions

---

## ✅ Fixes Applied

### Frontend (`apps/web/app/dashboard/page.tsx`)

1. **Always Include Cache Buster**
   ```typescript
   // Before: const cacheBuster = shouldBypassCache ? `&_t=${Date.now()}` : ''
   // After:  const cacheBuster = `&_t=${Date.now()}` // Always add
   ```

2. **Better Logging**
   - Shows when periodic refresh is triggered
   - Logs cache buster status
   - Indicates real-time update attempts

### Backend (`services/api/routers/transactions.py`)

1. **Smart Caching Logic**
   ```python
   should_cache = not bypass_cache and not csv_only
   ```
   - Don't cache CSV-only requests (always fresh)
   - Don't cache when bypass flag is set
   - Only cache standard requests

2. **Improved Cache Write**
   - Only writes to cache when `should_cache = True`
   - Skips cache write for real-time requests
   - Better logging for debugging

3. **Debug Logging**
   - Logs cache decisions
   - Shows when cache is bypassed
   - Helps diagnose caching issues

---

## 🎯 Expected Behavior Now

### Real-Time Updates ✅
1. **Initial Load**: Fetches fresh data with cache buster
2. **Periodic Refresh**: Every 30 seconds, fetches with new cache buster
3. **Manual Refresh**: Bypasses both browser and Redis cache
4. **After CSV Upload**: Immediately fetches fresh data

### Cache Behavior ✅
- **CSV-only requests**: Never cached (always fresh)
- **Standard requests**: Cached for 5 minutes (performance)
- **Manual refresh**: Always bypasses cache
- **Browser cache**: Bypassed by timestamp in URL

---

## 🧪 Testing

### Test 1: Verify Cache Buster
1. Open browser DevTools → Network tab
2. Watch dashboard refresh automatically
3. **Expected**: Each request has different `_t=` timestamp

### Test 2: Verify Fresh Data
1. Upload new CSV file
2. Watch dashboard
3. **Expected**: New transactions appear within 30 seconds

### Test 3: Verify Periodic Refresh
1. Check browser console
2. **Expected**: See "⏰ Periodic refresh triggered (every 30s)" every 30 seconds

### Test 4: Backend Logs
1. Check API server logs
2. **Expected**: See "Bypassing cache: bypass_cache=False, csv_only=True"

---

## 📊 Performance Impact

- **Cache Hits**: Reduced for CSV-only requests (intentional - ensures freshness)
- **Database Load**: Slightly increased (but acceptable for real-time updates)
- **Response Time**: Still fast (database queries are optimized)
- **User Experience**: ✅ Always sees latest data

---

## 🔧 Configuration

- **Refresh Interval**: 30 seconds (line 240 in dashboard)
- **Cache TTL**: 5 minutes (for standard requests only)
- **Cache Buster**: Timestamp on every request
- **CSV Filter**: Always bypasses cache

---

## 📝 Summary

The dashboard now:
- ✅ Shows real-time data (updates every 30 seconds)
- ✅ Always fetches fresh CSV transactions
- ✅ Bypasses cache when needed
- ✅ Provides clear logging for debugging
- ✅ Works correctly after CSV uploads

**Before:** Static cached data, same transactions shown repeatedly  
**After:** Real-time updates, fresh data on every refresh

