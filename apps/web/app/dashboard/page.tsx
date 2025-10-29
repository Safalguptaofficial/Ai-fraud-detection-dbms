import { Suspense } from 'react'

// Server-side data fetching
async function getAccounts() {
  try {
    const res = await fetch('http://fraud-dbms_api_1:8000/v1/accounts', {
      cache: 'no-store'
    })
    return res.json()
  } catch (error) {
    console.error('Error fetching accounts:', error)
    return []
  }
}

async function getAlerts() {
  try {
    const res = await fetch('http://fraud-dbms_api_1:8000/v1/alerts?status=open', {
      cache: 'no-store'
    })
    return res.json()
  } catch (error) {
    console.error('Error fetching alerts:', error)
    return []
  }
}

export default async function DashboardPage() {
  const [accounts, alerts] = await Promise.all([
    getAccounts(),
    getAlerts()
  ])

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Fraud Detection Dashboard</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Active Alerts</h3>
            <p className="text-3xl font-bold text-red-600 mt-2">{alerts.length}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Total Accounts</h3>
            <p className="text-3xl font-bold text-blue-600 mt-2">{accounts.length}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">Frozen Accounts</h3>
            <p className="text-3xl font-bold text-orange-600 mt-2">
              {accounts.filter((a: any) => a.status === 'FROZEN').length}
            </p>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Recent Fraud Alerts</h2>
          </div>
          <div className="p-6">
            {alerts && alerts.length > 0 ? (
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Alert ID</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Account</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rule</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Severity</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {alerts.slice(0, 10).map((alert: any) => (
                    <tr key={alert.id}>
                      <td className="px-4 py-4 text-sm text-gray-900">{alert.id}</td>
                      <td className="px-4 py-4 text-sm text-gray-900">{alert.account_id}</td>
                      <td className="px-4 py-4 text-sm text-gray-900">{alert.rule_code}</td>
                      <td className="px-4 py-4 text-sm">
                        <span className={`px-2 py-1 text-xs rounded-full ${
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
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-gray-500">No alerts found</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}