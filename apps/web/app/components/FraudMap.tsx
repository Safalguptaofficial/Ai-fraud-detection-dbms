'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { MapPin, TrendingUp, AlertTriangle } from 'lucide-react'

// Dynamic import to avoid SSR issues with Leaflet
const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
)
const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
)
const CircleMarker = dynamic(
  () => import('react-leaflet').then((mod) => mod.CircleMarker),
  { ssr: false }
)
const Popup = dynamic(
  () => import('react-leaflet').then((mod) => mod.Popup),
  { ssr: false }
)

interface FraudLocation {
  id: number
  lat: number
  lon: number
  city: string
  country: string
  count: number
  totalAmount: number
  severity: 'HIGH' | 'MEDIUM' | 'LOW'
  recentAlert?: {
    id: number
    rule_code: string
    created_at: string
  }
}

export function FraudMap() {
  const [fraudLocations, setFraudLocations] = useState<FraudLocation[]>([])
  const [selectedLocation, setSelectedLocation] = useState<FraudLocation | null>(null)
  const [mapReady, setMapReady] = useState(false)

  useEffect(() => {
    // Load Leaflet CSS
    if (typeof window !== 'undefined') {
      import('leaflet/dist/leaflet.css')
      setMapReady(true)
    }

    // Generate sample fraud locations (in production, fetch from API)
    const locations: FraudLocation[] = [
      {
        id: 1,
        lat: 40.7128,
        lon: -74.0060,
        city: 'New York',
        country: 'USA',
        count: 45,
        totalAmount: 125000,
        severity: 'HIGH',
        recentAlert: { id: 1, rule_code: 'MIDNIGHT_HIGH', created_at: new Date().toISOString() }
      },
      {
        id: 2,
        lat: 34.0522,
        lon: -118.2437,
        city: 'Los Angeles',
        country: 'USA',
        count: 32,
        totalAmount: 89000,
        severity: 'MEDIUM'
      },
      {
        id: 3,
        lat: 51.5074,
        lon: -0.1278,
        city: 'London',
        country: 'UK',
        count: 28,
        totalAmount: 76000,
        severity: 'MEDIUM'
      },
      {
        id: 4,
        lat: 35.6762,
        lon: 139.6503,
        city: 'Tokyo',
        country: 'Japan',
        count: 15,
        totalAmount: 45000,
        severity: 'LOW'
      },
      {
        id: 5,
        lat: 48.8566,
        lon: 2.3522,
        city: 'Paris',
        country: 'France',
        count: 22,
        totalAmount: 58000,
        severity: 'MEDIUM'
      },
      {
        id: 6,
        lat: -23.5505,
        lon: -46.6333,
        city: 'São Paulo',
        country: 'Brazil',
        count: 38,
        totalAmount: 95000,
        severity: 'HIGH'
      },
      {
        id: 7,
        lat: 55.7558,
        lon: 37.6173,
        city: 'Moscow',
        country: 'Russia',
        count: 12,
        totalAmount: 32000,
        severity: 'LOW'
      },
      {
        id: 8,
        lat: 1.3521,
        lon: 103.8198,
        city: 'Singapore',
        country: 'Singapore',
        count: 18,
        totalAmount: 52000,
        severity: 'MEDIUM'
      },
      {
        id: 9,
        lat: 19.4326,
        lon: -99.1332,
        city: 'Mexico City',
        country: 'Mexico',
        count: 41,
        totalAmount: 108000,
        severity: 'HIGH'
      },
      {
        id: 10,
        lat: -33.8688,
        lon: 151.2093,
        city: 'Sydney',
        country: 'Australia',
        count: 14,
        totalAmount: 38000,
        severity: 'LOW'
      }
    ]

    setFraudLocations(locations)
  }, [])

  const getColorBySeverity = (severity: string) => {
    switch (severity) {
      case 'HIGH': return '#ef4444' // red
      case 'MEDIUM': return '#f59e0b' // orange
      case 'LOW': return '#10b981' // green
      default: return '#6b7280' // gray
    }
  }

  const getRadiusByCount = (count: number) => {
    return Math.min(Math.max(count / 2, 8), 30)
  }

  if (!mapReady) {
    return (
      <div className="bg-white rounded-lg shadow p-6 h-96 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading map...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
          <MapPin className="w-6 h-6 text-blue-600" />
          Global Fraud Activity Map
        </h2>
        <p className="text-sm text-gray-600 mt-1">Real-time fraud incidents by location</p>
      </div>

      <div className="p-6">
        {/* Map Legend */}
        <div className="mb-4 flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500"></div>
            <span className="text-gray-700">High Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-orange-500"></div>
            <span className="text-gray-700">Medium Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span className="text-gray-700">Low Risk</span>
          </div>
          <div className="ml-auto text-gray-600">
            Circle size = fraud volume
          </div>
        </div>

        {/* Map */}
        <div className="h-96 rounded-lg overflow-hidden border border-gray-200">
          <MapContainer
            center={[20, 0]}
            zoom={2}
            style={{ height: '100%', width: '100%' }}
            scrollWheelZoom={true}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            
            {fraudLocations.map((location) => (
              <CircleMarker
                key={location.id}
                center={[location.lat, location.lon]}
                radius={getRadiusByCount(location.count)}
                pathOptions={{
                  fillColor: getColorBySeverity(location.severity),
                  fillOpacity: 0.6,
                  color: getColorBySeverity(location.severity),
                  weight: 2,
                  opacity: 0.8
                }}
                eventHandlers={{
                  click: () => setSelectedLocation(location)
                }}
              >
                <Popup>
                  <div className="min-w-[200px]">
                    <h3 className="font-semibold text-lg mb-2">{location.city}, {location.country}</h3>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Fraud Incidents:</span>
                        <span className="font-semibold">{location.count}</span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total Amount:</span>
                        <span className="font-semibold">${location.totalAmount.toLocaleString()}</span>
                      </div>
                      
                      <div className="flex justify-between">
                        <span className="text-gray-600">Risk Level:</span>
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          location.severity === 'HIGH' ? 'bg-red-100 text-red-800' :
                          location.severity === 'MEDIUM' ? 'bg-orange-100 text-orange-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {location.severity}
                        </span>
                      </div>

                      {location.recentAlert && (
                        <div className="pt-2 border-t border-gray-200 mt-2">
                          <p className="text-xs text-gray-600">Recent Alert:</p>
                          <p className="text-xs font-medium">{location.recentAlert.rule_code}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>

        {/* Stats */}
        <div className="mt-6 grid grid-cols-3 gap-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              <span className="text-sm font-medium text-red-900">High Risk Zones</span>
            </div>
            <p className="text-2xl font-bold text-red-600">
              {fraudLocations.filter(l => l.severity === 'HIGH').length}
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <MapPin className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-blue-900">Total Locations</span>
            </div>
            <p className="text-2xl font-bold text-blue-600">{fraudLocations.length}</p>
          </div>

          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-purple-600" />
              <span className="text-sm font-medium text-purple-900">Total Incidents</span>
            </div>
            <p className="text-2xl font-bold text-purple-600">
              {fraudLocations.reduce((sum, l) => sum + l.count, 0)}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

