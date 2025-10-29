'use client'

import { useState, useEffect } from 'react'
import { useAuth, getAuthHeaders } from '../utils/auth'
import { toast } from 'sonner'
import { Database, RefreshCw, Activity, Eye, Edit, Plus, Trash2, Filter } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface CRUDOperation {
  id: string
  timestamp: Date
  operation: 'CREATE' | 'READ' | 'UPDATE' | 'DELETE'
  table: string
  user: string
  recordId?: string | number
  details: string
  duration?: number
}

export default function CRUDMonitor() {
  const { user } = useAuth()
  const [operations, setOperations] = useState<CRUDOperation[]>([])
  const [filter, setFilter] = useState<string>('all')
  const [tableFilter, setTableFilter] = useState<string>('all')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [stats, setStats] = useState({
    creates: 0,
    reads: 0,
    updates: 0,
    deletes: 0,
    total: 0
  })

  useEffect(() => {
    fetchOperations()
    
    if (autoRefresh) {
      const interval = setInterval(fetchOperations, 3000)
      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  const fetchOperations = async () => {
    // Simulate CRUD operations - in production, this would come from audit logs
    const mockOperations: CRUDOperation[] = [
      {
        id: `${Date.now()}-1`,
        timestamp: new Date(),
        operation: 'CREATE',
        table: 'transactions',
        user: user?.name || 'system',
        recordId: Math.floor(Math.random() * 10000),
        details: 'New transaction created: $' + Math.floor(Math.random() * 1000),
        duration: Math.floor(Math.random() * 50) + 10
      },
      {
        id: `${Date.now()}-2`,
        timestamp: new Date(Date.now() - 1000),
        operation: 'UPDATE',
        table: 'alerts',
        user: 'analyst@bank.com',
        recordId: Math.floor(Math.random() * 100),
        details: 'Alert status changed to INVESTIGATING',
        duration: Math.floor(Math.random() * 30) + 5
      },
      {
        id: `${Date.now()}-3`,
        timestamp: new Date(Date.now() - 2000),
        operation: 'READ',
        table: 'accounts',
        user: user?.name || 'system',
        recordId: Math.floor(Math.random() * 100),
        details: 'Account details retrieved',
        duration: Math.floor(Math.random() * 20) + 2
      }
    ]

    // Merge with existing operations, keeping last 50
    setOperations(prev => [...mockOperations, ...prev].slice(0, 50))

    // Update stats
    const newStats = {
      creates: operations.filter(op => op.operation === 'CREATE').length,
      reads: operations.filter(op => op.operation === 'READ').length,
      updates: operations.filter(op => op.operation === 'UPDATE').length,
      deletes: operations.filter(op => op.operation === 'DELETE').length,
      total: operations.length
    }
    setStats(newStats)
  }

  const getOperationIcon = (operation: string) => {
    switch (operation) {
      case 'CREATE': return <Plus className="w-4 h-4" />
      case 'READ': return <Eye className="w-4 h-4" />
      case 'UPDATE': return <Edit className="w-4 h-4" />
      case 'DELETE': return <Trash2 className="w-4 h-4" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  const getOperationColor = (operation: string) => {
    switch (operation) {
      case 'CREATE': return 'bg-green-100 text-green-800'
      case 'READ': return 'bg-blue-100 text-blue-800'
      case 'UPDATE': return 'bg-yellow-100 text-yellow-800'
      case 'DELETE': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const filteredOperations = operations.filter(op => {
    const matchesOperation = filter === 'all' || op.operation === filter
    const matchesTable = tableFilter === 'all' || op.table === tableFilter
    return matchesOperation && matchesTable
  })

  const tables = ['all', ...Array.from(new Set(operations.map(op => op.table)))]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <Database className="w-8 h-8 text-blue-600" />
              CRUD Operations Monitor
            </h1>
            <p className="text-gray-600 dark:text-gray-300 mt-1">Real-time database operation tracking and auditing</p>
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Auto-refresh</span>
            </label>
            <button
              onClick={fetchOperations}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Plus className="w-5 h-5 text-green-600" />
              <p className="text-green-600 text-sm font-medium">CREATE</p>
            </div>
            <p className="text-2xl font-bold text-green-900">{stats.creates}</p>
          </div>
          
          <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Eye className="w-5 h-5 text-blue-600" />
              <p className="text-blue-600 text-sm font-medium">READ</p>
            </div>
            <p className="text-2xl font-bold text-blue-900">{stats.reads}</p>
          </div>
          
          <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Edit className="w-5 h-5 text-yellow-600" />
              <p className="text-yellow-600 text-sm font-medium">UPDATE</p>
            </div>
            <p className="text-2xl font-bold text-yellow-900">{stats.updates}</p>
          </div>
          
          <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Trash2 className="w-5 h-5 text-red-600" />
              <p className="text-red-600 text-sm font-medium">DELETE</p>
            </div>
            <p className="text-2xl font-bold text-red-900">{stats.deletes}</p>
          </div>
          
          <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-5 h-5 text-purple-600" />
              <p className="text-purple-600 text-sm font-medium">TOTAL</p>
            </div>
            <p className="text-2xl font-bold text-purple-900">{stats.total}</p>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-400" />
              <span className="text-sm font-medium text-gray-700">Filters:</span>
            </div>
            
            <div className="flex gap-2">
              {['all', 'CREATE', 'READ', 'UPDATE', 'DELETE'].map(op => (
                <button
                  key={op}
                  onClick={() => setFilter(op)}
                  className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                    filter === op
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {op === 'all' ? 'All Operations' : op}
                </button>
              ))}
            </div>

            <div className="ml-auto">
              <select
                value={tableFilter}
                onChange={(e) => setTableFilter(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {tables.map(table => (
                  <option key={table} value={table}>
                    {table === 'all' ? 'All Tables' : table}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Operations Timeline */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Operation Log</h2>
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">Live feed of database operations</p>
          </div>
          
          <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
            {filteredOperations.length > 0 ? (
              filteredOperations.map((op) => (
                <div key={op.id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start gap-4">
                    <div className={`p-2 rounded-lg ${getOperationColor(op.operation)}`}>
                      {getOperationIcon(op.operation)}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <span className={`px-2 py-1 text-xs font-semibold rounded ${getOperationColor(op.operation)}`}>
                          {op.operation}
                        </span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">{op.table}</span>
                        {op.recordId && (
                          <span className="text-sm text-gray-500">ID: {op.recordId}</span>
                        )}
                        {op.duration && (
                          <span className="text-xs text-gray-400">{op.duration}ms</span>
                        )}
                      </div>
                      
                      <p className="text-sm text-gray-700">{op.details}</p>
                      
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>User: {op.user}</span>
                        <span>•</span>
                        <span>{op.timestamp.toLocaleTimeString()}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-16">
                <Database className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 text-lg">No operations found</p>
                <p className="text-gray-400 text-sm mt-2">Waiting for database activity...</p>
              </div>
            )}
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Average Query Time</h3>
            <p className="text-3xl font-bold text-blue-600">
              {operations.length > 0
                ? Math.round(operations.reduce((sum, op) => sum + (op.duration || 0), 0) / operations.length)
                : 0}ms
            </p>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Operations/Minute</h3>
            <p className="text-3xl font-bold text-green-600">
              {Math.floor(operations.filter(op => 
                new Date().getTime() - op.timestamp.getTime() < 60000
              ).length)}
            </p>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Most Active Table</h3>
            <p className="text-2xl font-bold text-purple-600">
              {operations.length > 0
                ? (() => {
                    const tableCounts = operations.reduce((acc, op) => {
                      acc[op.table] = (acc[op.table] || 0) + 1
                      return acc
                    }, {} as Record<string, number>)
                    const sorted = Object.entries(tableCounts).sort((a, b) => b[1] - a[1])
                    return sorted[0]?.[0] || 'N/A'
                  })()
                : 'N/A'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

