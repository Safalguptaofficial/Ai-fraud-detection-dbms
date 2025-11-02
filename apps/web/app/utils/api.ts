/**
 * Centralized API Configuration and Utilities
 * Provides consistent API URL management and helper functions
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export { API_URL }

/**
 * Build full API endpoint URL
 */
export function apiUrl(endpoint: string): string {
  // Remove leading slash if present
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint
  return `${API_URL}/${cleanEndpoint}`
}

/**
 * Standard API request wrapper with error handling
 */
export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = apiUrl(endpoint)
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const errorText = await response.text()
      let errorData
      try {
        errorData = JSON.parse(errorText)
      } catch {
        errorData = { detail: errorText || `HTTP ${response.status}` }
      }

      throw new APIError(
        errorData.detail || `Request failed: ${response.statusText}`,
        response.status,
        errorData
      )
    }

    // Handle empty responses
    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      return await response.json()
    }

    return await response.text() as any
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }
    
    // Better error messages for network errors
    const errorMessage = error instanceof Error ? error.message : 'Network error'
    let userMessage = errorMessage
    
    // Check for common network errors
    if (errorMessage.includes('Failed to fetch') || 
        errorMessage.includes('NetworkError') ||
        errorMessage.includes('ERR_INTERNET_DISCONNECTED') ||
        errorMessage.includes('ERR_CONNECTION_REFUSED')) {
      userMessage = `Cannot connect to backend API at ${API_URL}. Please ensure the API server is running on port 8000.`
    } else if (errorMessage.includes('timeout') || errorMessage.includes('AbortError')) {
      userMessage = 'Request timed out. The server is taking too long to respond.'
    }
    
    throw new APIError(userMessage, 0, error)
  }
}

/**
 * API Error class
 */
export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message)
    this.name = 'APIError'
  }
}

/**
 * Check if API is available
 */
export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(apiUrl(''))
    return response.ok
  } catch {
    return false
  }
}

