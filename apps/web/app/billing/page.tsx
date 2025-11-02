'use client'

import { useState, useEffect } from 'react'
import { useAuth, getAuthHeaders } from '../utils/auth'
import { CreditCard, DollarSign, TrendingUp, Download, Check, AlertCircle } from 'lucide-react'
import { toast } from 'sonner'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Subscription {
  plan: string
  status: string
  current_period_end: string
  stripe_subscription_id: string
}

interface Usage {
  usage: {
    transactions: {
      limit: number
      used: number
      remaining: number
      exceeded: boolean
    }
  }
  overage_charges: number
}

const PLANS = {
  STARTER: {
    name: 'Starter',
    price: 199,
    transactions: '50K',
    users: 5,
    features: ['Email support', 'Basic ML models', 'API access']
  },
  PROFESSIONAL: {
    name: 'Professional',
    price: 799,
    transactions: '500K',
    users: 25,
    features: ['Priority support', 'SSO', 'Custom ML models', 'Advanced API']
  },
  ENTERPRISE: {
    name: 'Enterprise',
    price: 2999,
    transactions: 'Unlimited',
    users: 'Unlimited',
    features: ['24/7 support', 'Dedicated DB', 'Custom features', 'SLA']
  }
}

export default function BillingPage() {
  const { isAuthenticated } = useAuth()
  const [loading, setLoading] = useState(false)
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [usage, setUsage] = useState<Usage | null>(null)
  const [invoices, setInvoices] = useState<any[]>([])

  useEffect(() => {
    if (isAuthenticated) {
      fetchSubscription()
      fetchUsage()
      fetchInvoices()
    }
  }, [isAuthenticated])

  const fetchSubscription = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/billing/subscriptions`, {
        headers: getAuthHeaders()
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        console.error('Failed to fetch subscription:', response.status, errorData)
        if (response.status === 401 || response.status === 403) {
          toast.error('Authentication required. Please log in again.')
        } else if (response.status === 404) {
          // No subscription found - that's okay, user can create one
          setSubscription(null)
          return
        } else {
          toast.error(`Failed to load subscription: ${errorData.detail || 'Unknown error'}`)
        }
        return
      }
      
      const data = await response.json()
      setSubscription(data.subscription)
    } catch (error: any) {
      console.error('Failed to fetch subscription:', error)
      toast.error(`Network error: ${error.message || 'Failed to fetch subscription'}`)
    }
  }

  const fetchUsage = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/billing/usage`, {
        headers: getAuthHeaders()
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        console.error('Failed to fetch usage:', response.status, errorData)
        if (response.status === 401 || response.status === 403) {
          toast.error('Authentication required. Please log in again.')
        } else {
          toast.error(`Failed to load usage: ${errorData.detail || 'Unknown error'}`)
        }
        return
      }
      
      const data = await response.json()
      setUsage(data)
    } catch (error: any) {
      console.error('Failed to fetch usage:', error)
      toast.error(`Network error: ${error.message || 'Failed to fetch usage'}`)
    }
  }

  const fetchInvoices = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/billing/invoices`, {
        headers: getAuthHeaders()
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        console.error('Failed to fetch invoices:', response.status, errorData)
        // Don't show error for invoices if no subscription exists
        if (response.status !== 401 && response.status !== 403) {
          setInvoices([])
          return
        }
        return
      }
      
      const data = await response.json()
      setInvoices(data.invoices || [])
    } catch (error: any) {
      console.error('Failed to fetch invoices:', error)
      // Don't show error toast for invoices - just set empty array
      setInvoices([])
    }
  }

  const upgradePlan = async (plan: string) => {
    if (!confirm(`Upgrade to ${plan} plan?`)) return

    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/v1/billing/subscriptions`, {
        method: subscription ? 'PATCH' : 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          plan: plan,
          new_plan: plan 
        })
      })

      if (!response.ok) throw new Error('Failed to update plan')

      toast.success(`Successfully ${subscription ? 'upgraded' : 'subscribed'} to ${plan}!`)
      fetchSubscription()
      fetchUsage()
    } catch (error: any) {
      toast.error(error.message)
    } finally {
      setLoading(false)
    }
  }

  const cancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription? You will lose access to premium features.')) {
      return
    }

    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/v1/billing/subscriptions`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      })

      if (!response.ok) throw new Error('Failed to cancel subscription')

      toast.success('Subscription cancelled')
      fetchSubscription()
    } catch (error: any) {
      toast.error(error.message)
    } finally {
      setLoading(false)
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p>Please log in to access billing.</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Billing & Subscription
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your subscription and view usage
          </p>
        </div>

        {/* Current Subscription */}
        {subscription ? (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-8">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                  Current Plan: {subscription.plan}
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  ${PLANS[subscription.plan as keyof typeof PLANS]?.price}/month
                </p>
              </div>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                subscription.status === 'ACTIVE' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {subscription.status}
              </div>
            </div>

            {subscription.current_period_end && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Next billing date: {new Date(subscription.current_period_end).toLocaleDateString()}
              </p>
            )}

            <button
              onClick={cancelSubscription}
              disabled={loading}
              className="text-red-600 hover:text-red-700 text-sm font-medium"
            >
              Cancel Subscription
            </button>
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-8">
            <div className="text-center py-8">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                No Active Subscription
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Subscribe to a plan below to get started with FraudGuard
              </p>
            </div>
          </div>
        )}

        {/* Usage Stats */}
        {usage ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-2">
                <TrendingUp className="w-8 h-8 text-blue-600" />
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  This Month
                </span>
              </div>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                {usage.usage.transactions.used.toLocaleString()}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                of {usage.usage.transactions.limit.toLocaleString()} transactions
              </p>
              <div className="mt-4 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full ${
                    usage.usage.transactions.exceeded ? 'bg-red-600' : 'bg-blue-600'
                  }`}
                  style={{
                    width: `${Math.min((usage.usage.transactions.used / usage.usage.transactions.limit) * 100, 100)}%`
                  }}
                />
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-2">
                <DollarSign className="w-8 h-8 text-green-600" />
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Overage
                </span>
              </div>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                ${usage.overage_charges.toFixed(2)}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Additional charges this month
              </p>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-2">
                <AlertCircle className="w-8 h-8 text-orange-600" />
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Remaining
                </span>
              </div>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mb-1">
                {usage.usage.transactions.remaining?.toLocaleString() || 'Unlimited'}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Transactions left
              </p>
            </div>
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-8">
            <div className="text-center py-4">
              <p className="text-gray-600 dark:text-gray-400">
                Usage statistics will be available after you subscribe to a plan.
              </p>
            </div>
          </div>
        )}

        {/* Available Plans */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            Available Plans
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Object.entries(PLANS).map(([key, plan]) => (
              <div
                key={key}
                className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 ${
                  subscription?.plan === key ? 'ring-2 ring-blue-600' : ''
                }`}
              >
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                  {plan.name}
                </h3>
                <div className="mb-4">
                  <span className="text-4xl font-bold text-gray-900 dark:text-white">
                    ${plan.price}
                  </span>
                  <span className="text-gray-600 dark:text-gray-400">/month</span>
                </div>

                <ul className="space-y-3 mb-6">
                  <li className="flex items-start space-x-2">
                    <Check className="w-5 h-5 text-green-600 mt-0.5" />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {plan.transactions} transactions/month
                    </span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <Check className="w-5 h-5 text-green-600 mt-0.5" />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      Up to {plan.users} users
                    </span>
                  </li>
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start space-x-2">
                      <Check className="w-5 h-5 text-green-600 mt-0.5" />
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>

                {subscription?.plan === key ? (
                  <button
                    disabled
                    className="w-full py-2 px-4 bg-gray-300 dark:bg-gray-600 text-gray-600 dark:text-gray-400 font-semibold rounded-lg cursor-not-allowed"
                  >
                    Current Plan
                  </button>
                ) : (
                  <button
                    onClick={() => upgradePlan(key)}
                    disabled={loading}
                    className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg disabled:opacity-50"
                  >
                    {subscription ? 'Upgrade' : 'Subscribe'}
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Invoices */}
        {invoices.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
              Invoice History
            </h2>
            <div className="space-y-3">
              {invoices.map((invoice) => (
                <div
                  key={invoice.id}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      ${(invoice.amount_due / 100).toFixed(2)}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {new Date(invoice.created * 1000).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      invoice.status === 'PAID' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {invoice.status}
                    </span>
                    {invoice.invoice_pdf && (
                      <a
                        href={invoice.invoice_pdf}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center space-x-1 text-blue-600 hover:text-blue-700"
                      >
                        <Download className="w-4 h-4" />
                        <span className="text-sm">PDF</span>
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

