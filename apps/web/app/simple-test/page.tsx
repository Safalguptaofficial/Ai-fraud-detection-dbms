'use client'

import { useState } from 'react'

export default function SimpleTest() {
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)

  const testFetch = async () => {
    setLoading(true)
    try {
      console.log('Starting fetch...')
      const response = await fetch('http://localhost:8000/v1/accounts')
      console.log('Response received:', response.status)
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const data = await response.json()
      console.log('Data parsed:', data)
      setResult(`Success: ${data.length} accounts`)
    } catch (error) {
      console.error('Fetch error:', error)
      setResult(`Error: ${error.message}`)
    }
    setLoading(false)
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Simple API Test</h1>
      <button 
        onClick={testFetch}
        disabled={loading}
        className="bg-blue-500 text-white px-4 py-2 rounded disabled:opacity-50"
      >
        {loading ? 'Testing...' : 'Test Fetch'}
      </button>
      <div className="mt-4">
        <strong>Result:</strong> {result}
      </div>
    </div>
  )
}
