'use client'

import { useState, useEffect } from 'react'
import { useAuth, getAuthHeaders } from '../utils/auth'
import { BulkActions } from '../components/BulkActions'
import { AlertFilters, FilterState } from '../components/AlertFilters'
import { exportAlertsToCSV } from '../utils/export'
import { downloadPDFReport, downloadCSVReport, ReportData } from '../utils/pdf-report'
import { FileDown, FileText } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Account {
  id: number
  account_id: string
  status: string
  balance?: number
}

interface Alert {
  id: number
  account_id: number
  rule_code: string
  severity: string
  created_at: string
  reason?: string
}

export default function DashboardPage() {
  const { user, loading: authLoading, logout } = useAuth()
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [filteredAlerts, setFilteredAlerts] = useState<Alert[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    severity: 'all',
    dateRange: 'all',
    ruleCode: 'all'
  })

  const fetchData = async () => {
    try {
      const headers = getAuthHeaders()
      const [alertsRes, accountsRes] = await Promise.all([
        fetch(`${API_URL}/v1/alerts?status=open`, { headers }).catch(() => null),
        fetch(`${API_URL}/v1/accounts`, { headers }).catch(() => null)
      ])

      if (alertsRes?.ok) {
        const alertsData = await alertsRes.json()
        setAlerts(alertsData)
      } else {
        // Use mock data when API is not available
        console.log('📊 Using mock data (API not available)')
        setAlerts([
          {
            id: 1,
            account_id: 101,
            rule_code: 'VELOCITY_CHECK',
            severity: 'HIGH',
            created_at: new Date().toISOString(),
            reason: '10 transactions in 5 minutes'
          },
          {
            id: 2,
            account_id: 102,
            rule_code: 'LOCATION_ANOMALY',
            severity: 'MEDIUM',
            created_at: new Date().toISOString(),
            reason: 'Transaction from unusual location'
          },
          {
            id: 3,
            account_id: 103,
            rule_code: 'LARGE_AMOUNT',
            severity: 'HIGH',
            created_at: new Date().toISOString(),
            reason: 'Transaction exceeds $10,000 threshold'
          }
        ])
      }

      if (accountsRes?.ok) {
        const accountsData = await accountsRes.json()
        setAccounts(accountsData)
      } else {
        // Use mock data
        setAccounts([
          { id: 1, account_id: 'ACC001', status: 'ACTIVE', balance: 5000 },
          { id: 2, account_id: 'ACC002', status: 'ACTIVE', balance: 12000 },
          { id: 3, account_id: 'ACC003', status: 'FROZEN', balance: 8500 },
          { id: 4, account_id: 'ACC004', status: 'ACTIVE', balance: 3200 },
          { id: 5, account_id: 'ACC005', status: 'FROZEN', balance: 15000 }
        ])
      }

      setLastUpdate(new Date())
      setLoading(false)
    } catch (error) {
      console.error('Error fetching data:', error)
      console.log('📊 Using mock data due to error')
      // Set mock data on error
      setAlerts([
        {
          id: 1,
          account_id: 101,
          rule_code: 'DEMO_ALERT',
          severity: 'HIGH',
          created_at: new Date().toISOString(),
          reason: 'Demo alert - API not connected'
        }
      ])
      setAccounts([
        { id: 1, account_id: 'DEMO001', status: 'ACTIVE', balance: 5000 }
      ])
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    
    // Poll every 5 seconds for real-time updates
    const interval = setInterval(fetchData, 5000)
    
    return () => clearInterval(interval)
  }, [])

  // Apply filters
  useEffect(() => {
    let filtered = [...alerts]

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      filtered = filtered.filter(alert => 
        alert.account_id.toString().includes(searchLower) ||
        alert.rule_code.toLowerCase().includes(searchLower) ||
        alert.reason?.toLowerCase().includes(searchLower)
      )
    }

    // Severity filter
    if (filters.severity !== 'all') {
      filtered = filtered.filter(alert => alert.severity === filters.severity)
    }

    // Date range filter
    if (filters.dateRange !== 'all') {
      const now = new Date()
      const filterDate = new Date()
      
      if (filters.dateRange === 'today') {
        filterDate.setHours(0, 0, 0, 0)
      } else if (filters.dateRange === 'week') {
        filterDate.setDate(now.getDate() - 7)
      } else if (filters.dateRange === 'month') {
        filterDate.setMonth(now.getMonth() - 1)
      }

      filtered = filtered.filter(alert => new Date(alert.created_at) >= filterDate)
    }

    // Rule code filter
    if (filters.ruleCode !== 'all') {
      filtered = filtered.filter(alert => alert.rule_code === filters.ruleCode)
    }

    setFilteredAlerts(filtered)
  }, [alerts, filters])

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(filteredAlerts.map(a => a.id))
    } else {
      setSelectedIds([])
    }
  }

  const handleSelectOne = (id: number, checked: boolean) => {
    if (checked) {
      setSelectedIds(prev => [...prev, id])
    } else {
      setSelectedIds(prev => prev.filter(i => i !== id))
    }
  }

  const handleBulkAction = (action: string, value?: string) => {
    console.log(`Bulk action: ${action}`, { selectedIds, value })
    
    if (action === 'export') {
      const selectedAlerts = alerts.filter(a => selectedIds.includes(a.id))
      exportAlertsToCSV(selectedAlerts)
    } else if (action === 'approve') {
      // Update alerts status
      setAlerts(prev => prev.map(a => 
        selectedIds.includes(a.id) ? { ...a, status: 'APPROVED' } : a
      ))
    } else if (action === 'reject') {
      setAlerts(prev => prev.map(a => 
        selectedIds.includes(a.id) ? { ...a, status: 'REJECTED' } : a
      ))
    } else if (action === 'delete') {
      setAlerts(prev => prev.filter(a => !selectedIds.includes(a.id)))
    }
    
    setSelectedIds([])
  }

  const handleExportPDF = () => {
    const reportData: ReportData = {
      title: 'Fraud Detection Report',
      dateRange: {
        from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toLocaleDateString(),
        to: new Date().toLocaleDateString()
      },
      summary: {
        totalAlerts: alerts.length,
        highRisk: alerts.filter(a => a.severity === 'HIGH').length,
        mediumRisk: alerts.filter(a => a.severity === 'MEDIUM').length,
        lowRisk: alerts.filter(a => a.severity === 'LOW').length,
        totalAmount: 125000,
        blockedAmount: 87500
      },
      alerts: filteredAlerts.slice(0, 20).map(a => ({
        ...a,
        amount: Math.floor(Math.random() * 10000)
      }))
    }
    downloadPDFReport(reportData)
  }

  const handleExportCSV = () => {
    const reportData: ReportData = {
      title: 'Fraud Detection Report',
      dateRange: {
        from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toLocaleDateString(),
        to: new Date().toLocaleDateString()
      },
      summary: {
        totalAlerts: alerts.length,
        highRisk: alerts.filter(a => a.severity === 'HIGH').length,
        mediumRisk: alerts.filter(a => a.severity === 'MEDIUM').length,
        lowRisk: alerts.filter(a => a.severity === 'LOW').length,
        totalAmount: 125000,
        blockedAmount: 87500
      },
      alerts: filteredAlerts.map(a => ({
        ...a,
        amount: Math.floor(Math.random() * 10000),
        status: 'OPEN'
      }))
    }
    downloadCSVReport(reportData, `fraud_report_${new Date().toISOString().split('T')[0]}.csv`)
  }

  const frozenCount = accounts.filter(a => a.status === 'FROZEN').length
  const activeCount = accounts.filter(a => a.status === 'ACTIVE').length

  if (authLoading || (loading && accounts.length === 0)) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8 transition-colors">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Fraud Detection Dashboard</h1>
            {user && (
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">Welcome, {user.name} ({user.role})</p>
            )}
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Last updated: {lastUpdate.toLocaleTimeString()}
              <span className="ml-2 inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            </div>
            {user && (
              <button
                onClick={logout}
                className="px-4 py-2 bg-red-600 dark:bg-red-700 text-white rounded-lg hover:bg-red-700 dark:hover:bg-red-800 transition-colors text-sm"
              >
                Logout
              </button>
            )}
          </div>
        </div>

        {/* Alert Filters */}
        <AlertFilters onFilterChange={setFilters} />
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow hover:shadow-lg transition-all border border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Active Alerts</h3>
            <p className="text-3xl font-bold text-red-600 dark:text-red-400 mt-2">{alerts.length}</p>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">High priority fraud cases</p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow hover:shadow-lg transition-all border border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Accounts</h3>
            <p className="text-3xl font-bold text-blue-600 dark:text-blue-400 mt-2">{accounts.length}</p>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">All monitored accounts</p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow hover:shadow-lg transition-all border border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Frozen Accounts</h3>
            <p className="text-3xl font-bold text-orange-600 dark:text-orange-400 mt-2">{frozenCount}</p>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Suspicious activity detected</p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow hover:shadow-lg transition-all border border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Active Accounts</h3>
            <p className="text-3xl font-bold text-green-600 dark:text-green-400 mt-2">{activeCount}</p>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Normal operations</p>
          </div>
        </div>

        {/* Severity Distribution Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow mb-8 p-6 border border-gray-200 dark:border-gray-700 transition-colors">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Alert Severity Distribution</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600 dark:text-red-400 mb-1">
                {alerts.filter(a => a.severity === 'HIGH').length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">High</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400 mb-1">
                {alerts.filter(a => a.severity === 'MEDIUM').length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Medium</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600 dark:text-green-400 mb-1">
                {alerts.filter(a => a.severity === 'LOW').length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Low</div>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 transition-colors">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
            <div className="flex items-center gap-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Recent Fraud Alerts</h2>
              {selectedIds.length > 0 && (
                <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full text-sm font-medium">
                  {selectedIds.length} selected
                </span>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleExportPDF}
                className="px-4 py-2 bg-purple-600 dark:bg-purple-700 text-white rounded-lg hover:bg-purple-700 dark:hover:bg-purple-800 transition-colors text-sm flex items-center gap-2"
              >
                <FileText className="w-4 h-4" />
                PDF
              </button>
              <button
                onClick={handleExportCSV}
                className="px-4 py-2 bg-green-600 dark:bg-green-700 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-800 transition-colors text-sm flex items-center gap-2"
              >
                <FileDown className="w-4 h-4" />
                CSV
              </button>
              <button
                onClick={fetchData}
                className="px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 transition-colors text-sm"
              >
                Refresh
              </button>
            </div>
          </div>
          <div className="p-6">
            {filteredAlerts && filteredAlerts.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead>
                    <tr>
                      <th className="px-4 py-3 text-left">
                        <input
                          type="checkbox"
                          checked={selectedIds.length === filteredAlerts.length && filteredAlerts.length > 0}
                          onChange={(e) => handleSelectAll(e.target.checked)}
                          className="w-4 h-4 text-blue-600 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500 dark:focus:ring-blue-400 cursor-pointer"
                        />
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Alert ID</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Account</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Rule</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Severity</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Time</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {filteredAlerts.slice(0, 10).map((alert) => (
                      <tr key={alert.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                        <td className="px-4 py-4">
                          <input
                            type="checkbox"
                            checked={selectedIds.includes(alert.id)}
                            onChange={(e) => handleSelectOne(alert.id, e.target.checked)}
                            className="w-4 h-4 text-blue-600 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500 dark:focus:ring-blue-400 cursor-pointer"
                          />
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-900 dark:text-gray-100 font-mono">{alert.id}</td>
                        <td className="px-4 py-4 text-sm text-gray-900 dark:text-gray-100">Account {alert.account_id}</td>
                        <td className="px-4 py-4 text-sm text-gray-900 dark:text-gray-100">
                          <span className="font-medium">{alert.rule_code}</span>
                          {alert.reason && (
                            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{alert.reason}</div>
                          )}
                        </td>
                        <td className="px-4 py-4 text-sm">
                          <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                            alert.severity === 'HIGH' ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300' :
                            alert.severity === 'MEDIUM' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300' :
                            'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                          }`}>
                            {alert.severity}
                          </span>
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-500 dark:text-gray-400">
                          {new Date(alert.created_at).toLocaleString()}
                        </td>
                        <td className="px-4 py-4 text-sm">
                          <button className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium">
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-500 dark:text-gray-400 text-lg">
                  {alerts.length > 0 ? 'No alerts match your filters' : 'No alerts found'}
                </p>
                <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
                  {alerts.length > 0 ? 'Try adjusting your filters' : 'All clear! No fraud detected.'}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bulk Actions Toolbar */}
      <BulkActions 
        selectedIds={selectedIds}
        onClearSelection={() => setSelectedIds([])}
        onBulkUpdate={handleBulkAction}
      />
    </div>
  )
}