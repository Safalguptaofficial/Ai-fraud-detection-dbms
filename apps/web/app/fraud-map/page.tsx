'use client'

import { FraudMap } from '../components/FraudMap'
import { useAuth } from '../utils/auth'
import { MapPin, Shield, TrendingUp, Activity } from 'lucide-react'

export default function FraudMapPage() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading map...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <MapPin className="w-10 h-10 text-blue-600" />
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
              Global Fraud Map
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-300 text-lg">
            Real-time visualization of fraud incidents worldwide
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gradient-to-br from-red-500 to-red-600 p-6 rounded-xl shadow-lg text-white">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium opacity-90">High Risk Zones</h3>
              <Shield className="w-5 h-5 opacity-75" />
            </div>
            <p className="text-4xl font-bold">3</p>
            <p className="text-xs opacity-75 mt-1">Active hotspots</p>
          </div>

          <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-6 rounded-xl shadow-lg text-white">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium opacity-90">Monitored Locations</h3>
              <MapPin className="w-5 h-5 opacity-75" />
            </div>
            <p className="text-4xl font-bold">10</p>
            <p className="text-xs opacity-75 mt-1">Global coverage</p>
          </div>

          <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-6 rounded-xl shadow-lg text-white">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium opacity-90">Total Incidents</h3>
              <Activity className="w-5 h-5 opacity-75" />
            </div>
            <p className="text-4xl font-bold">265</p>
            <p className="text-xs opacity-75 mt-1">Last 24 hours</p>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-xl shadow-lg text-white">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium opacity-90">Detection Rate</h3>
              <TrendingUp className="w-5 h-5 opacity-75" />
            </div>
            <p className="text-4xl font-bold">96.2%</p>
            <p className="text-xs opacity-75 mt-1">Accuracy</p>
          </div>
        </div>

        {/* Map Component */}
        <FraudMap />

        {/* Additional Info */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">
            💡 How to Use the Map
          </h3>
          <ul className="space-y-2 text-blue-800 text-sm">
            <li className="flex items-start gap-2">
              <span>•</span>
              <span><strong>Click on circles</strong> to view detailed fraud statistics for that location</span>
            </li>
            <li className="flex items-start gap-2">
              <span>•</span>
              <span><strong>Circle size</strong> represents the volume of fraud incidents</span>
            </li>
            <li className="flex items-start gap-2">
              <span>•</span>
              <span><strong>Circle color</strong> indicates risk level (Red = High, Orange = Medium, Green = Low)</span>
            </li>
            <li className="flex items-start gap-2">
              <span>•</span>
              <span><strong>Zoom and pan</strong> to explore different regions</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}

