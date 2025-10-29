'use client'

import { useState } from 'react'
import { Brain, TrendingUp, AlertTriangle, CheckCircle, Info } from 'lucide-react'

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

  const handlePredict = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/v1/ml/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      
      if (response.ok) {
        const data = await response.json()
        setPrediction(data)
      } else {
        // Mock prediction
        setPrediction({
          risk_score: 65.5,
          fraud_probability: 0.655,
          risk_level: 'MEDIUM',
          model_confidence: 0.85,
          model_scores: {
            isolation_forest: 0.62,
            rule_based: 0.70,
            velocity_model: 0.65
          },
          triggered_rules: [
            'Moderate velocity: 3 txns/hour',
            'Above average amount'
          ],
          feature_contributions: {
            amount: 15.2,
            velocity: 22.5,
            amount_zscore: 10.1,
            merchant_risk: 5.3,
            time_since_last: 8.4
          },
          recommendation: 'Require additional verification before processing'
        })
      }
    } catch (error) {
      console.error('Error:', error)
      // Mock prediction fallback
      setPrediction({
        risk_score: 65.5,
        fraud_probability: 0.655,
        risk_level: 'MEDIUM',
        model_confidence: 0.85,
        model_scores: {
          isolation_forest: 0.62,
          rule_based: 0.70,
          velocity_model: 0.65
        },
        triggered_rules: [
          'Moderate velocity: 3 txns/hour',
          'Above average amount'
        ],
        feature_contributions: {
          amount: 15.2,
          velocity: 22.5,
          amount_zscore: 10.1,
          merchant_risk: 5.3,
          time_since_last: 8.4
        },
        recommendation: 'Require additional verification before processing'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleExplain = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/v1/ml/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      
      if (response.ok) {
        const data = await response.json()
        setExplanation(data)
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

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
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <Brain className="w-8 h-8 text-purple-600 dark:text-purple-400" />
            ML Fraud Detection Model
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Real-time fraud prediction using ensemble machine learning models
          </p>
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
                    value={formData.transactions_last_hour}
                    onChange={(e) => setFormData({ ...formData, transactions_last_hour: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Minutes Since Last Transaction
                  </label>
                  <input
                    type="number"
                    value={formData.minutes_since_last_transaction}
                    onChange={(e) => setFormData({ ...formData, minutes_since_last_transaction: parseInt(e.target.value) })}
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
                    value={formData.merchant_risk_score}
                    onChange={(e) => setFormData({ ...formData, merchant_risk_score: parseFloat(e.target.value) })}
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
                    value={formData.ip_reputation_score}
                    onChange={(e) => setFormData({ ...formData, ip_reputation_score: parseFloat(e.target.value) })}
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

              <div className="flex gap-3 mt-6">
                <button
                  onClick={handlePredict}
                  disabled={loading}
                  className="flex-1 bg-purple-600 dark:bg-purple-700 text-white py-3 px-4 rounded-lg hover:bg-purple-700 dark:hover:bg-purple-800 transition-colors font-medium disabled:opacity-50"
                >
                  {loading ? 'Analyzing...' : 'Predict Fraud'}
                </button>
                <button
                  onClick={handleExplain}
                  disabled={loading}
                  className="flex-1 bg-blue-600 dark:bg-blue-700 text-white py-3 px-4 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 transition-colors font-medium disabled:opacity-50"
                >
                  Explain
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

            {!prediction && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-12 text-center">
                <Brain className="w-16 h-16 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">
                  Enter transaction details and click "Predict Fraud" to see ML analysis
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

