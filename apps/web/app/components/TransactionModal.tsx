'use client'

import { X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { getAuthHeaders } from '../utils/auth'
import { toast } from 'sonner'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Transaction {
  id: number
  account_id: number
  amount: number
  currency: string
  merchant: string
  mcc: string
  channel: string
  city?: string
  country?: string
  lat?: number
  lon?: number
  txn_time: string
  status: string
  risk_score?: number
}

interface TransactionModalProps {
  transaction: Transaction | null
  onClose: () => void
}

export function TransactionModal({ transaction, onClose }: TransactionModalProps) {
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (transaction) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [transaction])

  const handleFlagAsFraud = async () => {
    if (!transaction) return
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/v1/alerts/flag-transaction`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          txn_id: transaction.id,
          account_id: transaction.account_id,
          reason: 'Manually flagged by user'
        })
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to flag transaction' }))
        throw new Error(error.detail || 'Failed to flag transaction')
      }

      const result = await response.json()
      toast.success('Transaction flagged as fraud', {
        description: `Alert ${result.alert_id} created`
      })
      onClose()
      // Refresh page to show new alert
      window.location.reload()
    } catch (error: any) {
      console.error('Flag as fraud error:', error)
      toast.error('Failed to flag transaction', {
        description: error.message || 'Please try again'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleMarkAsSafe = async () => {
    if (!transaction) return
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/v1/alerts/mark-safe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          txn_id: transaction.id,
          account_id: transaction.account_id,
          reason: 'Manually marked as safe by user'
        })
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to mark transaction as safe' }))
        throw new Error(error.detail || 'Failed to mark transaction as safe')
      }

      const result = await response.json()
      toast.success('Transaction marked as safe', {
        description: `${result.updated_alerts} alert(s) dismissed`
      })
      onClose()
      // Refresh page to update alerts
      window.location.reload()
    } catch (error: any) {
      console.error('Mark as safe error:', error)
      toast.error('Failed to mark transaction as safe', {
        description: error.message || 'Please try again'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCreateCase = async () => {
    if (!transaction) return
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/v1/cases`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          accountId: transaction.account_id,
          txnIds: [transaction.id],
          notes: `Case created from transaction ${transaction.id}: ${transaction.merchant} - ${transaction.currency} ${transaction.amount}`,
          tags: ['manual-review', 'transaction-investigation']
        })
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to create case' }))
        throw new Error(error.detail || 'Failed to create case')
      }

      const result = await response.json()
      toast.success('Case created successfully', {
        description: `Case ID: ${result.caseId}`
      })
      onClose()
      // Navigate to cases page
      window.location.href = `/cases`
    } catch (error: any) {
      console.error('Create case error:', error)
      toast.error('Failed to create case', {
        description: error.message || 'Please try again'
      })
    } finally {
      setLoading(false)
    }
  }

  if (!transaction) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-6 border-b border-gray-200 flex justify-between items-center sticky top-0 bg-white">
          <h2 className="text-2xl font-bold text-gray-900">Transaction Details</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-6 h-6 text-gray-600" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Transaction ID and Status */}
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-gray-500">Transaction ID</p>
              <p className="text-lg font-mono font-semibold text-gray-900">{transaction.id}</p>
            </div>
            <span className={`px-3 py-1 text-sm rounded-full font-medium ${
              transaction.status === 'APPROVED' ? 'bg-green-100 text-green-800' :
              transaction.status === 'DECLINED' ? 'bg-red-100 text-red-800' :
              'bg-yellow-100 text-yellow-800'
            }`}>
              {transaction.status}
            </span>
          </div>

          {/* Amount */}
          <div className="bg-gradient-to-r from-blue-50 to-blue-100 p-4 rounded-lg">
            <p className="text-sm text-gray-600">Amount</p>
            <p className="text-3xl font-bold text-blue-900">
              {transaction.currency} ${transaction.amount.toLocaleString()}
            </p>
          </div>

          {/* Risk Score */}
          {transaction.risk_score !== undefined && (
            <div>
              <p className="text-sm text-gray-600 mb-2">Risk Score</p>
              <div className="flex items-center gap-3">
                <div className="flex-1 bg-gray-200 rounded-full h-3">
                  <div 
                    className={`h-3 rounded-full transition-all ${
                      transaction.risk_score > 75 ? 'bg-red-500' :
                      transaction.risk_score > 50 ? 'bg-orange-500' :
                      transaction.risk_score > 25 ? 'bg-yellow-500' :
                      'bg-green-500'
                    }`}
                    style={{ width: `${transaction.risk_score}%` }}
                  />
                </div>
                <span className="text-lg font-semibold">{transaction.risk_score}%</span>
              </div>
            </div>
          )}

          {/* Details Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">Account ID</p>
              <p className="text-base font-medium text-gray-900">{transaction.account_id}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Merchant</p>
              <p className="text-base font-medium text-gray-900">{transaction.merchant}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">MCC Code</p>
              <p className="text-base font-medium text-gray-900">{transaction.mcc}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Channel</p>
              <p className="text-base font-medium text-gray-900">{transaction.channel}</p>
            </div>
            {transaction.city && (
              <div>
                <p className="text-sm text-gray-500">Location</p>
                <p className="text-base font-medium text-gray-900">{transaction.city}, {transaction.country}</p>
              </div>
            )}
            {transaction.lat && transaction.lon && (
              <div>
                <p className="text-sm text-gray-500">Coordinates</p>
                <p className="text-base font-medium text-gray-900">{transaction.lat.toFixed(4)}, {transaction.lon.toFixed(4)}</p>
              </div>
            )}
            <div className="col-span-2">
              <p className="text-sm text-gray-500">Transaction Time</p>
              <p className="text-base font-medium text-gray-900">{new Date(transaction.txn_time).toLocaleString()}</p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button 
              onClick={handleFlagAsFraud}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Processing...' : 'Flag as Fraud'}
            </button>
            <button 
              onClick={handleMarkAsSafe}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Processing...' : 'Mark as Safe'}
            </button>
            <button 
              onClick={handleCreateCase}
              disabled={loading}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating...' : 'Create Case'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

