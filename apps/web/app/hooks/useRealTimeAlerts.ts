'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'

interface RealTimeAlert {
  id: number
  type: string
  severity: 'HIGH' | 'MEDIUM' | 'LOW'
  title: string
  message: string
  account_id: number
  timestamp: string
  rule_code: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function useRealTimeAlerts() {
  const [alerts, setAlerts] = useState<RealTimeAlert[]>([])
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    // Create EventSource for Server-Sent Events
    const eventSource = new EventSource(`${API_URL}/v1/realtime/alerts`)

    eventSource.onopen = () => {
      console.log('✅ Real-time alerts connected')
      setIsConnected(true)
    }

    eventSource.onmessage = (event) => {
      try {
        const alert: RealTimeAlert = JSON.parse(event.data)
        console.log('🔔 New alert received:', alert)
        
        // Add to alerts list
        setAlerts(prev => [alert, ...prev].slice(0, 50))
        
        // Show toast notification
        const icon = alert.severity === 'HIGH' ? '🚨' : 
                     alert.severity === 'MEDIUM' ? '⚠️' : 'ℹ️'
        
        toast(alert.title, {
          description: alert.message,
          icon,
          duration: 5000,
        })
        
        // Play sound for high severity
        if (alert.severity === 'HIGH') {
          playNotificationSound()
        }
      } catch (error) {
        console.error('Error parsing alert:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('❌ EventSource error:', error)
      setIsConnected(false)
      eventSource.close()
      
      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        console.log('🔄 Attempting to reconnect...')
        window.location.reload()
      }, 5000)
    }

    return () => {
      console.log('🔌 Disconnecting real-time alerts')
      eventSource.close()
    }
  }, [])

  const playNotificationSound = () => {
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

  return { alerts, isConnected }
}

