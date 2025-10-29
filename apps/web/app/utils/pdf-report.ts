/**
 * PDF Report Generator
 * 
 * Generates PDF reports from fraud detection data
 * Uses browser's print functionality to generate PDFs
 */

export interface ReportData {
  title: string
  dateRange: { from: string; to: string }
  summary: {
    totalAlerts: number
    highRisk: number
    mediumRisk: number
    lowRisk: number
    totalAmount: number
    blockedAmount: number
  }
  alerts: Array<{
    id: number
    account_id: number
    rule_code: string
    severity: string
    created_at: string
    amount?: number
    status?: string
  }>
  chartData?: any[]
}

export function generateReportHTML(data: ReportData): string {
  const currentDate = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })

  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>${data.title}</title>
  <style>
    @page {
      size: A4;
      margin: 20mm;
    }
    
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      line-height: 1.6;
      color: #333;
      background: white;
    }
    
    .report-container {
      max-width: 100%;
      padding: 20px;
    }
    
    .header {
      border-bottom: 3px solid #3b82f6;
      padding-bottom: 20px;
      margin-bottom: 30px;
    }
    
    .header h1 {
      color: #1e40af;
      font-size: 28px;
      margin-bottom: 10px;
    }
    
    .header .meta {
      color: #64748b;
      font-size: 14px;
    }
    
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 20px;
      margin-bottom: 30px;
    }
    
    .summary-card {
      border: 2px solid #e2e8f0;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
    }
    
    .summary-card.high-risk {
      border-color: #ef4444;
      background: #fee2e2;
    }
    
    .summary-card.medium-risk {
      border-color: #f59e0b;
      background: #fef3c7;
    }
    
    .summary-card.low-risk {
      border-color: #10b981;
      background: #d1fae5;
    }
    
    .summary-card h3 {
      font-size: 14px;
      color: #64748b;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    
    .summary-card .value {
      font-size: 32px;
      font-weight: bold;
      color: #1e293b;
    }
    
    .section {
      margin-bottom: 30px;
    }
    
    .section-title {
      font-size: 20px;
      color: #1e40af;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 2px solid #e2e8f0;
    }
    
    .alerts-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 15px;
    }
    
    .alerts-table thead {
      background: #f1f5f9;
    }
    
    .alerts-table th {
      padding: 12px;
      text-align: left;
      font-weight: 600;
      color: #475569;
      border-bottom: 2px solid #cbd5e1;
      font-size: 12px;
      text-transform: uppercase;
    }
    
    .alerts-table td {
      padding: 10px 12px;
      border-bottom: 1px solid #e2e8f0;
      font-size: 13px;
    }
    
    .alerts-table tr:hover {
      background: #f8fafc;
    }
    
    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
    }
    
    .badge.high {
      background: #fee2e2;
      color: #991b1b;
    }
    
    .badge.medium {
      background: #fef3c7;
      color: #92400e;
    }
    
    .badge.low {
      background: #d1fae5;
      color: #065f46;
    }
    
    .footer {
      margin-top: 50px;
      padding-top: 20px;
      border-top: 2px solid #e2e8f0;
      text-align: center;
      color: #64748b;
      font-size: 12px;
    }
    
    @media print {
      .no-print {
        display: none !important;
      }
      
      .page-break {
        page-break-after: always;
      }
    }
  </style>
</head>
<body>
  <div class="report-container">
    <div class="header">
      <h1>🛡️ ${data.title}</h1>
      <div class="meta">
        <strong>Report Generated:</strong> ${currentDate}<br>
        <strong>Period:</strong> ${data.dateRange.from} to ${data.dateRange.to}
      </div>
    </div>
    
    <div class="section">
      <h2 class="section-title">Executive Summary</h2>
      <div class="summary-grid">
        <div class="summary-card">
          <h3>Total Alerts</h3>
          <div class="value">${data.summary.totalAlerts}</div>
        </div>
        <div class="summary-card high-risk">
          <h3>High Risk</h3>
          <div class="value">${data.summary.highRisk}</div>
        </div>
        <div class="summary-card medium-risk">
          <h3>Medium Risk</h3>
          <div class="value">${data.summary.mediumRisk}</div>
        </div>
        <div class="summary-card low-risk">
          <h3>Low Risk</h3>
          <div class="value">${data.summary.lowRisk}</div>
        </div>
        <div class="summary-card">
          <h3>Total Amount</h3>
          <div class="value">$${data.summary.totalAmount.toLocaleString()}</div>
        </div>
        <div class="summary-card">
          <h3>Blocked Amount</h3>
          <div class="value">$${data.summary.blockedAmount.toLocaleString()}</div>
        </div>
      </div>
    </div>
    
    <div class="section">
      <h2 class="section-title">Fraud Alerts Details</h2>
      <table class="alerts-table">
        <thead>
          <tr>
            <th>Alert ID</th>
            <th>Account</th>
            <th>Rule</th>
            <th>Severity</th>
            <th>Date</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody>
          ${data.alerts.map(alert => `
            <tr>
              <td>#${alert.id}</td>
              <td>${alert.account_id}</td>
              <td>${alert.rule_code}</td>
              <td><span class="badge ${alert.severity.toLowerCase()}">${alert.severity}</span></td>
              <td>${new Date(alert.created_at).toLocaleDateString()}</td>
              <td>${alert.amount ? '$' + alert.amount.toLocaleString() : '-'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
    
    <div class="footer">
      <p>
        <strong>FraudGuard</strong> - AI-Powered Fraud Detection System<br>
        Confidential Report | Internal Use Only
      </p>
    </div>
  </div>
</body>
</html>
  `
}

export function downloadPDFReport(data: ReportData) {
  const html = generateReportHTML(data)
  
  // Create a new window for printing
  const printWindow = window.open('', '_blank')
  if (!printWindow) {
    alert('Please allow popups to generate PDF reports')
    return
  }
  
  printWindow.document.write(html)
  printWindow.document.close()
  
  // Wait for content to load, then print
  setTimeout(() => {
    printWindow.print()
    
    // Close window after printing (user will see print dialog)
    setTimeout(() => {
      printWindow.close()
    }, 500)
  }, 500)
}

export function generateCSVReport(data: ReportData): string {
  const headers = ['Alert ID', 'Account', 'Rule', 'Severity', 'Date', 'Amount', 'Status']
  const rows = data.alerts.map(alert => [
    alert.id,
    alert.account_id,
    alert.rule_code,
    alert.severity,
    new Date(alert.created_at).toISOString(),
    alert.amount || '',
    alert.status || ''
  ])
  
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n')
  
  return csvContent
}

export function downloadCSVReport(data: ReportData, filename: string = 'fraud_report.csv') {
  const csv = generateCSVReport(data)
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  
  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'
  
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

