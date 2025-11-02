'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'

export function useAuth() {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    const userStr = localStorage.getItem('user')
    const currentPath = pathname
    const manualLogout = localStorage.getItem('manual_logout')
    
    // Don't redirect from login page itself
    if (currentPath === '/login') {
      setLoading(false)
      return
    }
    
    // If manually logged out, don't check auth (user needs to login again)
    if (manualLogout === 'true') {
      setIsAuthenticated(false)
      setLoading(false)
      return
    }
    
    if (token && userStr) {
      try {
        const userData = JSON.parse(userStr)
        setUser(userData)
        setIsAuthenticated(true)
        console.log('✅ Auth check passed:', userData.email)
      } catch (e) {
        console.error('Failed to parse user data:', e)
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user')
        setIsAuthenticated(false)
        // Only redirect if not already on login page
        if (currentPath !== '/login') {
        router.push('/login')
        }
      }
    } else {
      // No token found - but don't redirect immediately
      // Let the page try to load with API key fallback
      // Dashboard will redirect on 401 errors
      setIsAuthenticated(false)
      console.log('⚠️ No auth token found, will use API key fallback')
    }
    setLoading(false)
  }, [router, pathname])

  const logout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    localStorage.setItem('manual_logout', 'true')
    setIsAuthenticated(false)
    router.push('/login')
  }

  return { user, loading, logout, isAuthenticated }
}

export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('auth_token')
}

export function getAuthHeaders(): HeadersInit {
  const token = getAuthToken()
  const headers: HeadersInit = {}
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
    console.log('✅ Using JWT token for auth')
  } else {
    // Fallback demo API key for development
    headers['X-API-Key'] = 'fgk_live_xj2twCjoRDv2q9ReBlNkf1wxvte-e8Jhz5cOj_kh5ik'
    console.log('⚠️ No JWT token, using API key fallback')
  }
  
  return headers
}
