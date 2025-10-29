'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { LayoutDashboard, FileText, Database, TrendingUp, MapPin, Network, Users, FileCheck, Brain, Menu, X, ChevronDown } from 'lucide-react'
import { NotificationCenter } from './NotificationCenter'
import { ThemeToggle } from './ThemeToggle'

const navItems = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', group: 'main' },
  { href: '/dashboard-enhanced', icon: TrendingUp, label: 'Analytics', group: 'main' },
  { href: '/ml-model', icon: Brain, label: 'ML Model', group: 'advanced' },
  { href: '/network-graph', icon: Network, label: 'Network', group: 'advanced' },
  { href: '/fraud-map', icon: MapPin, label: 'Map', group: 'advanced' },
  { href: '/cases', icon: FileText, label: 'Cases', group: 'management' },
  { href: '/investigation', icon: FileCheck, label: 'Investigations', group: 'management' },
  { href: '/rbac', icon: Users, label: 'Users', group: 'admin' },
  { href: '/crud-monitor', icon: Database, label: 'Monitor', group: 'admin' },
]

export function Navigation() {
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [advancedOpen, setAdvancedOpen] = useState(false)

  return (
    <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm transition-colors sticky top-0 z-40">
      <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex-shrink-0 flex items-center">
            <Link href="/dashboard" className="text-xl lg:text-2xl font-bold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-500 transition-colors">
              🛡️ FraudGuard
            </Link>
          </div>

          {/* Desktop Navigation - Compact */}
          <div className="hidden xl:flex items-center space-x-1 flex-1 justify-center max-w-4xl">
            {/* Main Items */}
            {navItems.filter(item => item.group === 'main').map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-1.5" />
                  {item.label}
                </Link>
              )
            })}

            {/* Advanced Dropdown */}
            <div className="relative">
              <button
                onClick={() => setAdvancedOpen(!advancedOpen)}
                className="inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                <Brain className="w-4 h-4 mr-1.5" />
                Advanced
                <ChevronDown className={`w-3 h-3 ml-1 transition-transform ${advancedOpen ? 'rotate-180' : ''}`} />
              </button>
              
              {advancedOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setAdvancedOpen(false)} />
                  <div className="absolute left-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-20">
                    {navItems.filter(item => item.group === 'advanced').map((item) => {
                      const Icon = item.icon
                      const isActive = pathname === item.href
                      return (
                        <Link
                          key={item.href}
                          href={item.href}
                          onClick={() => setAdvancedOpen(false)}
                          className={`flex items-center px-4 py-2 text-sm ${
                            isActive
                              ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                          }`}
                        >
                          <Icon className="w-4 h-4 mr-2" />
                          {item.label}
                        </Link>
                      )
                    })}
                  </div>
                </>
              )}
            </div>

            {/* Management Items */}
            {navItems.filter(item => item.group === 'management').map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-1.5" />
                  {item.label}
                </Link>
              )
            })}

            {/* Admin Items */}
            {navItems.filter(item => item.group === 'admin').map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`inline-flex items-center px-2 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </Link>
              )
            })}
          </div>
          
          {/* Right side: Theme + Notifications */}
          <div className="flex items-center gap-2 sm:gap-4">
            <ThemeToggle />
            <NotificationCenter />
            
            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="xl:hidden p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="xl:hidden border-t border-gray-200 dark:border-gray-700 py-3 max-h-[70vh] overflow-y-auto">
            <div className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center px-4 py-3 text-base font-medium rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                        : 'text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    <Icon className="w-5 h-5 mr-3" />
                    {item.label}
                  </Link>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}

