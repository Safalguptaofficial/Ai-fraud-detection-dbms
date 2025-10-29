'use client'

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface TopMerchantsChartProps {
  data: Array<{
    merchant: string
    fraudCount: number
    totalAmount: number
  }>
}

export function TopMerchantsChart({ data }: TopMerchantsChartProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">🏪 Top Merchants with Fraud</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis type="number" stroke="#6b7280" />
          <YAxis dataKey="merchant" type="category" width={100} stroke="#6b7280" />
          <Tooltip 
            contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
            formatter={(value: any, name: string) => {
              if (name === 'totalAmount') return `$${value.toLocaleString()}`
              return value
            }}
          />
          <Bar dataKey="fraudCount" fill="#ef4444" name="Fraud Count" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

