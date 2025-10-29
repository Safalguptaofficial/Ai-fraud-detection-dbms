'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Command } from 'cmdk'
import {
  Search,
  LayoutDashboard,
  FileText,
  Database,
  TrendingUp,
  Bell,
  Download,
  Settings,
  LogOut,
  Plus,
  Filter,
  RefreshCw,
  Home,
  Map
} from 'lucide-react'
import './command-palette.css'

export function CommandPalette() {
  const [open, setOpen] = useState(false)
  const router = useRouter()

  // Toggle with Cmd+K or Ctrl+K
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }

    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  const navigate = (path: string) => {
    router.push(path)
    setOpen(false)
  }

  const commands = [
    {
      group: 'Navigation',
      items: [
        { icon: Home, label: 'Go to Home', shortcut: 'G then H', action: () => navigate('/') },
        { icon: LayoutDashboard, label: 'Go to Dashboard', shortcut: 'G then D', action: () => navigate('/dashboard') },
        { icon: TrendingUp, label: 'Go to Enhanced Analytics', shortcut: 'G then E', action: () => navigate('/dashboard-enhanced') },
        { icon: FileText, label: 'Go to Cases', shortcut: 'G then C', action: () => navigate('/cases') },
        { icon: Database, label: 'Go to CRUD Monitor', shortcut: 'G then M', action: () => navigate('/crud-monitor') },
        { icon: Map, label: 'View Fraud Map', shortcut: 'G then F', action: () => navigate('/fraud-map') },
      ]
    },
    {
      group: 'Actions',
      items: [
        { icon: Plus, label: 'Create New Case', shortcut: 'C', action: () => console.log('Create case') },
        { icon: Download, label: 'Export Data', shortcut: 'E', action: () => console.log('Export') },
        { icon: RefreshCw, label: 'Refresh Dashboard', shortcut: 'R', action: () => window.location.reload() },
        { icon: Filter, label: 'Open Filters', shortcut: 'F', action: () => console.log('Filters') },
        { icon: Bell, label: 'View Notifications', shortcut: 'N', action: () => console.log('Notifications') },
      ]
    },
    {
      group: 'Settings',
      items: [
        { icon: Settings, label: 'Preferences', shortcut: ',', action: () => console.log('Settings') },
        { icon: LogOut, label: 'Logout', shortcut: 'Q', action: () => navigate('/login') },
      ]
    }
  ]

  return (
    <>
      {/* Keyboard hint */}
      <div className="fixed bottom-4 right-4 bg-gray-900 text-white px-3 py-2 rounded-lg shadow-lg text-sm opacity-50 hover:opacity-100 transition-opacity">
        Press <kbd className="px-2 py-1 bg-gray-700 rounded text-xs mx-1">⌘K</kbd> for commands
      </div>

      <Command.Dialog open={open} onOpenChange={setOpen} label="Command Menu">
        <div className="command-palette">
          <div className="command-input-wrapper">
            <Search className="w-5 h-5 text-gray-400" />
            <Command.Input 
              placeholder="Type a command or search..." 
              className="command-input"
            />
          </div>

          <Command.List className="command-list">
            <Command.Empty className="command-empty">
              No results found.
            </Command.Empty>

            {commands.map((group) => (
              <Command.Group key={group.group} heading={group.group} className="command-group">
                {group.items.map((item) => {
                  const Icon = item.icon
                  return (
                    <Command.Item
                      key={item.label}
                      onSelect={item.action}
                      className="command-item"
                    >
                      <Icon className="w-5 h-5" />
                      <span className="flex-1">{item.label}</span>
                      {item.shortcut && (
                        <kbd className="command-kbd">{item.shortcut}</kbd>
                      )}
                    </Command.Item>
                  )
                })}
              </Command.Group>
            ))}
          </Command.List>

          <div className="command-footer">
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 rounded">↑↓</kbd> Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 rounded">Enter</kbd> Select
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-gray-100 rounded">Esc</kbd> Close
              </span>
            </div>
          </div>
        </div>
      </Command.Dialog>
    </>
  )
}

