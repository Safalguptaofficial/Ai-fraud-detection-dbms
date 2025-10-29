// Demo data for GitHub Pages static deployment

export const demoAlerts = [
  {
    id: 1,
    account_id: 1001,
    rule_code: 'MIDNIGHT_5K',
    severity: 'HIGH',
    status: 'OPEN',
    message: 'Large transaction detected at midnight',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    amount: 8500,
    merchant: 'ATM-WITHDRAWAL'
  },
  {
    id: 2,
    account_id: 1002,
    rule_code: 'GEO_JUMP',
    severity: 'HIGH',
    status: 'INVESTIGATING',
    message: 'Geographic anomaly detected - 1200km in 1.5 hours',
    created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    amount: 450,
    merchant: 'HOTEL-PARIS'
  },
  {
    id: 3,
    account_id: 1003,
    rule_code: 'VELOCITY_SPIKE',
    severity: 'MEDIUM',
    status: 'OPEN',
    message: '7 transactions in 8 minutes',
    created_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    amount: 2100,
    merchant: 'ONLINE-RETAIL'
  },
  {
    id: 4,
    account_id: 1004,
    rule_code: 'MIDNIGHT_5K',
    severity: 'HIGH',
    status: 'RESOLVED',
    message: 'Large overnight transaction',
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    amount: 12000,
    merchant: 'LUXURY-GOODS'
  },
  {
    id: 5,
    account_id: 1005,
    rule_code: 'VELOCITY_SPIKE',
    severity: 'LOW',
    status: 'OPEN',
    message: 'Multiple small transactions',
    created_at: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    amount: 350,
    merchant: 'COFFEE-SHOP'
  }
]

export const demoAccounts = [
  {
    id: 1001,
    account_id: 'ACC-1001',
    customer_id: 'CUST-501',
    account_type: 'CHECKING',
    status: 'FROZEN',
    balance: 45678.90,
    created_at: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString()
  },
  {
    id: 1002,
    account_id: 'ACC-1002',
    customer_id: 'CUST-502',
    account_type: 'SAVINGS',
    status: 'ACTIVE',
    balance: 123456.78,
    created_at: new Date(Date.now() - 200 * 24 * 60 * 60 * 1000).toISOString()
  },
  {
    id: 1003,
    account_id: 'ACC-1003',
    customer_id: 'CUST-503',
    account_type: 'CHECKING',
    status: 'ACTIVE',
    balance: 8765.43,
    created_at: new Date(Date.now() - 150 * 24 * 60 * 60 * 1000).toISOString()
  },
  {
    id: 1004,
    account_id: 'ACC-1004',
    customer_id: 'CUST-504',
    account_type: 'CHECKING',
    status: 'ACTIVE',
    balance: 34567.89,
    created_at: new Date(Date.now() - 500 * 24 * 60 * 60 * 1000).toISOString()
  },
  {
    id: 1005,
    account_id: 'ACC-1005',
    customer_id: 'CUST-505',
    account_type: 'SAVINGS',
    status: 'FROZEN',
    balance: 98765.43,
    created_at: new Date(Date.now() - 300 * 24 * 60 * 60 * 1000).toISOString()
  }
]

export const demoTransactions = [
  {
    id: 1,
    account_id: 1001,
    amount: 8500,
    merchant: 'ATM-WITHDRAWAL',
    location: 'New York, NY',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    risk_score: 85
  },
  {
    id: 2,
    account_id: 1002,
    amount: 450,
    merchant: 'HOTEL-PARIS',
    location: 'Paris, FR',
    created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    risk_score: 78
  },
  {
    id: 3,
    account_id: 1003,
    amount: 2100,
    merchant: 'ONLINE-RETAIL',
    location: 'Los Angeles, CA',
    created_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    risk_score: 65
  },
  {
    id: 4,
    account_id: 1001,
    amount: 125.50,
    merchant: 'GROCERY-STORE',
    location: 'New York, NY',
    created_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
    risk_score: 15
  },
  {
    id: 5,
    account_id: 1004,
    amount: 12000,
    merchant: 'LUXURY-GOODS',
    location: 'London, UK',
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    risk_score: 92
  }
]

export const demoCases = [
  {
    id: 1,
    alert_id: 1,
    status: 'OPEN',
    assigned_to: 'analyst@bank.com',
    priority: 'HIGH',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    notes: [
      {
        content: 'Large ATM withdrawal at unusual hour. Customer contacted.',
        created_at: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
        author: 'analyst@bank.com'
      }
    ]
  },
  {
    id: 2,
    alert_id: 2,
    status: 'INVESTIGATING',
    assigned_to: 'senior@bank.com',
    priority: 'HIGH',
    created_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    notes: [
      {
        content: 'Potential account takeover. Reviewing recent login history.',
        created_at: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
        author: 'senior@bank.com'
      },
      {
        content: 'Customer confirmed travel. Legitimate transaction.',
        created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        author: 'senior@bank.com'
      }
    ]
  }
]

export const demoAnalytics = {
  anomalies: [
    { event_type: 'time_of_day', account_id: 1001, z_score: 3.2, created_at: new Date().toISOString() },
    { event_type: 'velocity', account_id: 1003, z_score: 2.8, created_at: new Date().toISOString() },
    { event_type: 'geo_jump', account_id: 1002, z_score: 4.5, created_at: new Date().toISOString() }
  ],
  geoJumps: [
    { account_id: 1002, from_location: 'New York', to_location: 'Paris', distance_km: 5837, time_diff_hours: 1.5 }
  ],
  velocityAnomalies: [
    { account_id: 1003, transaction_count: 7, time_window_minutes: 8, avg_amount: 300 }
  ]
}

export const demoStats = {
  totalAlerts: 847,
  activeAlerts: 234,
  resolvedToday: 45,
  highSeverity: 89,
  frozenAccounts: 23,
  activeAccounts: 1547
}

export const demoFraudMap = [
  { id: 1, lat: 40.7128, lng: -74.0060, severity: 'HIGH', amount: 8500, location: 'New York, NY' },
  { id: 2, lat: 48.8566, lng: 2.3522, severity: 'HIGH', amount: 12000, location: 'Paris, FR' },
  { id: 3, lat: 34.0522, lng: -118.2437, severity: 'MEDIUM', amount: 2100, location: 'Los Angeles, CA' },
  { id: 4, lat: 51.5074, lng: -0.1278, severity: 'HIGH', amount: 15000, location: 'London, UK' },
  { id: 5, lat: 35.6762, lng: 139.6503, severity: 'LOW', amount: 350, location: 'Tokyo, JP' },
  { id: 6, lat: -33.8688, lng: 151.2093, severity: 'MEDIUM', amount: 4500, location: 'Sydney, AU' }
]

export const demoNetworkGraph = {
  nodes: [
    { id: 'account1', label: 'Account 1001', type: 'account', color: '#3b82f6' },
    { id: 'account2', label: 'Account 1002', type: 'account', color: '#3b82f6' },
    { id: 'merchantA', label: 'Merchant A', type: 'merchant', color: '#ef4444' },
    { id: 'merchantB', label: 'Merchant B', type: 'merchant', color: '#ef4444' },
    { id: 'ip1', label: 'IP: 192.168.1.1', type: 'ip', color: '#22c55e' },
    { id: 'deviceX', label: 'Device X', type: 'device', color: '#f97316' },
    { id: 'transaction1', label: 'Txn 1 ($100)', type: 'transaction', color: '#a855f7' },
    { id: 'transaction2', label: 'Txn 2 ($120)', type: 'transaction', color: '#a855f7' },
    { id: 'transaction3', label: 'Txn 3 ($5000)', type: 'transaction', color: '#a855f7' },
    { id: 'transaction4', label: 'Txn 4 ($150)', type: 'transaction', color: '#a855f7' },
  ],
  links: [
    { source: 'account1', target: 'transaction1', label: 'initiates' },
    { source: 'transaction1', target: 'merchantA', label: 'to' },
    { source: 'transaction1', target: 'ip1', label: 'from' },
    { source: 'account1', target: 'deviceX', label: 'uses' },
    { source: 'account2', target: 'transaction2', label: 'initiates' },
    { source: 'transaction2', target: 'merchantA', label: 'to' },
    { source: 'transaction2', target: 'ip1', label: 'from' },
    { source: 'account2', target: 'deviceX', label: 'uses' },
    { source: 'account1', target: 'transaction3', label: 'initiates' },
    { source: 'transaction3', target: 'merchantB', label: 'to' },
    { source: 'transaction3', target: 'ip1', label: 'from' },
    { source: 'account2', target: 'transaction4', label: 'initiates' },
    { source: 'transaction4', target: 'merchantB', label: 'to' },
  ],
}

export const demoUsers = [
  { id: 1, username: 'admin', email: 'admin@example.com', role: 'ADMIN', is_active: true, permissions: ['*:*'] },
  { id: 2, username: 'analyst', email: 'analyst@example.com', role: 'ANALYST', is_active: true, permissions: ['alerts:read', 'cases:read', 'cases:write'] },
  { id: 3, username: 'viewer', email: 'viewer@example.com', role: 'VIEWER', is_active: true, permissions: ['alerts:read', 'cases:read'] },
]

export const demoInvestigations = [
  {
    id: 1,
    title: 'Suspected Account Takeover - ACC-1001',
    status: 'ACTIVE',
    priority: 'HIGH',
    assigned_to: 'analyst@bank.com',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    timeline: [
      { timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), event: 'Investigation opened', user: 'analyst@bank.com' },
      { timestamp: new Date(Date.now() - 1.5 * 60 * 60 * 1000).toISOString(), event: 'Customer contacted', user: 'analyst@bank.com' },
      { timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(), event: 'Account frozen', user: 'analyst@bank.com' }
    ],
    evidence: [
      { type: 'transaction', id: 1, description: 'Suspicious ATM withdrawal' },
      { type: 'log', description: 'Login from unusual IP address' }
    ]
  },
  {
    id: 2,
    title: 'Geographic Anomaly - ACC-1002',
    status: 'RESOLVED',
    priority: 'MEDIUM',
    assigned_to: 'senior@bank.com',
    created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    timeline: [
      { timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), event: 'Investigation opened', user: 'senior@bank.com' },
      { timestamp: new Date(Date.now() - 20 * 60 * 60 * 1000).toISOString(), event: 'Travel confirmed with customer', user: 'senior@bank.com' },
      { timestamp: new Date(Date.now() - 18 * 60 * 60 * 1000).toISOString(), event: 'Case closed - legitimate', user: 'senior@bank.com' }
    ],
    evidence: [
      { type: 'transaction', id: 2, description: 'Transaction in Paris after NYC' }
    ]
  }
]

export const demoMLPredictions = {
  is_fraud: true,
  risk_score: 87,
  explanation: 'High risk score (87%). Behavioral anomaly detected by ML model (score: 72). Triggered rules: Large transaction amount., Transaction at high-risk merchant.',
  ml_anomaly_score: 72,
  rule_score: 40,
  feature_importance: {
    amount: 0.28,
    transaction_count_24h: 0.35,
    avg_transaction_amount_7d: 0.18,
    time_since_last_txn_min: 0.19
  }
}

export const demoChartData = {
  fraudTrends: [
    { date: '2025-01-22', confirmed: 12, false_positive: 3 },
    { date: '2025-01-23', confirmed: 15, false_positive: 5 },
    { date: '2025-01-24', confirmed: 8, false_positive: 2 },
    { date: '2025-01-25', confirmed: 18, false_positive: 4 },
    { date: '2025-01-26', confirmed: 22, false_positive: 6 },
    { date: '2025-01-27', confirmed: 19, false_positive: 3 },
    { date: '2025-01-28', confirmed: 14, false_positive: 4 }
  ],
  riskDistribution: [
    { name: 'Low (0-30)', value: 342, fill: '#22c55e' },
    { name: 'Medium (31-70)', value: 156, fill: '#f59e0b' },
    { name: 'High (71-100)', value: 89, fill: '#ef4444' }
  ],
  topMerchants: [
    { merchant: 'ATM Withdrawals', fraud_count: 45 },
    { merchant: 'Online Retail', fraud_count: 32 },
    { merchant: 'Foreign Hotels', fraud_count: 28 },
    { merchant: 'Luxury Goods', fraud_count: 23 },
    { merchant: 'Crypto Exchanges', fraud_count: 19 }
  ],
  heatmapData: [
    { hour: 0, day: 'Mon', count: 12 },
    { hour: 1, day: 'Mon', count: 18 },
    { hour: 2, day: 'Mon', count: 22 },
    { hour: 0, day: 'Tue', count: 8 },
    { hour: 1, day: 'Tue', count: 15 },
    { hour: 2, day: 'Tue', count: 19 },
    // ... more data
  ]
}

