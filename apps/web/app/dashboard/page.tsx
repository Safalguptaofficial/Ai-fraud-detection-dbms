'use client'

import { useState, useEffect } from 'react'
import { useAuth, getAuthHeaders } from '../utils/auth'

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
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  const fetchData = async () => {
    try {
      const headers = getAuthHeaders()
      const [alertsRes, accountsRes] = await Promise.all([
        fetch(`${API_URL}/v1/alerts?status=open`, { headers }),
        fetch(`${API_URL}/v1/accounts`, { headers })
      ])

      if (alertsRes.ok) {
        const alertsData = await alertsRes.json()
        setAlerts(alertsData)
      }

      if (accountsRes.ok) {
        const accountsData = await accountsRes.json()
        setAccounts(accountsData)
      }

      setLastUpdate(new Date())
      setLoading(false)
    } catch (error) {
      console.error('Error fetching data:', error)
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    
    // Poll every 5 seconds for real-time updates
    const interval = setInterval(fetchData, 5000)
    
    return () => clearInterval(interval)
  }, [])

  const frozenCount = accounts.filter(a => a.status === 'FROZEN').length
  const activeCount = accounts.filter(a => a.status === 'ACTIVE').length

  if (authLoading || (loading && accounts.length === 0)) {
    return (
      <div className="min-h-screen bg-gray-50 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Fraud Detection Dashboard</h1>
            {user && (
              <p className="text-sm text-gray-600 mt-1">Welcome, {user.name} ({user.role})</p>
            )}
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-500">
              Last updated: {lastUpdate.toLocaleTimeString()}
              <span className="ml-2 inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            </div>
            {user && (
              <button
                onClick={logout}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
              >
                Logout
              </button>
            )}
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
            <h3 className="text-sm font-medium text-gray-500">Active Alerts</h3>
            <p className="text-3xl font-bold text-red-600 mt-2">{alerts.length}</p>
            <p className="text-xs text-gray-400 mt-1">High priority fraud cases</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
            <h3 className="text-sm font-medium text-gray-500">Total Accounts</h3>
            <p className="text-3xl font-bold text-blue-600 mt-2">{accounts.length}</p>
            <p className="text-xs text-gray-400 mt-1">All monitored accounts</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
            <h3 className="text-sm font-medium text-gray-500">Frozen Accounts</h3>
            <p className="text-3xl font-bold text-orange-600 mt-2">{frozenCount}</p>
            <p className="text-xs text-gray-400 mt-1">Suspicious activity detected</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition-shadow">
            <h3 className="text-sm font-medium text-gray-500">Active Accounts</h3>
            <p className="text-3xl font-bold text-green-600 mt-2">{activeCount}</p>
            <p className="text-xs text-gray-400 mt-1">Normal operations</p>
          </div>
        </div>

        {/* Severity Distribution Chart */}
        <div className="bg-white rounded-lg shadow mb-8 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Alert Severity Distribution</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600 mb-1">
                {alerts.filter(a => a.severity === 'HIGH').length}
              </div>
              <div className="text-sm text-gray-600">High</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600 mb-1">
                {alerts.filter(a => a.severity === 'MEDIUM').length}
              </div>
              <div className="text-sm text-gray-600">Medium</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600 mb-1">
                {alerts.filter(a => a.severity === 'LOW').length}
              </div>
              <div className="text-sm text-gray-600">Low</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900">Recent Fraud Alerts</h2>
            <button
              onClick={fetchData}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
            >
              Refresh
            </button>
          </div>
          <div className="p-6">
            {alerts && alerts.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead>
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Alert ID</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Account</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rule</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Severity</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {alerts.slice(0, 10).map((alert) => (
                      <tr key={alert.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-4 py-4 text-sm text-gray-900 font-mono">{alert.id}</td>
                        <td className="px-4 py-4 text-sm text-gray-900">Account {alert.account_id}</td>
                        <td className="px-4 py-4 text-sm text-gray-900">
                          <span className="font-medium">{alert.rule_code}</span>
                          {alert.reason && (
                            <div className="text-xs text-gray-500 mt-1">{alert.reason}</div>
                          )}
                        </td>
                        <td className="px-4 py-4 text-sm">
                          <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                            alert.severity === 'HIGH' ? 'bg-red-100 text-red-800' :
                            alert.severity === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {alert.severity}
                          </span>
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-500">
                          {new Date(alert.created_at).toLocaleString()}
                        </td>
                        <td className="px-4 py-4 text-sm">
                          <button className="text-blue-600 hover:text-blue-800 font-medium">
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
                <p className="text-gray-500 text-lg">No alerts found</p>
                <p className="text-gray-400 text-sm mt-2">All clear! No fraud detected.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}