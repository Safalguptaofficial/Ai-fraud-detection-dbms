'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'

interface FraudTrendsChartProps {
  data: Array<{
    date: string
    count: number
    highSeverity: number
    mediumSeverity: number
    lowSeverity: number
  }>
}

export function FraudTrendsChart({ data }: FraudTrendsChartProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">📈 Fraud Detection Trends</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="date" 
            tickFormatter={(value) => format(new Date(value), 'MMM dd')}
            stroke="#6b7280"
          />
          <YAxis stroke="#6b7280" />
          <Tooltip 
            labelFormatter={(value) => format(new Date(value), 'PPP')}
            contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
          />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="highSeverity" 
            stroke="#ef4444" 
            strokeWidth={2}
            name="High Severity"
            dot={{ fill: '#ef4444' }}
          />
          <Line 
            type="monotone" 
            dataKey="mediumSeverity" 
            stroke="#f59e0b" 
            strokeWidth={2}
            name="Medium Severity"
            dot={{ fill: '#f59e0b' }}
          />
          <Line 
            type="monotone" 
            dataKey="lowSeverity" 
            stroke="#10b981" 
            strokeWidth={2}
            name="Low Severity"
            dot={{ fill: '#10b981' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

