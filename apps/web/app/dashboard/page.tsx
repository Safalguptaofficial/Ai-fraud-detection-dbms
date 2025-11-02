'use client'

import { useState, useEffect } from 'react'
import { useAuth, getAuthHeaders } from '../utils/auth'
import { FraudTrendsChart } from '../components/FraudTrendsChart'
import { TransactionHeatmap } from '../components/TransactionHeatmap'
import { RiskDistribution } from '../components/RiskDistribution'
import { TopMerchantsChart } from '../components/TopMerchantsChart'
import { TransactionModal } from '../components/TransactionModal'
import { exportAlertsToCSV } from '../utils/export'
import { toast } from 'sonner'
import { Download, RefreshCw, Bell, TrendingUp, Shield, AlertTriangle } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Alert {
  id: number
  account_id: number
  rule_code: string
  severity: string
  created_at: string
  reason?: string
  status?: string
}

interface Transaction {
  id: number
  account_id: number
  amount: number
  currency: string
  merchant: string
  mcc: string
  channel: string
  city?: string
  country?: string
  txn_time: string
  status: string
  risk_score?: number
}

export default function EnhancedDashboard() {
  const { user, loading: authLoading, logout, isAuthenticated } = useAuth()
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [redirecting, setRedirecting] = useState(false)

  const fetchData = async (forceRefresh = false) => {
    // Don't fetch if already redirecting
    if (redirecting) return
    
    try {
      // Check if we need to force refresh (from upload page or URL param) BEFORE setting refreshing state
      const urlParams = new URLSearchParams(window.location.search)
      const urlRefresh = urlParams.get('refresh') === 'true'
      const dataUploaded = sessionStorage.getItem('data_uploaded') === 'true'
      
      // Force refresh if coming from upload, URL param, or manual refresh
      // Note: Check urlRefresh and dataUploaded BEFORE setting refreshing state
      const shouldBypassCache = forceRefresh || urlRefresh || dataUploaded
      
      console.log('🔍 Fetching dashboard data', { 
        forceRefresh, 
        urlRefresh, 
        dataUploaded, 
        shouldBypassCache,
        refreshing 
      })
      
      setRefreshing(true)
      const headers = getAuthHeaders()
      console.log('🔍 Fetching dashboard data with headers:', Object.keys(headers))
      
      // Clear the data_uploaded flag after using it (but keep the bypass state)
      if (dataUploaded) {
        sessionStorage.removeItem('data_uploaded')
        sessionStorage.removeItem('upload_timestamp')
        console.log('📥 Cleared data_uploaded flag - forcing cache bypass')
      }
      
      // Remove refresh param from URL without page reload (but after we've read it)
      if (urlRefresh) {
        const newUrl = window.location.pathname + window.location.search.replace(/[?&]refresh=true/, '').replace(/[?&]_t=\d+/, '')
        window.history.replaceState({}, '', newUrl || '/dashboard')
        console.log('🔄 Removed refresh param from URL')
      }
      
      // Add timeout wrapper for fetch requests
      const fetchWithTimeout = (url: string, options: RequestInit, timeout = 5000): Promise<Response> => {
        return Promise.race([
          fetch(url, options),
          new Promise<Response>((_, reject) =>
            setTimeout(() => reject(new Error('Request timeout')), timeout)
          )
        ])
      }
      
      // Always add cache buster for real-time updates (prevent stale cached data)
      // Use timestamp to ensure fresh data on every request
      const cacheBuster = `&_t=${Date.now()}`
      // Bypass cache when force refresh is requested (manual refresh or after upload)
      const bypassCache = shouldBypassCache ? '&bypass_cache=true' : ''
      
      // Fetch ALL real transactions (no csv_only filter to show all uploaded data)
      // Increased limit to 1000 to show all uploaded transactions
      const transactionsUrl = `${API_URL}/v1/transactions?limit=1000&bypass_cache=true${cacheBuster}`
      
      if (shouldBypassCache) {
        console.log('🔄 Bypassing cache - fetching fresh transactions', { transactionsUrl })
      } else {
        console.log('📥 Fetching all transactions (with cache buster for real-time updates)', { transactionsUrl })
      }
      
      const [alertsRes, transactionsRes] = await Promise.allSettled([
        fetchWithTimeout(`${API_URL}/v1/alerts?status=open`, { headers }).catch(() => null),
        fetchWithTimeout(transactionsUrl, { headers }).catch(() => null)
      ])

      // Handle alerts response
      if (alertsRes.status === 'fulfilled' && alertsRes.value && alertsRes.value.ok) {
        try {
          const alertsData = await alertsRes.value.json()
          setAlerts(Array.isArray(alertsData) ? alertsData : [])
          console.log('✅ Alerts fetched successfully:', alertsData.length || 0)
        } catch (e) {
          console.error('Failed to parse alerts:', e)
          setAlerts([])
        }
      } else if (alertsRes.status === 'fulfilled' && alertsRes.value) {
        const res = alertsRes.value
        if (res.status === 401) {
          const token = localStorage.getItem('auth_token')
          if (!token) {
            console.warn('⚠️ No token found, redirecting to login')
            setRedirecting(true)
            localStorage.removeItem('auth_token')
            localStorage.removeItem('user')
            window.location.href = '/login'
            return
          }
        }
        console.warn('⚠️ Alerts fetch failed or timed out, continuing with empty alerts')
        setAlerts([])
      } else {
        console.warn('⚠️ Alerts request failed or timed out, continuing without alerts')
        setAlerts([])
      }

      // Handle transactions response
      if (transactionsRes.status === 'fulfilled' && transactionsRes.value && transactionsRes.value.ok) {
        try {
          const transactionsData = await transactionsRes.value.json()
          setTransactions(Array.isArray(transactionsData) ? transactionsData : [])
          console.log('✅ Transactions fetched successfully:', transactionsData.length || 0)
          
          // Log first few transaction IDs for debugging
          if (transactionsData.length > 0 && shouldBypassCache) {
            console.log('📊 Latest transaction IDs:', transactionsData.slice(0, 3).map((t: Transaction) => t.id))
          }
        } catch (e) {
          console.error('Failed to parse transactions:', e)
          setTransactions([])
        }
      } else if (transactionsRes.status === 'fulfilled' && transactionsRes.value) {
        const res = transactionsRes.value
        console.error('❌ Transactions fetch failed:', res.status, res.statusText)
        if (res.status === 401) {
          console.warn('⚠️ Authentication issue - may need to login again')
        }
        setTransactions([])
      } else {
        console.warn('⚠️ Transactions request failed or timed out, continuing without transactions')
        setTransactions([])
      }

      setLastUpdate(new Date())
      setLoading(false)
      
      // Show success message if we got any data
      const hasAlerts = alertsRes.status === 'fulfilled' && alertsRes.value && alertsRes.value.ok
      const hasTransactions = transactionsRes.status === 'fulfilled' && transactionsRes.value && transactionsRes.value.ok
      
      if (hasAlerts || hasTransactions) {
        if (shouldBypassCache && hasTransactions) {
          // Show special message when fresh data is loaded after upload
          const txnCount = transactions.length || 0
          toast.success(`Dashboard refreshed! Showing ${txnCount} transactions.`, {
            duration: 4000
          })
        } else {
        toast.success('Dashboard loaded successfully')
        }
      } else if (!redirecting) {
        toast.error('Some data failed to load. Showing available data.')
      }
    } catch (error: any) {
      console.error('Error fetching data:', error)
      // Don't redirect on network errors - might be temporary
      const errorMsg = error.message || 'Network error'
      console.error('Full error:', error)
      
      // Only show error if we haven't redirected already
      if (!redirecting) {
        toast.error(`Failed to fetch data: ${errorMsg}`)
      }
      setLoading(false)
    } finally {
      setRefreshing(false)
    }
  }

  useEffect(() => {
    // Wait for auth check to complete before fetching
    if (authLoading) {
      console.log('⏳ Waiting for auth check...')
      return
    }
    
    // Check if we need to force refresh on initial load (from upload page)
    const dataUploaded = sessionStorage.getItem('data_uploaded') === 'true'
    const urlParams = new URLSearchParams(window.location.search)
    const urlRefresh = urlParams.get('refresh') === 'true'
    const shouldForceRefresh = dataUploaded || urlRefresh
    
    // Small delay to ensure localStorage is fully updated after login
    const timer = setTimeout(() => {
      console.log('🚀 Starting to fetch dashboard data...', { shouldForceRefresh, dataUploaded, urlRefresh })
      fetchData(shouldForceRefresh)
    }, 100)
    
    // Set up interval for periodic refresh with cache buster for real-time updates
    // Using cache buster ensures we get fresh data even if backend has cached response
    const interval = setInterval(() => {
      if (!redirecting && !authLoading) {
        console.log('⏰ Periodic refresh triggered (every 30s)')
        fetchData(false) // false = don't force bypass, but cache buster in URL ensures fresh data
      }
    }, 30000) // Refresh every 30 seconds
    
    return () => {
      clearTimeout(timer)
      clearInterval(interval)
    }
  }, [authLoading, redirecting])

  // Generate chart data
  const generateTrendsData = () => {
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const date = new Date()
      date.setDate(date.getDate() - (6 - i))
      return date.toISOString().split('T')[0]
    })

    return last7Days.map(date => {
      const dayAlerts = alerts.filter(a => a.created_at.startsWith(date))
      return {
        date,
        count: dayAlerts.length,
        highSeverity: dayAlerts.filter(a => a.severity === 'HIGH').length,
        mediumSeverity: dayAlerts.filter(a => a.severity === 'MEDIUM').length,
        lowSeverity: dayAlerts.filter(a => a.severity === 'LOW').length,
      }
    })
  }

  const generateHeatmapData = () => {
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    const data = []
    
    // Group transactions by day of week and hour
    const txnByTime: Record<string, number> = {}
    
    transactions.forEach(txn => {
      const date = new Date(txn.txn_time)
      const day = days[date.getDay()]
      const hour = date.getHours()
      const key = `${day}-${hour}`
      txnByTime[key] = (txnByTime[key] || 0) + 1
    })
    
    for (const day of days) {
      for (let hour = 0; hour < 24; hour++) {
        const key = `${day}-${hour}`
        data.push({ day, hour, count: txnByTime[key] || 0 })
      }
    }
    
    return data
  }

  const generateRiskData = () => {
    // Calculate risk distribution from transactions
    const ranges = [
      { range: '0-20', count: 0 },
      { range: '21-40', count: 0 },
      { range: '41-60', count: 0 },
      { range: '61-80', count: 0 },
      { range: '81-100', count: 0 },
    ]
    
    transactions.forEach(txn => {
      const score = txn.risk_score || 0
      if (score <= 20) ranges[0].count++
      else if (score <= 40) ranges[1].count++
      else if (score <= 60) ranges[2].count++
      else if (score <= 80) ranges[3].count++
      else ranges[4].count++
    })
    
    return ranges
  }

  const generateMerchantData = () => {
    // Group transactions by merchant and calculate fraud alerts
    const merchantMap: Record<string, { fraudCount: number, totalAmount: number }> = {}
    
    transactions.forEach(txn => {
      if (!merchantMap[txn.merchant]) {
        merchantMap[txn.merchant] = { fraudCount: 0, totalAmount: 0 }
      }
      merchantMap[txn.merchant].totalAmount += txn.amount
    })
    
    // Count fraud alerts per merchant (match by account_id since alerts might not have txn_id)
    alerts.forEach(alert => {
      const txn = transactions.find(t => t.account_id === alert.account_id)
      if (txn && merchantMap[txn.merchant]) {
        merchantMap[txn.merchant].fraudCount++
      }
    })
    
    // Sort by fraud count and take top 5
    return Object.entries(merchantMap)
      .map(([merchant, data]) => ({
        merchant,
        fraudCount: data.fraudCount,
        totalAmount: data.totalAmount
      }))
      .sort((a, b) => b.fraudCount - a.fraudCount)
      .slice(0, 5)
  }

  const handleExportAlerts = () => {
    exportAlertsToCSV(alerts)
    toast.success('Alerts exported to CSV')
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-8 flex items-center justify-center transition-colors">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 dark:border-blue-400 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300 text-lg">Loading enhanced dashboard...</p>
        </div>
      </div>
    )
  }

  const highSeverityCount = alerts.filter(a => a.severity === 'HIGH').length
  const mediumSeverityCount = alerts.filter(a => a.severity === 'MEDIUM').length
  
  // Calculate real detection rate: (alerts / transactions) * 100
  const detectionRate = transactions.length > 0 
    ? ((alerts.length / transactions.length) * 100).toFixed(1)
    : '0.0'

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-8 transition-colors">
      <div className="max-w-[1800px] mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
              <Shield className="w-10 h-10 text-blue-600 dark:text-blue-400" />
              Fraud Detection Command Center
            </h1>
            {user && (
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-2">Welcome back, {user.name} • {user.role}</p>
            )}
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-600 dark:text-gray-300 bg-white dark:bg-gray-800 px-4 py-2 rounded-lg shadow border border-gray-200 dark:border-gray-700 flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              Last updated: {lastUpdate.toLocaleTimeString()}
            </div>
            <button
              onClick={() => fetchData(true)}
              disabled={refreshing}
              className="px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 transition-all flex items-center gap-2 shadow-lg disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={handleExportAlerts}
              className="px-4 py-2 bg-green-600 dark:bg-green-700 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-800 transition-all flex items-center gap-2 shadow-lg"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
            {user && (
              <button
                onClick={logout}
                className="px-4 py-2 bg-red-600 dark:bg-red-700 text-white rounded-lg hover:bg-red-700 dark:hover:bg-red-800 transition-all shadow-lg"
              >
                Logout
              </button>
            )}
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <div className="bg-gradient-to-br from-red-500 to-red-600 p-6 rounded-xl shadow-lg text-white">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium opacity-90">Critical Alerts</h3>
              <Bell className="w-5 h-5 opacity-75" />
            </div>
            <p className="text-4xl font-bold">{highSeverityCount}</p>
            <p className="text-xs opacity-75 mt-1">Requires immediate action</p>
          </div>

          <div className="bg-gradient-to-br from-orange-500 to-orange-600 p-6 rounded-xl shadow-lg text-white">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium opacity-90">Medium Risk</h3>
              <AlertTriangle className="w-5 h-5 opacity-75" />
            </div>
            <p className="text-4xl font-bold">{mediumSeverityCount}</p>
            <p className="text-xs opacity-75 mt-1">Under investigation</p>
          </div>

          <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl shadow-lg text-white">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium opacity-90">Total Alerts</h3>
              <TrendingUp className="w-5 h-5 opacity-75" />
            </div>
            <p className="text-4xl font-bold">{alerts.length}</p>
            <p className="text-xs opacity-75 mt-1">All active cases</p>
          </div>

          <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 rounded-xl shadow-lg text-white">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium opacity-90">Transactions</h3>
              <Shield className="w-5 h-5 opacity-75" />
            </div>
            <p className="text-4xl font-bold">{transactions.length}</p>
            <p className="text-xs opacity-75 mt-1">Last 24 hours</p>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-xl shadow-lg text-white">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium opacity-90">Detection Rate</h3>
              <TrendingUp className="w-5 h-5 opacity-75" />
            </div>
            <p className="text-4xl font-bold">{detectionRate}%</p>
            <p className="text-xs opacity-75 mt-1">Alerts per transaction</p>
          </div>
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <FraudTrendsChart data={generateTrendsData()} />
          <RiskDistribution data={generateRiskData()} />
        </div>

        {/* Charts Row 2 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <TransactionHeatmap data={generateHeatmapData()} />
          <TopMerchantsChart data={generateMerchantData()} />
        </div>

        {/* Recent Transactions Table */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 transition-colors mb-6">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">💳 Recent Transactions</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Your uploaded transaction data</p>
          </div>
          <div className="p-6">
            {transactions && transactions.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead>
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Account</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Merchant</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Location</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Time</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Risk Score</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {transactions.map((txn) => (
                      <tr 
                        key={txn.id} 
                        className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                        onClick={() => setSelectedTransaction(txn)}
                      >
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900 dark:text-gray-100">{txn.id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">#{txn.account_id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900 dark:text-gray-100">
                          {txn.currency || 'USD'} {txn.amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                          <span className="font-medium">{txn.merchant}</span>
                          {txn.mcc && (
                            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">MCC: {txn.mcc}</div>
                          )}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                          {txn.city && txn.country ? (
                            <span>{txn.city}, {txn.country}</span>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {new Date(txn.txn_time).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {txn.risk_score !== undefined ? (
                            <span className={`px-3 py-1 text-xs rounded-full font-semibold ${
                              txn.risk_score >= 70 ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300' :
                              txn.risk_score >= 40 ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300' :
                              'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                            }`}>
                              {txn.risk_score}
                            </span>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button 
                            onClick={(e) => {
                              e.stopPropagation()
                              setSelectedTransaction(txn)
                            }}
                            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium transition-colors"
                          >
                            View →
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {transactions.length > 100 && (
                  <div className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
                    Showing first 100 of {transactions.length} transactions
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-16">
                <Shield className="w-16 h-16 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400 text-xl font-medium">No Transactions Yet</p>
                <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
                  Upload your transaction data to get started
                </p>
                <button
                  onClick={() => window.location.href = '/data/upload'}
                  className="mt-4 px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 transition-all"
                >
                  Upload Data →
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Recent Alerts Table */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 transition-colors">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">🚨 Recent Fraud Alerts</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Fraud detection alerts from your transactions</p>
          </div>
          <div className="p-6">
            {alerts && alerts.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead>
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Alert ID</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Account</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Rule</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Severity</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Time</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {alerts.slice(0, 15).map((alert) => (
                      <tr key={alert.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900 dark:text-gray-100">{alert.id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">#{alert.account_id}</td>
                        <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                          <span className="font-medium">{alert.rule_code}</span>
                          {alert.reason && (
                            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{alert.reason}</div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`px-3 py-1 text-xs rounded-full font-semibold ${
                            alert.severity === 'HIGH' ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300' :
                            alert.severity === 'MEDIUM' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300' :
                            'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                          }`}>
                            {alert.severity}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {new Date(alert.created_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button 
                            onClick={() => window.location.href = '/investigation'}
                            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium transition-colors"
                          >
                            Investigate →
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-16">
                <Shield className="w-16 h-16 text-green-500 dark:text-green-400 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400 text-xl font-medium">All Clear!</p>
                <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">No fraud alerts detected</p>
                <p className="text-gray-400 dark:text-gray-500 text-xs mt-1">
                  Upload transactions and test them with the ML model to generate alerts
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Transaction Modal */}
      <TransactionModal transaction={selectedTransaction} onClose={() => setSelectedTransaction(null)} />
    </div>
  )
}
