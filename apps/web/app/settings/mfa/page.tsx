'use client'

import { useState, useEffect } from 'react'
import { useAuth, getAuthHeaders } from '../../utils/auth'
import { Shield, Key, Download, Check, X, AlertTriangle } from 'lucide-react'
import { toast } from 'sonner'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function MFASetupPage() {
  const { isAuthenticated } = useAuth()
  const [loading, setLoading] = useState(false)
  const [mfaEnabled, setMfaEnabled] = useState(false)
  const [qrCode, setQrCode] = useState('')
  const [secret, setSecret] = useState('')
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [verificationCode, setVerificationCode] = useState('')
  const [step, setStep] = useState<'check' | 'setup' | 'verify' | 'complete'>('check')

  useEffect(() => {
    checkMFAStatus()
  }, [])

  const checkMFAStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/mfa/status`, {
        headers: getAuthHeaders()
      })
      const data = await response.json()
      
      if (data.enabled) {
        setMfaEnabled(true)
        setStep('complete')
      }
    } catch (error) {
      console.error('Failed to check MFA status:', error)
    }
  }

  const setupMFA = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/mfa/setup`, {
        method: 'POST',
        headers: getAuthHeaders()
      })

      if (!response.ok) throw new Error('MFA setup failed')

      const data = await response.json()
      setSecret(data.secret)
      setQrCode(data.qr_code)
      setBackupCodes(data.backup_codes)
      setStep('setup')
      toast.success('MFA setup initiated!')
    } catch (error: any) {
      toast.error('Failed to setup MFA: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const verifyMFA = async () => {
    if (verificationCode.length !== 6) {
      toast.error('Please enter a 6-digit code')
      return
    }

    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/mfa/verify`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token: verificationCode })
      })

      if (!response.ok) throw new Error('Invalid code')

      toast.success('MFA enabled successfully!')
      setMfaEnabled(true)
      setStep('complete')
    } catch (error: any) {
      toast.error('Invalid verification code')
    } finally {
      setLoading(false)
    }
  }

  const disableMFA = async () => {
    if (!confirm('Are you sure you want to disable MFA? This will make your account less secure.')) {
      return
    }

    const code = prompt('Enter your current MFA code to disable:')
    if (!code) return

    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/mfa/disable`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token: code })
      })

      if (!response.ok) throw new Error('Invalid code')

      toast.success('MFA disabled')
      setMfaEnabled(false)
      setStep('check')
    } catch (error: any) {
      toast.error('Failed to disable MFA')
    } finally {
      setLoading(false)
    }
  }

  const downloadBackupCodes = () => {
    const text = backupCodes.join('\n')
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'fraudguard-backup-codes.txt'
    a.click()
    toast.success('Backup codes downloaded')
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p>Please log in to access MFA settings.</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 mb-6">
          <div className="flex items-center space-x-4 mb-4">
            <Shield className="w-12 h-12 text-blue-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Two-Factor Authentication
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Add an extra layer of security to your account
              </p>
            </div>
          </div>

          {mfaEnabled && (
            <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <div className="flex items-center space-x-2">
                <Check className="w-5 h-5 text-green-600" />
                <span className="font-medium text-green-900 dark:text-green-100">
                  MFA is enabled on your account
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Step: Check Status */}
        {step === 'check' && !mfaEnabled && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
              Secure Your Account
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Two-factor authentication adds an extra layer of security by requiring a code
              from your phone in addition to your password.
            </p>

            <div className="space-y-4 mb-6">
              <div className="flex items-start space-x-3">
                <Check className="w-5 h-5 text-green-600 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    Works with Google Authenticator
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Compatible with Authy, Microsoft Authenticator, and other TOTP apps
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <Check className="w-5 h-5 text-green-600 mt-0.5" />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    Backup codes included
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Save backup codes to recover your account if you lose your phone
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={setupMFA}
              disabled={loading}
              className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg disabled:opacity-50"
            >
              {loading ? 'Setting up...' : 'Enable Two-Factor Authentication'}
            </button>
          </div>
        )}

        {/* Step: Setup (Show QR Code) */}
        {step === 'setup' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
              Scan QR Code
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Scan this QR code with your authenticator app:
            </p>

            {/* QR Code */}
            <div className="flex justify-center mb-6">
              <div className="bg-white p-4 rounded-lg border-2 border-gray-200">
                <img src={qrCode} alt="MFA QR Code" className="w-64 h-64" />
              </div>
            </div>

            {/* Manual Entry */}
            <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Can't scan? Enter this code manually:
              </p>
              <div className="flex items-center space-x-2">
                <code className="flex-1 p-2 bg-white dark:bg-gray-800 rounded border border-gray-300 dark:border-gray-600 font-mono text-sm">
                  {secret}
                </code>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(secret)
                    toast.success('Copied to clipboard!')
                  }}
                  className="px-3 py-2 bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 rounded"
                >
                  Copy
                </button>
              </div>
            </div>

            {/* Backup Codes */}
            <div className="mb-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <div className="flex items-start space-x-3 mb-3">
                <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div>
                  <p className="font-medium text-yellow-900 dark:text-yellow-100 mb-2">
                    Save your backup codes
                  </p>
                  <p className="text-sm text-yellow-800 dark:text-yellow-200">
                    Store these codes in a safe place. You can use them to access your account if you lose your phone.
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 mb-3">
                {backupCodes.map((code, idx) => (
                  <code key={idx} className="p-2 bg-white dark:bg-gray-800 rounded text-sm font-mono">
                    {code}
                  </code>
                ))}
              </div>
              <button
                onClick={downloadBackupCodes}
                className="flex items-center space-x-2 text-sm text-yellow-900 dark:text-yellow-100 hover:underline"
              >
                <Download className="w-4 h-4" />
                <span>Download backup codes</span>
              </button>
            </div>

            <button
              onClick={() => setStep('verify')}
              className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg"
            >
              Continue to Verification
            </button>
          </div>
        )}

        {/* Step: Verify */}
        {step === 'verify' && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
              Verify Setup
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Enter the 6-digit code from your authenticator app:
            </p>

            <input
              type="text"
              value={verificationCode}
              onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              className="w-full text-center text-3xl font-mono tracking-widest p-4 border-2 border-gray-300 dark:border-gray-600 rounded-lg mb-6 dark:bg-gray-700 dark:text-white"
              maxLength={6}
            />

            <div className="space-y-3">
              <button
                onClick={verifyMFA}
                disabled={loading || verificationCode.length !== 6}
                className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg disabled:opacity-50"
              >
                {loading ? 'Verifying...' : 'Verify and Enable MFA'}
              </button>
              <button
                onClick={() => setStep('setup')}
                className="w-full py-3 px-4 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white font-semibold rounded-lg"
              >
                Back to QR Code
              </button>
            </div>
          </div>
        )}

        {/* Step: Complete */}
        {step === 'complete' && mfaEnabled && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900/20 rounded-full mb-4">
                <Check className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold mb-2 text-gray-900 dark:text-white">
                MFA is Enabled!
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                Your account is now protected with two-factor authentication
              </p>
            </div>

            <div className="space-y-4">
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <p className="text-sm text-blue-900 dark:text-blue-100">
                  <strong>Next time you log in:</strong> You'll need to enter a code from your authenticator app in addition to your password.
                </p>
              </div>

              <button
                onClick={disableMFA}
                disabled={loading}
                className="w-full py-3 px-4 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg disabled:opacity-50"
              >
                {loading ? 'Disabling...' : 'Disable Two-Factor Authentication'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

