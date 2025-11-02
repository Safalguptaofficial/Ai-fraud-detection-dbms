'use client'

import { useState, useRef, useEffect } from 'react'
import { useAuth, getAuthHeaders } from '../../utils/auth'
import { Upload, FileText, Download, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { toast } from 'sonner'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function DataUploadPage() {
  const { isAuthenticated } = useAuth()
  const [loading, setLoading] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [uploadResult, setUploadResult] = useState<any>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // Debug: Log component state changes
  useEffect(() => {
    console.log('📝 Upload page state updated:', { 
      hasFile: !!file, 
      fileName: file?.name,
      loading, 
      isAuthenticated,
      uploadResult: !!uploadResult
    })
  }, [file, loading, isAuthenticated, uploadResult])

  const downloadTemplate = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/ingestion/template`, {
        headers: getAuthHeaders()
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to download template' }))
        throw new Error(errorData.detail || 'Failed to download template')
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'transaction_template.csv'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      toast.success('Template downloaded!')
    } catch (error: any) {
      console.error('Template download error:', error)
      toast.error(error.message || 'Failed to download template')
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      const fileType = selectedFile.name.split('.').pop()?.toLowerCase()
      if (!['csv', 'xlsx', 'xls'].includes(fileType || '')) {
        toast.error('Please select a CSV or Excel file')
        return
      }
      setFile(selectedFile)
      setUploadResult(null)
    }
  }

  const uploadFile = async () => {
    // Add early validation
    if (!file) {
      console.warn('⚠️ uploadFile called but no file selected')
      toast.error('Please select a file first')
      setLoading(false)
      return
    }
    
    console.log('🔵 Upload function called', { 
      file: file.name, 
      fileSize: file.size,
      fileType: file.type,
      timestamp: new Date().toISOString()
    })
    
    // Additional validation
    if (loading) {
      console.warn('⚠️ Upload already in progress, ignoring duplicate call')
      return
    }

    console.log('📤 Starting file upload...', {
      filename: file.name,
      size: file.size,
      type: file.type,
      apiUrl: API_URL
    })

    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)

      // Get auth headers but DO NOT include Content-Type for FormData
      // The browser will set it automatically with the boundary parameter
      const authHeaders = getAuthHeaders()
      const headers: HeadersInit = {}
      
      // Add auth headers (API key or JWT token)
      if (authHeaders['X-API-Key']) {
        headers['X-API-Key'] = authHeaders['X-API-Key'] as string
        console.log('✅ Using API key for authentication')
      }
      if (authHeaders['Authorization']) {
        headers['Authorization'] = authHeaders['Authorization'] as string
        console.log('✅ Using JWT token for authentication')
      }
      
      if (Object.keys(headers).length === 0) {
        console.warn('⚠️ No authentication headers found')
        toast.error('Authentication error. Please log in again.')
        setLoading(false)
        return
      }
      
      // DO NOT set Content-Type - browser needs to set it with boundary

      const uploadUrl = `${API_URL}/api/v1/ingestion/files`
      console.log('📡 Sending upload request to:', uploadUrl)

      const response = await fetch(uploadUrl, {
        method: 'POST',
        headers: headers,
        body: formData
      })
      
      console.log('📥 Received response:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok
      })

      if (!response.ok) {
        let errorData: any = { detail: 'Upload failed' }
        try {
          const text = await response.text()
          if (text) {
            errorData = JSON.parse(text)
          }
        } catch (e) {
          console.error('Failed to parse error response:', e)
        }
        
        console.error('Upload error:', {
          status: response.status,
          statusText: response.statusText,
          errorData,
          url: `${API_URL}/api/v1/ingestion/files`
        })
        
        let errorMessage = 'Upload failed'
        
        if (errorData?.detail) {
          errorMessage = errorData.detail
        } else if (errorData?.error) {
          errorMessage = errorData.error
        } else if (errorData?.message) {
          errorMessage = errorData.message
        } else if (response.status === 401 || response.status === 403) {
          errorMessage = 'Authentication required. Please log in again.'
        } else if (response.status === 400) {
          errorMessage = errorData.detail || 'Invalid file format or missing required columns. Please check your CSV file matches the template.'
        } else if (response.status === 500) {
          errorMessage = errorData.detail || 'Server error during upload. Please try again or contact support.'
        } else if (response.status === 0 || !response.status) {
          errorMessage = 'Network error. Please check your connection and try again.'
        }
        
        throw new Error(errorMessage)
      }

      const data = await response.json()
      setUploadResult(data.result)
      
      if (data.result && data.result.success !== false) {
        const rowsInserted = data.result.rows_inserted || 0
        
        // Set a flag in sessionStorage to indicate we need to refresh dashboard
        // This will be picked up by the dashboard to bypass cache
        sessionStorage.setItem('data_uploaded', 'true')
        sessionStorage.setItem('upload_timestamp', Date.now().toString())
        
        toast.success(`Successfully uploaded! ${rowsInserted} rows inserted`, {
          duration: 5000,
          action: {
            label: 'View Dashboard',
            onClick: () => {
              // Navigate to dashboard with refresh flag to bypass cache
              window.location.href = '/dashboard?refresh=true&_t=' + Date.now()
            }
          }
        })
        
        // Auto-navigate to dashboard after a short delay to show new data
        setTimeout(() => {
          toast.info('Redirecting to dashboard to view your transactions...', {
            duration: 3000
          })
          setTimeout(() => {
            window.location.href = '/dashboard?refresh=true&_t=' + Date.now()
          }, 1000)
        }, 2000)
      } else {
        toast.warning(`Upload completed with ${data.result?.rows_failed || 0} errors`)
      }
      
      setFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error: any) {
      console.error('Upload error:', error)
      const errorMessage = error.message || 'Failed to upload file. Please check the file format and try again.'
      
      // Show detailed error message
      toast.error(errorMessage, {
        duration: 6000,
        description: 'Check the browser console for more details'
      })
      
      // Also log additional context
      console.error('Full upload error context:', {
        error: error.message,
        stack: error.stack,
        file: file?.name,
        fileSize: file?.size,
        fileType: file?.type
      })
    } finally {
      setLoading(false)
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p>Please log in to upload data.</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Upload Transaction Data
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">
          Bulk upload historical transaction data via CSV or Excel
        </p>

        {/* Template Download */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 mb-8">
          <div className="flex items-start space-x-4">
            <AlertCircle className="w-6 h-6 text-blue-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-bold text-blue-900 dark:text-blue-100 mb-2">
                First time uploading?
              </h3>
              <p className="text-sm text-blue-800 dark:text-blue-200 mb-4">
                Download our template to see the required format for your data
              </p>
              <button
                onClick={downloadTemplate}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
              >
                <Download className="w-4 h-4" />
                <span>Download CSV Template</span>
              </button>
            </div>
          </div>
        </div>

        {/* File Upload */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
            Select File
          </h2>

          <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-12 text-center">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer flex flex-col items-center"
            >
              <Upload className="w-16 h-16 text-gray-400 mb-4" />
              <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Click to upload or drag and drop
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                CSV, XLSX, or XLS (up to 50MB)
              </p>
            </label>
          </div>

          {file && (
            <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <FileText className="w-8 h-8 text-blue-600" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {file.name}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {(file.size / 1024).toFixed(2)} KB
                  </p>
                </div>
              </div>
              <button
                onClick={() => setFile(null)}
                className="text-red-600 hover:text-red-700"
              >
                Remove
              </button>
            </div>
          )}

          <button
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              e.nativeEvent?.stopImmediatePropagation?.()
              
              console.log('🔵 Button onClick triggered', { 
                hasFile: !!file, 
                loading, 
                file: file?.name,
                uploadFileFunction: typeof uploadFile
              })
              
              // Verify uploadFile function exists
              if (typeof uploadFile !== 'function') {
                console.error('❌ uploadFile is not a function!', uploadFile)
                toast.error('Upload function error. Please refresh the page.')
                return
              }
              
              // Double check file exists
              if (!file) {
                console.warn('⚠️ No file selected when button clicked')
                toast.error('Please select a file first')
                return
              }
              
              // Prevent double-click
              if (loading) {
                console.warn('⚠️ Upload already in progress')
                return
              }
              
              try {
                uploadFile()
              } catch (error: any) {
                console.error('❌ Error calling uploadFile:', error)
                toast.error(`Failed to start upload: ${error.message || 'Unknown error'}`)
              }
            }}
            disabled={!file || loading}
            className="w-full mt-6 py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            type="button"
            aria-label="Upload file"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Uploading...
              </span>
            ) : !file ? (
              'Please Select a File First'
            ) : (
              'Upload File'
            )}
          </button>
          
          {!file && (
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400 text-center">
              Select a file above to enable upload
            </p>
          )}
        </div>

        {/* Upload Result */}
        {uploadResult && (
          <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-6">
              Upload Results
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <FileText className="w-5 h-5 text-blue-600" />
                  <span className="font-medium text-blue-900 dark:text-blue-100">
                    Total Rows
                  </span>
                </div>
                <p className="text-3xl font-bold text-blue-900 dark:text-blue-100">
                  {uploadResult.rows_processed}
                </p>
              </div>

              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="font-medium text-green-900 dark:text-green-100">
                    Inserted
                  </span>
                </div>
                <p className="text-3xl font-bold text-green-900 dark:text-green-100">
                  {uploadResult.rows_inserted}
                </p>
              </div>

              <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <XCircle className="w-5 h-5 text-red-600" />
                  <span className="font-medium text-red-900 dark:text-red-100">
                    Failed
                  </span>
                </div>
                <p className="text-3xl font-bold text-red-900 dark:text-red-100">
                  {uploadResult.rows_failed}
                </p>
              </div>
            </div>

            {uploadResult.errors && uploadResult.errors.length > 0 && (
              <div className="mt-6">
                <h3 className="font-bold text-red-900 dark:text-red-100 mb-3">
                  Errors (first 10):
                </h3>
                <div className="space-y-2">
                  {uploadResult.errors.map((error: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm"
                    >
                      <span className="font-medium text-red-900 dark:text-red-100">
                        Row {error.row}:
                      </span>{' '}
                      <span className="text-red-800 dark:text-red-200">
                        {error.error}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Required Columns Info */}
        <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Required Columns
          </h2>
          <div className="space-y-2">
            {[
              { name: 'account_id', desc: 'Customer account identifier' },
              { name: 'amount', desc: 'Transaction amount (numeric)' },
              { name: 'merchant', desc: 'Merchant name' },
              { name: 'transaction_date', desc: 'Transaction timestamp (YYYY-MM-DD HH:MM:SS)' }
            ].map((col) => (
              <div key={col.name} className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-700 rounded">
                <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                <div>
                  <code className="text-sm font-mono text-blue-600 dark:text-blue-400">
                    {col.name}
                  </code>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {col.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
          <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
            <strong>Optional columns:</strong> currency, mcc, channel, city, country, device_id
          </p>
        </div>
      </div>
    </div>
  )
}

