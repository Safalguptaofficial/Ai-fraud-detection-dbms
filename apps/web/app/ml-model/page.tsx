'use client'

import { useState, useEffect, useRef } from 'react'
import { Brain, TrendingUp, AlertTriangle, CheckCircle, Info, RefreshCw, Zap, PlayCircle, PauseCircle, Activity } from 'lucide-react'
import { toast } from 'sonner'
import { getAuthHeaders } from '../utils/auth'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function MLModelPage() {
  const [formData, setFormData] = useState({
    amount: 1000,
    transactions_last_hour: 3,
    historical_avg_amount: 150,
    historical_std_amount: 50,
    minutes_since_last_transaction: 30,
    location_changed: false,
    merchant_risk_score: 0.2,
    device_changed: false,
    ip_reputation_score: 0.8
  })
  
  const [prediction, setPrediction] = useState<any>(null)
  const [explanation, setExplanation] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [batchPredictions, setBatchPredictions] = useState<any[]>([])
  const [batchLoading, setBatchLoading] = useState(false)
  const [sampleTransactions, setSampleTransactions] = useState<any[]>([])
  const [showBatchResults, setShowBatchResults] = useState(false)
  const [realTimeMode, setRealTimeMode] = useState(false)
  const [realTimePredictions, setRealTimePredictions] = useState<any[]>([])
  const [lastFetchedTransactionId, setLastFetchedTransactionId] = useState<number | null>(null)
  
  // Use refs to prevent duplicate calls
  const isPredictingRef = useRef(false)
  const isExplainingRef = useRef(false)

  const handlePredict = async (event?: React.MouseEvent) => {
    if (event) {
      event.preventDefault()
      event.stopPropagation()
      if (event.nativeEvent) {
        event.nativeEvent.stopImmediatePropagation()
      }
    }
    
    console.log('🔵 handlePredict called - ONLY PREDICT')
    console.trace('Stack trace for handlePredict')
    
    // CRITICAL: Check if explain is already running - if so, DO NOT proceed
    if (isExplainingRef.current) {
      console.log('⚠️ EXPLAIN IS ALREADY RUNNING - IGNORING PREDICT CALL')
      return
    }
    
    // Use ref to prevent duplicate calls (more reliable than state)
    if (isPredictingRef.current) {
      console.log('⚠️ ALREADY PREDICTING - IGNORING DUPLICATE CALL')
      return
    }
    
    if (loading) {
      console.log('⚠️ Already loading, ignoring duplicate call')
      return
    }
    
    isPredictingRef.current = true
    setLoading(true)
    setShowBatchResults(false) // Show single prediction view
    // Don't clear explanation - user might want to keep it
    setPrediction(null) // Clear previous prediction
    
    try {
      // Get CURRENT form values - force fresh read
      const currentAmount = Number(formData.amount) || 0
      const currentVelocity = Number(formData.transactions_last_hour) || 1
      const currentTimeSince = Number(formData.minutes_since_last_transaction) || 60
      const currentMerchantRisk = Number(formData.merchant_risk_score) || 0.1
      const currentIpRisk = Number(formData.ip_reputation_score) || 0.5
      
      // Prepare data matching API schema exactly
      const requestData = {
        amount: currentAmount,
        transactions_last_hour: currentVelocity,
        historical_avg_amount: Number(formData.historical_avg_amount) || 100,
        historical_std_amount: Number(formData.historical_std_amount) || 50,
        minutes_since_last_transaction: currentTimeSince,
        location_changed: Boolean(formData.location_changed),
        merchant_risk_score: currentMerchantRisk,
        device_changed: Boolean(formData.device_changed),
        ip_reputation_score: currentIpRisk
      }

      console.log('🚀 Sending prediction request with CURRENT values:')
      console.log('  Amount:', currentAmount)
      console.log('  Velocity:', currentVelocity)
      console.log('  Time Since:', currentTimeSince)
      console.log('  Merchant Risk:', currentMerchantRisk)
      console.log('  IP Risk:', currentIpRisk)
      console.log('  Full Request:', requestData)
      
      // Get auth headers and verify they're present
      const authHeaders = getAuthHeaders()
      const headers = { 'Content-Type': 'application/json', ...authHeaders }
      
      console.log('🚀 Request headers:', Object.keys(headers))
      const apiKey = (headers as any)['X-API-Key']
      const authToken = (headers as any)['Authorization']
      console.log('🚀 Has X-API-Key:', !!apiKey, apiKey ? apiKey.substring(0, 20) + '...' : 'NO')
      console.log('🚀 Has Authorization:', !!authToken, authToken ? 'YES' : 'NO')
      
      const response = await fetch(`${API_URL}/v1/ml/predict`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(requestData)
      })
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('❌ API Error:', response.status, errorText)
        console.error('❌ Request sent:', requestData)
        console.error('❌ API URL:', `${API_URL}/v1/ml/predict`)
        toast.error(`API Error ${response.status}: ${errorText.substring(0, 100)}`)
        setLoading(false)
        
        // Show debug info in console
        console.log('💡 Debug Info:')
        console.log('  - Check if backend API is running on port 8000')
        console.log('  - Check if endpoint /v1/ml/predict is registered')
        console.log('  - Check browser Network tab for actual request')
        return
      }
      
        const data = await response.json()
      console.log('✅ Prediction received:', data)
      console.log('✅ Risk Score:', data.risk_score)
      console.log('✅ Risk Level:', data.risk_level)
        setPrediction(data)
      toast.success(`Prediction: ${data.risk_score?.toFixed(1) || 'N/A'}/100 (${data.risk_level || 'UNKNOWN'})`)
    } catch (error: any) {
      console.error('❌ Error:', error)
      toast.error(`Error: ${error.message || 'Failed to get prediction'}`)
    } finally {
      isPredictingRef.current = false
      setLoading(false)
    }
  }

  const handleExplain = async (event?: React.MouseEvent) => {
    if (event) {
      event.preventDefault()
      event.stopPropagation()
      if (event.nativeEvent) {
        event.nativeEvent.stopImmediatePropagation()
      }
    }
    
    console.log('🔵 handleExplain called - ONLY EXPLAIN')
    console.trace('Stack trace for handleExplain')
    
    // CRITICAL: Check if predict is already running - if so, DO NOT proceed
    if (isPredictingRef.current) {
      console.log('⚠️ PREDICT IS ALREADY RUNNING - IGNORING EXPLAIN CALL')
      return
    }
    
    // Use ref to prevent duplicate calls (more reliable than state)
    if (isExplainingRef.current) {
      console.log('⚠️ ALREADY EXPLAINING - IGNORING DUPLICATE CALL')
      return
    }
    
    if (loading) {
      console.log('⚠️ Already loading, ignoring duplicate call')
      return
    }
    
    isExplainingRef.current = true
    setLoading(true)
    // Don't clear - let user see previous if error occurs
    // setExplanation(null) // Clear previous explanation
    
    try {
      // TEMPORARILY BYPASS PREDICTION CHECK FOR TESTING
      // TODO: Re-enable this check after testing
      if (!prediction) {
        console.log('⚠️ No prediction exists, but bypassing check for testing')
        console.log('⚠️ Will call Explain API directly without prediction requirement')
        // toast.info('Please click "Predict Fraud" first to get a prediction, then click "Explain" for detailed breakdown')
        // isExplainingRef.current = false
        // setLoading(false)
        // return
      } else {
        console.log('✅ Prediction exists, proceeding with explanation')
      }
      
      // Prepare data matching API schema exactly
      const requestData = {
        amount: formData.amount || 0,
        transactions_last_hour: formData.transactions_last_hour || 1,
        historical_avg_amount: formData.historical_avg_amount || 100,
        historical_std_amount: formData.historical_std_amount || 50,
        minutes_since_last_transaction: formData.minutes_since_last_transaction || 60,
        location_changed: formData.location_changed || false,
        merchant_risk_score: formData.merchant_risk_score || 0.1,
        device_changed: formData.device_changed || false,
        ip_reputation_score: formData.ip_reputation_score || 0.5
      }

      console.log('🔍 Sending explanation request:', requestData)
      
      // Get auth headers and verify they're present
      const authHeaders = getAuthHeaders()
      const headers = { 'Content-Type': 'application/json', ...authHeaders }
      
      console.log('🔍 Request headers:', Object.keys(headers))
      const apiKey = (headers as any)['X-API-Key']
      const authToken = (headers as any)['Authorization']
      console.log('🔍 Has X-API-Key:', !!apiKey, apiKey ? 'YES' : 'NO')
      console.log('🔍 Has Authorization:', !!authToken, authToken ? 'YES' : 'NO')
      
      const response = await fetch(`${API_URL}/v1/ml/explain`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(requestData)
      })
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('❌ API Error:', response.status, errorText)
        toast.error(`Explanation failed: ${response.status}`)
        setLoading(false)
        return
      }
      
      const data = await response.json()
      console.log('✅ Explanation received:', data)
      console.log('   Explanation parts:', data.explanation_parts)
      console.log('   Explanation text:', data.explanation_text)
      console.log('   Explanation parts count:', data.explanation_parts?.length || 0)
      
      // Set explanation (this will show the detailed breakdown)
      setExplanation(data)
      
      // Show prominent toast
      toast.success('✅ Detailed Explanation Generated!', {
        description: 'Scroll down to see the blue explanation box with breakdown',
        duration: 5000,
      })
      
      // Also update prediction if explanation includes it and prediction doesn't exist
      if (data.risk_score !== undefined && !prediction) {
        setPrediction(data)
      }
      
      // Scroll to explanation after a brief delay
      setTimeout(() => {
        const explanationElement = document.querySelector('[data-explanation-section]')
        if (explanationElement) {
          explanationElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      }, 300)
    } catch (error: any) {
      console.error('❌ Error:', error)
      console.error('❌ Error name:', error.name)
      console.error('❌ Error message:', error.message)
      console.error('❌ Full error:', JSON.stringify(error, null, 2))
      
      // Check for network/connection errors
      const isNetworkError = 
        (error.name === 'TypeError' || error.name === 'AbortError') && 
        (error.message.includes('Failed to fetch') || 
         error.message.includes('ERR_INTERNET_DISCONNECTED') ||
         error.message.includes('NetworkError') ||
         error.message.includes('Network request failed') ||
         error.message.includes('ERR_CONNECTION_REFUSED') ||
         error.message.includes('timeout'))
      
      if (isNetworkError) {
        const errorMessage = `Cannot connect to backend API at ${API_URL}. Please ensure the API server is running on port 8000.`
        console.error('❌ Network Error Detected:', errorMessage)
        console.error('❌ Full error:', error)
        toast.error('Backend API Not Available', {
          description: `Cannot connect to ${API_URL}. Make sure the API server is running. Check console for details.`,
          duration: 8000,
        })
      } else {
        toast.error(`Error: ${error.message || 'Failed to get explanation'}`)
      }
    } finally {
      isExplainingRef.current = false
      setLoading(false)
    }
  }

  const loadSampleTransactions = async () => {
    try {
      const response = await fetch(`${API_URL}/v1/transactions?limit=10`, {
        headers: getAuthHeaders()
      })
      if (response.ok) {
        const data = await response.json()
        setSampleTransactions(data)
      }
    } catch (error) {
      console.error('Error loading samples:', error)
    }
  }

  const handleBatchPredict = async () => {
    if (sampleTransactions.length === 0) {
      await loadSampleTransactions()
      return
    }

    setBatchLoading(true)
    setShowBatchResults(true)
    try {
      // Convert transactions to prediction format
      const transactionsForPrediction = sampleTransactions.slice(0, 5).map(txn => ({
        amount: txn.amount || 0,
        transactions_last_hour: 3, // Default
        historical_avg_amount: 150,
        historical_std_amount: 50,
        minutes_since_last_transaction: 30,
        location_changed: false,
        merchant_risk_score: 0.2,
        device_changed: false,
        ip_reputation_score: 0.8
      }))

      const response = await fetch(`${API_URL}/v1/ml/batch-predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify(transactionsForPrediction)
      })
      
      if (response.ok) {
        const data = await response.json()
        console.log('✅ Batch predictions received:', data)
        setBatchPredictions(data.predictions || [])
        toast.success(`Analyzed ${data.predictions?.length || 0} transactions`)
      } else {
        const errorText = await response.text()
        console.error('❌ Batch predict failed:', response.status, errorText)
        toast.error(`Batch analysis failed: ${response.status}`)
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setBatchLoading(false)
    }
  }

  const loadQuickSample = (type: 'low' | 'medium' | 'high') => {
    const samples = {
      low: {
        amount: 50,
        transactions_last_hour: 1,
        historical_avg_amount: 100,
        historical_std_amount: 20,
        minutes_since_last_transaction: 120,
        location_changed: false,
        merchant_risk_score: 0.1,
        device_changed: false,
        ip_reputation_score: 0.9
      },
      medium: {
        amount: 500,
        transactions_last_hour: 5,
        historical_avg_amount: 150,
        historical_std_amount: 50,
        minutes_since_last_transaction: 10,
        location_changed: true,
        merchant_risk_score: 0.3,
        device_changed: false,
        ip_reputation_score: 0.7
      },
      high: {
        amount: 8500,
        transactions_last_hour: 15,
        historical_avg_amount: 150,
        historical_std_amount: 50,
        minutes_since_last_transaction: 2,
        location_changed: true,
        merchant_risk_score: 0.8,
        device_changed: true,
        ip_reputation_score: 0.2
      }
    }
    setFormData(samples[type])
    setPrediction(null) // Clear previous prediction
    setShowBatchResults(false) // Show single prediction view
  }

  useEffect(() => {
    loadSampleTransactions()
  }, [])

  // Real-time transaction monitoring and prediction
  useEffect(() => {
    if (!realTimeMode) return

    const fetchAndPredictNewTransactions = async () => {
      try {
        const headers = getAuthHeaders()
        // Fetch recent transactions (last 10)
        const response = await fetch(`${API_URL}/v1/transactions?limit=10&sort=desc`, {
          headers
        })
        
        if (!response.ok) return
        
        const transactions = await response.json()
        if (!Array.isArray(transactions) || transactions.length === 0) return

        // Find transactions we haven't processed yet
        const newTransactions = lastFetchedTransactionId
          ? transactions.filter(txn => txn.id > lastFetchedTransactionId)
          : transactions.slice(0, 5) // First load, take 5

        if (newTransactions.length === 0) return

        // Update last fetched ID
        const latestId = Math.max(...transactions.map((t: any) => t.id))
        setLastFetchedTransactionId(latestId)

        // Get account historical data for each transaction
        const predictions = await Promise.all(
          newTransactions.map(async (txn: any) => {
            try {
              // Fetch account historical data
              const accountRes = await fetch(`${API_URL}/v1/accounts/${txn.account_id}`, { headers })
              const accountData = accountRes.ok ? await accountRes.json() : null

              // Build ML model input
              const mlInput = {
                amount: txn.amount || 0,
                transactions_last_hour: accountData?.transactions_last_hour || 1,
                historical_avg_amount: accountData?.avg_transaction_amount || txn.amount || 100,
                historical_std_amount: accountData?.std_transaction_amount || 50,
                minutes_since_last_transaction: accountData?.minutes_since_last_txn || 60,
                location_changed: accountData?.location_changed || false,
                merchant_risk_score: txn.merchant_risk_score || 0.3,
                device_changed: accountData?.device_changed || false,
                ip_reputation_score: txn.ip_reputation_score || 0.8
              }

              // Get ML prediction
              const predictRes = await fetch(`${API_URL}/v1/ml/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...headers },
                body: JSON.stringify(mlInput)
              })

              if (!predictRes.ok) return null

              const prediction = await predictRes.json()
              
              return {
                transaction: txn,
                prediction: prediction,
                timestamp: new Date().toISOString()
              }
            } catch (error) {
              console.error('Error predicting for transaction:', txn.id, error)
              return null
            }
          })
        )

        // Filter out null results and add to real-time predictions
        const validPredictions = predictions.filter(p => p !== null)
        if (validPredictions.length > 0) {
          setRealTimePredictions(prev => [...validPredictions, ...prev].slice(0, 20)) // Keep last 20
        }
      } catch (error) {
        console.error('Error in real-time prediction:', error)
      }
    }

    // Initial fetch
    fetchAndPredictNewTransactions()

    // Set up interval to check for new transactions every 5 seconds
    const interval = setInterval(fetchAndPredictNewTransactions, 5000)

    return () => clearInterval(interval)
  }, [realTimeMode, lastFetchedTransactionId])

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'HIGH':
        return {
          bg: 'bg-red-100 dark:bg-red-900/30',
          text: 'text-red-700 dark:text-red-300',
          border: 'border-red-500',
          gradient: 'from-red-500 to-red-600'
        }
      case 'MEDIUM':
        return {
          bg: 'bg-yellow-100 dark:bg-yellow-900/30',
          text: 'text-yellow-700 dark:text-yellow-300',
          border: 'border-yellow-500',
          gradient: 'from-yellow-500 to-yellow-600'
        }
      case 'LOW':
        return {
          bg: 'bg-green-100 dark:bg-green-900/30',
          text: 'text-green-700 dark:text-green-300',
          border: 'border-green-500',
          gradient: 'from-green-500 to-green-600'
        }
      default:
        return {
          bg: 'bg-gray-100 dark:bg-gray-700',
          text: 'text-gray-700 dark:text-gray-300',
          border: 'border-gray-500',
          gradient: 'from-gray-500 to-gray-600'
        }
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <Brain className="w-8 h-8 text-purple-600 dark:text-purple-400" />
            ML Fraud Detection Model
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Real-time fraud prediction using ensemble machine learning models
          </p>
            </div>
            <button
              onClick={() => {
                setRealTimeMode(!realTimeMode)
                if (!realTimeMode) {
                  setLastFetchedTransactionId(null)
                  setRealTimePredictions([])
                  toast.success('Real-time mode enabled - monitoring new transactions')
                } else {
                  toast.info('Real-time mode disabled')
                }
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                realTimeMode
                  ? 'bg-green-600 dark:bg-green-700 text-white hover:bg-green-700 dark:hover:bg-green-800'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              {realTimeMode ? (
                <>
                  <PauseCircle className="w-5 h-5" />
                  Stop Real-Time
                </>
              ) : (
                <>
                  <PlayCircle className="w-5 h-5" />
                  Start Real-Time
                </>
              )}
            </button>
          </div>
          {realTimeMode && (
            <div className="mt-4 flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
              <Activity className="w-4 h-4 animate-pulse" />
              <span>Monitoring {realTimePredictions.length} predictions - Auto-refreshing every 5 seconds</span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Form */}
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Transaction Details
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Amount ($)
                  </label>
                  <input
                    type="number"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Transactions in Last Hour
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.transactions_last_hour || ''}
                    onChange={(e) => setFormData({ ...formData, transactions_last_hour: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Minutes Since Last Transaction
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.minutes_since_last_transaction || ''}
                    onChange={(e) => setFormData({ ...formData, minutes_since_last_transaction: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Merchant Risk Score (0-1)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={formData.merchant_risk_score || ''}
                    onChange={(e) => setFormData({ ...formData, merchant_risk_score: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    IP Reputation Score (0-1)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={formData.ip_reputation_score || ''}
                    onChange={(e) => setFormData({ ...formData, ip_reputation_score: parseFloat(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.location_changed}
                      onChange={(e) => setFormData({ ...formData, location_changed: e.target.checked })}
                      className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                    />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Location Changed
                    </span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.device_changed}
                      onChange={(e) => setFormData({ ...formData, device_changed: e.target.checked })}
                      className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                    />
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Device Changed
                    </span>
                  </label>
                </div>
              </div>

              <div className="flex gap-3 mt-6" style={{ position: 'relative', zIndex: 1 }}>
                <button
                  type="button"
                  id="predict-fraud-button"
                  onClick={(e) => {
                    console.log('🟣 Predict Fraud button clicked', e.target, 'ID:', e.currentTarget.id)
                    console.log('🟣 isPredictingRef.current:', isPredictingRef.current)
                    console.log('🟣 isExplainingRef.current:', isExplainingRef.current)
                    
                    e.preventDefault()
                    e.stopPropagation()
                    e.nativeEvent?.stopImmediatePropagation?.()
                    
                    // CRITICAL: Verify button ID before proceeding
                    if (e.currentTarget.id !== 'predict-fraud-button') {
                      console.error('❌ Button ID mismatch! Expected predict-fraud-button, got:', e.currentTarget.id)
                      return
                    }
                    
                    // CRITICAL: If explain is running, abort immediately
                    if (isExplainingRef.current) {
                      console.error('❌ CANNOT PREDICT - EXPLAIN IS ALREADY RUNNING!')
                      return
                    }
                    
                    handlePredict(e)
                  }}
                  disabled={loading || isExplainingRef.current}
                  className="flex-1 bg-purple-600 dark:bg-purple-700 text-white py-3 px-4 rounded-lg hover:bg-purple-700 dark:hover:bg-purple-800 transition-colors font-medium disabled:opacity-50"
                  style={{ position: 'relative', zIndex: 2 }}
                >
                  {loading ? 'Analyzing...' : 'Predict Fraud'}
                </button>
                <button
                  type="button"
                  id="explain-button"
                  onClick={(e) => {
                    console.log('🟦 Explain button clicked', e.target, 'ID:', e.currentTarget.id)
                    console.log('🟦 isPredictingRef.current:', isPredictingRef.current)
                    console.log('🟦 isExplainingRef.current:', isExplainingRef.current)
                    
                    e.preventDefault()
                    e.stopPropagation()
                    e.nativeEvent?.stopImmediatePropagation?.()
                    
                    // CRITICAL: Verify button ID before proceeding
                    if (e.currentTarget.id !== 'explain-button') {
                      console.error('❌ Button ID mismatch! Expected explain-button, got:', e.currentTarget.id)
                      return
                    }
                    
                    // CRITICAL: If predict is running, abort immediately
                    if (isPredictingRef.current) {
                      console.error('❌ CANNOT EXPLAIN - PREDICT IS ALREADY RUNNING!')
                      return
                    }
                    
                    handleExplain(e)
                  }}
                  disabled={loading || isPredictingRef.current}
                  className="flex-1 bg-blue-600 dark:bg-blue-700 text-white py-3 px-4 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 transition-colors font-medium disabled:opacity-50"
                  style={{ position: 'relative', zIndex: 2 }}
                >
                  Explain
                </button>
              </div>

              {/* Quick Test Samples */}
              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Quick Test Samples:
                </h3>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      loadQuickSample('low')
                    }}
                    className="px-3 py-2 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-lg hover:bg-green-200 dark:hover:bg-green-900/50 text-sm font-medium transition-colors"
                  >
                    Low Risk
                  </button>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      loadQuickSample('medium')
                    }}
                    className="px-3 py-2 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded-lg hover:bg-yellow-200 dark:hover:bg-yellow-900/50 text-sm font-medium transition-colors"
                  >
                    Medium Risk
                  </button>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      loadQuickSample('high')
                    }}
                    className="px-3 py-2 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 text-sm font-medium transition-colors"
                  >
                    High Risk
                  </button>
                </div>
              </div>

              {/* Batch Prediction */}
              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    handleBatchPredict()
                  }}
                  disabled={batchLoading}
                  className="w-full flex items-center justify-center gap-2 bg-indigo-600 dark:bg-indigo-700 text-white py-3 px-4 rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-800 transition-colors font-medium disabled:opacity-50"
                >
                  {batchLoading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Analyzing Batch...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4" />
                      Analyze Sample Transactions ({sampleTransactions.length} available)
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Prediction Results */}
          <div className="space-y-6">
            {prediction && (
              <>
                {/* Risk Score Card */}
                <div className={`rounded-lg shadow-lg border-2 ${getRiskColor(prediction.risk_level).border} p-6`}>
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                      Risk Assessment
                    </h2>
                    <span className={`px-4 py-2 rounded-full font-bold ${getRiskColor(prediction.risk_level).bg} ${getRiskColor(prediction.risk_level).text}`}>
                      {prediction.risk_level} RISK
                    </span>
                  </div>

                  <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-4xl font-bold text-gray-900 dark:text-white">
                        {prediction.risk_score.toFixed(1)}
                      </span>
                      <span className="text-lg text-gray-600 dark:text-gray-400">/ 100</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full bg-gradient-to-r ${getRiskColor(prediction.risk_level).gradient}`}
                        style={{ width: `${prediction.risk_score}%` }}
                      />
                    </div>
                  </div>

                  <div className={`p-4 rounded-lg ${getRiskColor(prediction.risk_level).bg}`}>
                    <p className={`text-sm font-medium ${getRiskColor(prediction.risk_level).text}`}>
                      {prediction.recommendation}
                    </p>
                  </div>

                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Model Confidence: <span className="font-bold">{(prediction.model_confidence * 100).toFixed(0)}%</span>
                    </p>
                  </div>
                </div>

                {/* Model Scores */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                    Ensemble Model Scores
                  </h3>
                  
                  <div className="space-y-3">
                    {Object.entries(prediction.model_scores).map(([model, score]: [string, any]) => (
                      <div key={model}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                            {model.replace('_', ' ')}
                          </span>
                          <span className="text-sm font-bold text-gray-900 dark:text-white">
                            {(score * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="h-2 rounded-full bg-purple-600 dark:bg-purple-500"
                            style={{ width: `${score * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Feature Contributions */}
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <Info className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    Feature Contributions
                  </h3>
                  
                  <div className="space-y-3">
                    {Object.entries(prediction.feature_contributions).map(([feature, contribution]: [string, any]) => (
                      <div key={feature}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                            {feature.replace('_', ' ')}
                          </span>
                          <span className={`text-sm font-bold ${contribution > 10 ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white'}`}>
                            {contribution > 0 ? '+' : ''}{contribution.toFixed(1)}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${contribution > 10 ? 'bg-red-600 dark:bg-red-500' : 'bg-blue-600 dark:bg-blue-500'}`}
                            style={{ width: `${Math.abs(contribution) * 2}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Triggered Rules */}
                {prediction.triggered_rules && prediction.triggered_rules.length > 0 && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                      Triggered Rules
                    </h3>
                    
                    <ul className="space-y-2">
                      {prediction.triggered_rules.map((rule: string, idx: number) => (
                        <li key={idx} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                          <span className="text-orange-600 dark:text-orange-400 mt-0.5">•</span>
                          <span>{rule}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

              </>
            )}

            {/* Detailed Explanation - Shows independently and prominently */}
            {explanation && (
              <div 
                data-explanation-section
                className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg shadow-lg border-2 border-blue-500 dark:border-blue-400 p-6 mb-6"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900/40 rounded-lg">
                    <Info className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                      🔍 Detailed Explanation
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Why this transaction was flagged - Detailed breakdown showing model reasoning
                    </p>
                  </div>
                  <div className="text-xs text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/40 px-2 py-1 rounded">
                    ACTIVE
                  </div>
                </div>
                
                {/* Show explanation_parts if available */}
                {explanation.explanation_parts && Array.isArray(explanation.explanation_parts) && explanation.explanation_parts.length > 0 && (
                  <div className="space-y-3 bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 mb-4">
                    {explanation.explanation_parts
                      .filter((part: any) => {
                        if (!part || typeof part !== 'string') return false
                        const trimmed = part.trim()
                        return trimmed !== '' && trimmed.length > 1 && !trimmed.startsWith('\n')
                      })
                      .map((part: string, idx: number) => {
                        const isRiskLevel = part.includes('🟢') || part.includes('🟡') || part.includes('🔴')
                        const isSection = part.trim().startsWith('**') && part.includes(':')
                        const isList = part.trim().includes('•') || part.includes('contribution')
                        
                        let content = part
                          .replace(/\*\*(.*?)\*\*/g, '$1')
                          .replace(/🟢|🟡|🔴/g, '')
                          .trim()
                        
                        if (!content || content.length < 2) return null
                        
                        return (
                          <div
                            key={idx}
                            className={`${
                              isRiskLevel
                                ? 'text-base font-bold p-3 rounded-lg bg-blue-100 dark:bg-blue-900/40 border-l-4 border-blue-600 text-blue-900 dark:text-blue-100'
                                : isSection
                                ? 'font-semibold text-gray-900 dark:text-white text-sm mt-3 mb-2 pb-2 border-b border-gray-300 dark:border-gray-600'
                                : isList
                                ? 'text-sm text-gray-700 dark:text-gray-300 ml-4'
                                : 'text-sm text-gray-700 dark:text-gray-300'
                            }`}
                          >
                            {isList && <span className="text-blue-600 dark:text-blue-400 mr-2">•</span>}
                            {content}
                          </div>
                        )
                      })}
                    {explanation.explanation_parts.filter((p: any) => p && typeof p === 'string' && p.trim()).length === 0 && (
                      <p className="text-sm text-gray-500 dark:text-gray-400 italic">Processing explanation parts...</p>
                    )}
                  </div>
                )}
                
                {/* ALWAYS show explanation_text - this is the main content */}
                {explanation.explanation_text ? (
                  <div className="bg-white dark:bg-gray-800 rounded-lg p-5 border-2 border-blue-200 dark:border-blue-700 mb-4">
                    <h4 className="text-base font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <Info className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                      Complete Explanation
                    </h4>
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                      <div className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line leading-relaxed">
                        {explanation.explanation_text
                          .replace(/\*\*(.*?)\*\*/g, '$1')
                          .replace(/🟢|🟡|🔴/g, '')
                          .split('\n')
                          .map((line: string, lineIdx: number, arr: string[]) => (
                            <div key={lineIdx} className={line.trim().startsWith('•') ? 'ml-4' : ''}>
                              {line}
                              {lineIdx < arr.length - 1 && <br />}
                            </div>
                          ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-300 dark:border-yellow-700 rounded-lg p-4 mb-4">
                    <p className="text-sm text-yellow-800 dark:text-yellow-200">
                      ⚠️ Explanation text not available. Showing basic prediction data below.
                    </p>
                  </div>
                )}
                
                {/* Show risk score and basic info if explanation_text missing */}
                {!explanation.explanation_text && explanation.risk_score !== undefined && (
                  <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 mb-4">
                    <h4 className="text-base font-bold text-gray-900 dark:text-white mb-3">Risk Assessment</h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Risk Score:</span>
                        <span className="text-xl font-bold text-gray-900 dark:text-white">{explanation.risk_score.toFixed(1)}/100</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Risk Level:</span>
                        <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                          explanation.risk_level === 'HIGH' ? 'bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200' :
                          explanation.risk_level === 'MEDIUM' ? 'bg-yellow-200 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-200' :
                          'bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200'
                        }`}>
                          {explanation.risk_level}
                        </span>
                      </div>
                      {explanation.recommendation && (
                        <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                          <span className="text-sm text-gray-600 dark:text-gray-400">Recommendation: </span>
                          <span className="text-sm font-medium text-gray-900 dark:text-white">{explanation.recommendation}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {explanation.triggered_rules && explanation.triggered_rules.length > 0 && (
                  <div className="mt-4 pt-4 border-t-2 border-blue-300 dark:border-blue-700">
                    <h4 className="text-base font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                      Triggered Risk Rules ({explanation.triggered_rules.length})
                    </h4>
                    <ul className="space-y-2 bg-white dark:bg-gray-800 rounded-lg p-4">
                      {explanation.triggered_rules.map((rule: string, idx: number) => (
                        <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-3 p-2 rounded bg-orange-50 dark:bg-orange-900/20">
                          <span className="text-orange-600 dark:text-orange-400 font-bold mt-0.5">⚠️</span>
                          <span className="flex-1">{rule}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {!prediction && !showBatchResults && !realTimeMode && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-12 text-center">
                <Brain className="w-16 h-16 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">
                  Enter transaction details and click "Predict Fraud" to see ML analysis
                </p>
                <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
                  Or enable "Start Real-Time" to automatically analyze new transactions
                </p>
              </div>
            )}

            {/* Real-Time Predictions Feed */}
            {realTimeMode && (
              <div className="space-y-4">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                      <Activity className="w-5 h-5 text-green-600 dark:text-green-400 animate-pulse" />
                      Real-Time Predictions Feed
                    </h3>
                    <span className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-sm font-medium">
                      {realTimePredictions.length} predictions
                    </span>
          </div>
                  
                  {realTimePredictions.length === 0 ? (
                    <div className="text-center py-8">
                      <Activity className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-4 animate-pulse" />
                      <p className="text-gray-500 dark:text-gray-400">
                        Waiting for new transactions...
                      </p>
                      <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
                        New transactions will be automatically analyzed and displayed here
                      </p>
        </div>
                  ) : (
                    <div className="space-y-3 max-h-96 overflow-y-auto">
                      {realTimePredictions.map((item: any, idx: number) => (
                        <div
                          key={`${item.transaction.id}-${idx}`}
                          className={`p-4 rounded-lg border-2 ${
                            item.prediction.risk_level === 'HIGH'
                              ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                              : item.prediction.risk_level === 'MEDIUM'
                              ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
                              : 'border-green-500 bg-green-50 dark:bg-green-900/20'
                          }`}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-medium text-gray-900 dark:text-white">
                                  Transaction #{item.transaction.id}
                                </span>
                                <span className="text-xs text-gray-500 dark:text-gray-400">
                                  {new Date(item.timestamp).toLocaleTimeString()}
                                </span>
                              </div>
                              <div className="text-sm text-gray-600 dark:text-gray-400">
                                Account #{item.transaction.account_id} • ${item.transaction.amount?.toLocaleString() || 'N/A'}
                                {item.transaction.merchant && ` • ${item.transaction.merchant}`}
                              </div>
                            </div>
                            <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                              item.prediction.risk_level === 'HIGH'
                                ? 'bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200'
                                : item.prediction.risk_level === 'MEDIUM'
                                ? 'bg-yellow-200 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-200'
                                : 'bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200'
                            }`}>
                              {item.prediction.risk_level}
                            </span>
                          </div>
                          <div className="grid grid-cols-3 gap-4 text-sm mt-3">
                            <div>
                              <span className="text-gray-500 dark:text-gray-400">Risk Score:</span>
                              <span className="font-bold ml-1 text-gray-900 dark:text-white">
                                {item.prediction.risk_score?.toFixed(1) || 'N/A'}/100
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500 dark:text-gray-400">Confidence:</span>
                              <span className="font-bold ml-1 text-gray-900 dark:text-white">
                                {((item.prediction.model_confidence || 0) * 100).toFixed(0)}%
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500 dark:text-gray-400">Time:</span>
                              <span className="font-bold ml-1 text-gray-900 dark:text-white">
                                {new Date(item.transaction.txn_time || item.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                          </div>
                          {item.prediction.recommendation && (
                            <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                              <p className="text-xs text-gray-600 dark:text-gray-400">
                                {item.prediction.recommendation}
                              </p>
                            </div>
                          )}
                          {item.prediction.triggered_rules && item.prediction.triggered_rules.length > 0 && (
                            <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                              <p className="text-xs text-gray-600 dark:text-gray-400">
                                Rules: {item.prediction.triggered_rules.join(', ')}
                              </p>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* Batch Analysis Results Section */}
            {showBatchResults && (
              <div className="space-y-4">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                    <Zap className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                    Batch Analysis Results
                  </h3>
                  
                  {batchLoading ? (
                    <div className="text-center py-8">
                      <RefreshCw className="w-8 h-8 text-indigo-600 dark:text-indigo-400 animate-spin mx-auto mb-2" />
                      <p className="text-gray-500 dark:text-gray-400">Analyzing transactions...</p>
                    </div>
                  ) : batchPredictions.length > 0 ? (
                    <div className="space-y-4">
                      {/* Summary Statistics */}
                      {(() => {
                        const summary = batchPredictions.reduce((acc, item) => {
                          acc.total++
                          if (item.prediction.risk_level === 'HIGH') acc.high++
                          else if (item.prediction.risk_level === 'MEDIUM') acc.medium++
                          else acc.low++
                          acc.totalAmount += item.transaction.amount || 0
                          acc.totalRiskScore += item.prediction.risk_score || 0
                          return acc
                        }, { total: 0, high: 0, medium: 0, low: 0, totalAmount: 0, totalRiskScore: 0 })
                        
                        return (
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg">
                            <div className="text-center">
                              <div className="text-2xl font-bold text-gray-900 dark:text-white">{summary.total}</div>
                              <div className="text-xs text-gray-600 dark:text-gray-400">Total Transactions</div>
                            </div>
                            <div className="text-center">
                              <div className="text-2xl font-bold text-red-600 dark:text-red-400">{summary.high}</div>
                              <div className="text-xs text-gray-600 dark:text-gray-400">High Risk</div>
                            </div>
                            <div className="text-center">
                              <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{summary.medium}</div>
                              <div className="text-xs text-gray-600 dark:text-gray-400">Medium Risk</div>
                            </div>
                            <div className="text-center">
                              <div className="text-2xl font-bold text-green-600 dark:text-green-400">{summary.low}</div>
                              <div className="text-xs text-gray-600 dark:text-gray-400">Low Risk</div>
                            </div>
                          </div>
                        )
                      })()}
                      
                      {batchPredictions.map((item, idx) => (
                        <div
                          key={idx}
                          className={`p-4 rounded-lg border-2 ${
                            item.prediction.risk_level === 'HIGH'
                              ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                              : item.prediction.risk_level === 'MEDIUM'
                              ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
                              : 'border-green-500 bg-green-50 dark:bg-green-900/20'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-3">
                            <div>
                              <span className="font-semibold text-gray-900 dark:text-white">
                                Transaction #{idx + 1}
                              </span>
                              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                Amount: ${(item.transaction.amount || 0).toLocaleString()}
                              </div>
                            </div>
                            <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                              item.prediction.risk_level === 'HIGH'
                                ? 'bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200'
                                : item.prediction.risk_level === 'MEDIUM'
                                ? 'bg-yellow-200 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-200'
                                : 'bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200'
                            }`}>
                              {item.prediction.risk_level}
                            </span>
                          </div>
                          
                          <div className="grid grid-cols-3 gap-4 text-sm mb-3">
                            <div>
                              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Risk Score</div>
                              <div className="font-bold text-lg text-gray-900 dark:text-white">
                                {item.prediction.risk_score?.toFixed(1) || 'N/A'}/100
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Confidence</div>
                              <div className="font-bold text-lg text-gray-900 dark:text-white">
                                {((item.prediction.model_confidence || 0) * 100).toFixed(0)}%
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Models</div>
                              <div className="text-xs font-medium text-gray-700 dark:text-gray-300">
                                {item.prediction.model_scores ? 
                                  Object.keys(item.prediction.model_scores).length : 0} active
                              </div>
                            </div>
                          </div>
                          
                          {/* Progress bar for risk score */}
                          <div className="mb-3">
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${
                                  item.prediction.risk_level === 'HIGH'
                                    ? 'bg-red-500'
                                    : item.prediction.risk_level === 'MEDIUM'
                                    ? 'bg-yellow-500'
                                    : 'bg-green-500'
                                }`}
                                style={{ width: `${Math.min(100, item.prediction.risk_score || 0)}%` }}
                              />
                            </div>
                          </div>
                          
                          {item.prediction.triggered_rules && item.prediction.triggered_rules.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                              <div className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">
                                ⚠️ Triggered Rules:
                              </div>
                              <ul className="space-y-1">
                                {item.prediction.triggered_rules.slice(0, 3).map((rule: string, ruleIdx: number) => (
                                  <li key={ruleIdx} className="text-xs text-gray-600 dark:text-gray-400 flex items-start gap-1">
                                    <span className="text-orange-500 mt-0.5">•</span>
                                    <span>{rule}</span>
                                  </li>
                                ))}
                                {item.prediction.triggered_rules.length > 3 && (
                                  <li className="text-xs text-gray-500 dark:text-gray-500 italic">
                                    +{item.prediction.triggered_rules.length - 3} more rules
                                  </li>
                                )}
                              </ul>
                            </div>
                          )}
                          
                          {item.prediction.recommendation && (
                            <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                              <div className="text-xs text-gray-600 dark:text-gray-400">
                                💡 {item.prediction.recommendation}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                      <button
                        onClick={() => setShowBatchResults(false)}
                        className="w-full mt-4 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                      >
                        Back to Single Prediction
                      </button>
                    </div>
                  ) : (
                    <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                      No predictions available
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

