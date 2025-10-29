'use client'

import { useEffect, useState } from 'react'
import { Bell, X, AlertTriangle, Info, CheckCircle } from 'lucide-react'
import { toast } from 'sonner'

interface Notification {
  id: string
  type: 'alert' | 'case' | 'system'
  severity: 'high' | 'medium' | 'low'
  title: string
  message: string
  timestamp: Date
  read: boolean
}

export function NotificationCenter() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [showPanel, setShowPanel] = useState(false)
  const [soundEnabled, setSoundEnabled] = useState(true)

  useEffect(() => {
    // Simulate real-time notifications
    const interval = setInterval(() => {
      if (Math.random() > 0.7) {
        const newNotification: Notification = {
          id: Date.now().toString(),
          type: ['alert', 'case', 'system'][Math.floor(Math.random() * 3)] as any,
          severity: ['high', 'medium', 'low'][Math.floor(Math.random() * 3)] as any,
          title: getRandomTitle(),
          message: getRandomMessage(),
          timestamp: new Date(),
          read: false
        }
        
        setNotifications(prev => [newNotification, ...prev].slice(0, 50))
        
        // Show toast notification
        const icon = getNotificationIcon(newNotification.severity)
        toast(newNotification.title, {
          description: newNotification.message,
          icon,
          duration: 5000,
        })
        
        // Play sound for high severity
        if (soundEnabled && newNotification.severity === 'high') {
          playNotificationSound()
        }
      }
    }, 10000) // Check every 10 seconds
    
    return () => clearInterval(interval)
  }, [soundEnabled])

  const getRandomTitle = () => {
    const titles = [
      '🚨 High-Risk Transaction Detected',
      '⚠️ New Fraud Alert',
      '📊 Analytics Update',
      '✅ Case Resolved',
      '🔔 System Update',
      '💳 Unusual Activity'
    ]
    return titles[Math.floor(Math.random() * titles.length)]
  }

  const getRandomMessage = () => {
    const messages = [
      'Account #1234 - $7,500 ATM withdrawal at 2:30 AM',
      'Geographic anomaly detected - NYC to LA in 1 hour',
      'Velocity alert - 10 transactions in 5 minutes',
      'Case #CASE-ABC123 has been resolved',
      'New fraud pattern identified in system',
      'Multiple failed login attempts detected'
    ]
    return messages[Math.floor(Math.random() * messages.length)]
  }

  const getNotificationIcon = (severity: string) => {
    switch (severity) {
      case 'high': return '🚨'
      case 'medium': return '⚠️'
      case 'low': return 'ℹ️'
      default: return '🔔'
    }
  }

  const playNotificationSound = () => {
    // Simple beep using Web Audio API
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const oscillator = audioContext.createOscillator()
      const gainNode = audioContext.createGain()
      
      oscillator.connect(gainNode)
      gainNode.connect(audioContext.destination)
      
      oscillator.frequency.value = 800
      oscillator.type = 'sine'
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5)
      
      oscillator.start(audioContext.currentTime)
      oscillator.stop(audioContext.currentTime + 0.5)
    } catch (error) {
      console.warn('Could not play notification sound:', error)
    }
  }

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    )
  }

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
  }

  const clearAll = () => {
    setNotifications([])
  }

  const unreadCount = notifications.filter(n => !n.read).length

  return (
    <div className="relative">
      {/* Notification Bell Button */}
      <button
        onClick={() => setShowPanel(!showPanel)}
        className="relative p-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors"
      >
        <Bell className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-600 dark:bg-red-700 rounded-full animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notification Panel */}
      {showPanel && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40"
            onClick={() => setShowPanel(false)}
          />
          
          {/* Panel */}
          <div className="absolute right-0 top-12 z-50 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 max-h-[600px] flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Notifications
                </h3>
                <button
                  onClick={() => setShowPanel(false)}
                  className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                >
                  <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                </button>
              </div>
              
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={soundEnabled}
                    onChange={(e) => setSoundEnabled(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-gray-700">Sound alerts</span>
                </label>
                
                <div className="flex gap-2">
                  <button
                    onClick={markAllAsRead}
                    className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                  >
                    Mark all read
                  </button>
                  <button
                    onClick={clearAll}
                    className="text-xs text-red-600 hover:text-red-800 font-medium"
                  >
                    Clear all
                  </button>
                </div>
              </div>
            </div>

            {/* Notifications List */}
            <div className="flex-1 overflow-y-auto">
              {notifications.length > 0 ? (
                <div className="divide-y divide-gray-200">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                        !notification.read ? 'bg-blue-50' : ''
                      }`}
                      onClick={() => markAsRead(notification.id)}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`p-2 rounded-full ${
                          notification.severity === 'high' ? 'bg-red-100 text-red-600' :
                          notification.severity === 'medium' ? 'bg-yellow-100 text-yellow-600' :
                          'bg-blue-100 text-blue-600'
                        }`}>
                          {notification.severity === 'high' ? <AlertTriangle className="w-4 h-4" /> :
                           notification.severity === 'medium' ? <Info className="w-4 h-4" /> :
                           <CheckCircle className="w-4 h-4" />}
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <p className="text-sm font-semibold text-gray-900 truncate">
                              {notification.title}
                            </p>
                            {!notification.read && (
                              <div className="w-2 h-2 bg-blue-600 rounded-full flex-shrink-0" />
                            )}
                          </div>
                          
                          <p className="text-xs text-gray-600 mb-1">
                            {notification.message}
                          </p>
                          
                          <p className="text-xs text-gray-400">
                            {notification.timestamp.toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12">
                  <Bell className="w-12 h-12 text-gray-300 mb-2" />
                  <p className="text-gray-500 text-sm">No notifications</p>
                  <p className="text-gray-400 text-xs mt-1">You're all caught up!</p>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

