'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  // Check for existing valid token
  useEffect(() => {
    const existingToken = localStorage.getItem('auth_token')
    const manualLogout = localStorage.getItem('manual_logout')
    
    // If user has a valid token, redirect to dashboard
    if (existingToken && manualLogout !== 'true') {
      router.push('/dashboard')
      return
    }

    // Clear any invalid tokens
    if (manualLogout === 'true') {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
      localStorage.removeItem('tenant')
      console.log('⏸️ Please sign in')
    }
  }, [router])

  const handleDemoLogin = async () => {
    // Clear manual logout flag
    localStorage.removeItem('manual_logout')
    setLoading(true)
    setError('')
    
    try {
      // Add timeout to login request
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout
      
      // Call real login API with demo credentials
      const response = await fetch(`${API_URL}/api/v1/tenants/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'admin@demo.com',
          password: 'Password123!'
        }),
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        const errorText = await response.text()
        let errorData
        try {
          errorData = JSON.parse(errorText)
        } catch {
          errorData = { detail: errorText || `HTTP ${response.status}` }
        }
        console.error('Demo login error:', response.status, errorData)
        throw new Error(errorData.detail || 'Demo login failed')
      }
      
      const data = await response.json()
      console.log('Demo login response:', data)
      
      if (!data.access_token) {
        throw new Error('Invalid response: No access token received')
      }
      
      // Store real JWT token and user info
      localStorage.setItem('auth_token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      localStorage.setItem('tenant', JSON.stringify(data.tenant))
      localStorage.removeItem('manual_logout') // Clear manual logout flag
      
      console.log('✅ Demo login successful')
      console.log('Token stored:', data.access_token.substring(0, 20) + '...')
      
      // Use window.location instead of router.push to force full page reload
      // This ensures the auth hook picks up the new token
      window.location.href = '/dashboard'
    } catch (err: any) {
      console.error('Demo login error:', err)
      console.error('Error name:', err.name)
      console.error('Error message:', err.message)
      
      let errorMessage = 'Demo login failed. Please try manual login.'
      
      if (err.name === 'AbortError' || err.message.includes('timeout')) {
        errorMessage = 'Login timeout. The server is taking too long to respond. Please check if the backend is running on port 8000.'
      } else if (err.message.includes('Failed to fetch') || 
                 err.message.includes('NetworkError') ||
                 err.message.includes('ERR_CONNECTION_REFUSED') ||
                 err.message.includes('ERR_INTERNET_DISCONNECTED')) {
        errorMessage = `Cannot connect to backend API at ${API_URL}. Please ensure the API server is running on port 8000.`
      } else if (err.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
      setLoading(false)
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    
    // Clear manual logout flag when logging in
    localStorage.removeItem('manual_logout')
    
    try {
      // Add timeout to login request
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 second timeout
      
      // Use new multi-tenancy login endpoint
      const response = await fetch(`${API_URL}/api/v1/tenants/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        const errorText = await response.text()
        let errorData
        try {
          errorData = JSON.parse(errorText)
        } catch {
          errorData = { detail: errorText || `HTTP ${response.status}: ${response.statusText}` }
        }
        console.error('Login error response:', response.status, errorData)
        throw new Error(errorData.detail || `Login failed (${response.status})`)
      }
      
      const data = await response.json()
      console.log('Login response:', data)
      
      if (!data.access_token) {
        throw new Error('Invalid response: No access token received')
      }
      
      // Store JWT token and user info
      localStorage.setItem('auth_token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      localStorage.setItem('tenant', JSON.stringify(data.tenant))
      localStorage.removeItem('manual_logout') // Clear manual logout flag
      
      console.log('✅ Login successful:', data.user.email)
      console.log('Token stored:', data.access_token.substring(0, 20) + '...')
      
      // Use window.location instead of router.push to force full page reload
      // This ensures the auth hook picks up the new token
      window.location.href = '/dashboard'
    } catch (err: any) {
      console.error('Login error:', err)
      console.error('Error name:', err.name)
      console.error('Error message:', err.message)
      
      let errorMessage = 'Login failed. Please try again.'
      
      if (err.name === 'AbortError' || err.message.includes('timeout')) {
        errorMessage = 'Login timeout. The server is taking too long to respond. Please check if the backend is running on port 8000.'
      } else if (err.message.includes('Failed to fetch') || 
                 err.message.includes('NetworkError') ||
                 err.message.includes('ERR_CONNECTION_REFUSED') ||
                 err.message.includes('ERR_INTERNET_DISCONNECTED')) {
        errorMessage = `Cannot connect to backend API at ${API_URL}. Please ensure the API server is running on port 8000. Check the console for details.`
      } else if (err.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
      // Restore manual logout flag if login fails
      localStorage.setItem('manual_logout', 'true')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <div>
          <h2 className="text-center text-3xl font-bold text-gray-900">Fraud Detection Portal</h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Sign in to your account
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="analyst@bank.com"
              disabled={loading}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your password"
              disabled={loading}
            />
            <p className="mt-2 text-xs text-gray-500">
              Demo: analyst@bank.com / password123
            </p>
          </div>
          <div className="space-y-3">
            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
            <button
              type="button"
              onClick={handleDemoLogin}
              className="w-full flex justify-center py-2 px-4 border-2 border-blue-600 rounded-md shadow-sm text-sm font-medium text-blue-600 bg-white hover:bg-blue-50"
            >
              Quick Demo Login
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
