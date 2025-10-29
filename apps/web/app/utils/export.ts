export function exportToCSV(data: any[], filename: string) {
  if (!data || data.length === 0) {
    console.warn('No data to export')
    return
  }

  // Get headers from the first object
  const headers = Object.keys(data[0])
  
  // Create CSV content
  const csvContent = [
    headers.join(','), // Header row
    ...data.map(row => 
      headers.map(header => {
        const value = row[header]
        // Handle values that contain commas or quotes
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`
        }
        return value ?? ''
      }).join(',')
    )
  ].join('\n')

  // Create and download file
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  
  link.setAttribute('href', url)
  link.setAttribute('download', `${filename}_${new Date().toISOString().split('T')[0]}.csv`)
  link.style.visibility = 'hidden'
  
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

export function exportAlertsToCSV(alerts: any[]) {
  const formattedData = alerts.map(alert => ({
    'Alert ID': alert.id,
    'Account ID': alert.account_id,
    'Rule Code': alert.rule_code,
    'Severity': alert.severity,
    'Status': alert.status,
    'Created At': new Date(alert.created_at).toLocaleString(),
    'Reason': alert.reason || 'N/A'
  }))
  
  exportToCSV(formattedData, 'fraud_alerts')
}

export function exportTransactionsToCSV(transactions: any[]) {
  const formattedData = transactions.map(txn => ({
    'Transaction ID': txn.id,
    'Account ID': txn.account_id,
    'Amount': txn.amount,
    'Currency': txn.currency,
    'Merchant': txn.merchant,
    'MCC': txn.mcc,
    'Channel': txn.channel,
    'City': txn.city,
    'Country': txn.country,
    'Status': txn.status,
    'Time': new Date(txn.txn_time).toLocaleString()
  }))
  
  exportToCSV(formattedData, 'transactions')
}

