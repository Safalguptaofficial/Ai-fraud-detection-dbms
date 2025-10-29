'use client'

import { NetworkGraph } from '../components/NetworkGraph'

export default function NetworkGraphPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Fraud Network Analysis
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Visualize connections between accounts, transactions, and merchants to identify fraud rings
          </p>
        </div>
        
        <div style={{ height: '700px' }}>
          <NetworkGraph />
        </div>
      </div>
    </div>
  )
}

