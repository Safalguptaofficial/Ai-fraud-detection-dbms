'use client'

import { useState, useEffect } from 'react'
import { useAuth, getAuthHeaders } from '../utils/auth'
import { toast } from 'sonner'
import { Search, Plus, Filter, FileText, User, Clock, Tag, ChevronRight } from 'lucide-react'
import Link from 'next/link'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface FraudCase {
  _id?: string
  caseId: string
  accountId: number
  txnIds: number[]
  investigator?: string
  status: string
  tags: string[]
  createdAt: string
  updatedAt: string
  notes: Array<{
    author: string
    content: string
    createdAt: string
  }>
}

export default function CasesPage() {
  const { user } = useAuth()
  const [cases, setCases] = useState<FraudCase[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newCase, setNewCase] = useState({
    accountId: '',
    txnIds: '',
    notes: '',
    tags: ''
  })

  useEffect(() => {
    fetchCases()
  }, [statusFilter])

  const fetchCases = async () => {
    try {
      setLoading(true)
      const headers = getAuthHeaders()
      const url = statusFilter === 'all' 
        ? `${API_URL}/v1/cases`
        : `${API_URL}/v1/cases?status=${statusFilter}`
      
      const res = await fetch(url, { headers })
      
      if (res.ok) {
        const data = await res.json()
        setCases(data || [])
      } else {
        // Handle non-ok responses
        let errorMessage = 'Failed to fetch cases'
        try {
          const errorData = await res.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
        } catch {
          errorMessage = `Server error: ${res.status} ${res.statusText}`
        }
        
        console.error('Error fetching cases:', res.status, errorMessage)
        toast.error('Unable to fetch cases', {
          description: errorMessage
        })
        setCases([]) // Set empty array on error
      }
    } catch (error) {
      console.error('Error fetching cases:', error)
      const errorMessage = error instanceof Error ? error.message : 'Network error or server unavailable'
      toast.error('Unable to fetch cases', {
        description: errorMessage
      })
      setCases([]) // Set empty array on error
    } finally {
      setLoading(false)
    }
  }

  const handleCreateCase = async () => {
    try {
      const headers = {
        ...getAuthHeaders(),
        'Content-Type': 'application/json'
      }

      const res = await fetch(`${API_URL}/v1/cases`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          accountId: parseInt(newCase.accountId),
          txnIds: newCase.txnIds ? newCase.txnIds.split(',').map(id => parseInt(id.trim())) : [],
          notes: newCase.notes,
          tags: newCase.tags ? newCase.tags.split(',').map(tag => tag.trim()) : []
        })
      })

      if (res.ok) {
        const result = await res.json()
        toast.success('Case created successfully', {
          description: `Case ID: ${result.caseId}`
        })
        setShowCreateModal(false)
        setNewCase({ accountId: '', txnIds: '', notes: '', tags: '' })
        fetchCases()
      } else {
        const errorData = await res.json().catch(() => ({}))
        console.error('Failed to create case:', res.status, errorData)
        if (res.status === 500) {
          toast.error('MongoDB connection issue. Please check backend logs.')
        } else {
          toast.error(errorData.detail || 'Failed to create case')
        }
      }
    } catch (error) {
      console.error('Error creating case:', error)
      toast.error('Failed to create case')
    }
  }

  const filteredCases = cases.filter(c => 
    c.caseId.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.accountId.toString().includes(searchQuery)
  )

  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case 'OPEN': return 'bg-blue-100 text-blue-800'
      case 'INVESTIGATING': return 'bg-yellow-100 text-yellow-800'
      case 'RESOLVED': return 'bg-green-100 text-green-800'
      case 'CLOSED': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading cases...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              <FileText className="w-8 h-8 text-blue-600" />
              Case Management
            </h1>
            <p className="text-gray-600 dark:text-gray-300 mt-1">Manage and track fraud investigation cases</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all flex items-center gap-2 shadow-lg"
          >
            <Plus className="w-5 h-5" />
            New Case
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search by case ID or account ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none"
              >
                <option value="all">All Statuses</option>
                <option value="OPEN">Open</option>
                <option value="INVESTIGATING">Investigating</option>
                <option value="RESOLVED">Resolved</option>
                <option value="CLOSED">Closed</option>
              </select>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-blue-600 text-sm font-medium">Open Cases</p>
            <p className="text-2xl font-bold text-blue-900">{cases.filter(c => c.status === 'OPEN').length}</p>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-yellow-600 text-sm font-medium">Investigating</p>
            <p className="text-2xl font-bold text-yellow-900">{cases.filter(c => c.status === 'INVESTIGATING').length}</p>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-green-600 text-sm font-medium">Resolved</p>
            <p className="text-2xl font-bold text-green-900">{cases.filter(c => c.status === 'RESOLVED').length}</p>
          </div>
          <div className="bg-gray-50 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <p className="text-gray-600 dark:text-gray-300 text-sm font-medium">Total Cases</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{cases.length}</p>
          </div>
        </div>

        {/* Cases List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          {filteredCases.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {filteredCases.map((fraudCase) => (
                <Link 
                  key={fraudCase.caseId} 
                  href={`/cases/${fraudCase.caseId}`}
                  className="block p-6 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{fraudCase.caseId}</h3>
                        <span className={`px-3 py-1 text-xs rounded-full font-medium ${getStatusColor(fraudCase.status)}`}>
                          {fraudCase.status}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-6 text-sm text-gray-600">
                        <div className="flex items-center gap-2">
                          <User className="w-4 h-4" />
                          <span>Account #{fraudCase.accountId}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4" />
                          <span>{fraudCase.txnIds.length} transactions</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4" />
                          <span>{new Date(fraudCase.createdAt).toLocaleDateString()}</span>
                        </div>
                        {fraudCase.investigator && (
                          <div className="flex items-center gap-2">
                            <User className="w-4 h-4" />
                            <span>{fraudCase.investigator}</span>
                          </div>
                        )}
                      </div>

                      {fraudCase.tags && fraudCase.tags.length > 0 && (
                        <div className="flex items-center gap-2 mt-3">
                          <Tag className="w-4 h-4 text-gray-400" />
                          <div className="flex gap-2">
                            {fraudCase.tags.map((tag, idx) => (
                              <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-16">
              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No cases found</p>
              <p className="text-gray-400 text-sm mt-2">Create a new case to get started</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Case Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50" onClick={() => setShowCreateModal(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Create New Case</h2>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Account ID *</label>
                <input
                  type="number"
                  value={newCase.accountId}
                  onChange={(e) => setNewCase({...newCase, accountId: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter account ID"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Transaction IDs</label>
                <input
                  type="text"
                  value={newCase.txnIds}
                  onChange={(e) => setNewCase({...newCase, txnIds: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="1, 2, 3 (comma-separated)"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Initial Notes</label>
                <textarea
                  value={newCase.notes}
                  onChange={(e) => setNewCase({...newCase, notes: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={3}
                  placeholder="Describe the fraud case..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
                <input
                  type="text"
                  value={newCase.tags}
                  onChange={(e) => setNewCase({...newCase, tags: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="fraud, high-priority (comma-separated)"
                />
              </div>
            </div>
            <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateCase}
                disabled={!newCase.accountId}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Create Case
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

