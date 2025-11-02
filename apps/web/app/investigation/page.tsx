'use client'

import { useState, useEffect } from 'react'
import { FileCheck, Plus, Clock, User, Paperclip, MessageSquare, Eye, Edit2, Trash2, CheckCircle, XCircle } from 'lucide-react'
import { toast } from 'sonner'

interface TimelineEvent {
  id: number
  timestamp: string
  type: 'alert' | 'action' | 'note' | 'evidence'
  description: string
  user: string
  metadata?: any
}

interface Evidence {
  id: number
  name: string
  type: string
  size: string
  uploadedBy: string
  uploadedAt: string
  url?: string
}

interface Investigation {
  id: number
  caseId: string
  title: string
  status: 'open' | 'in_progress' | 'completed' | 'closed'
  priority: 'high' | 'medium' | 'low'
  assignee: string
  created_at: string
  updated_at: string
  timeline: TimelineEvent[]
  evidence: Evidence[]
  notes: string
}

export default function InvestigationPage() {
  const [investigations, setInvestigations] = useState<Investigation[]>([])
  const [selectedInvestigation, setSelectedInvestigation] = useState<Investigation | null>(null)
  const [loading, setLoading] = useState(true)
  const [newNote, setNewNote] = useState('')
  const [newEventDescription, setNewEventDescription] = useState('')

  useEffect(() => {
    fetchInvestigations()
  }, [])

  const fetchInvestigations = async () => {
    setLoading(true)
    try {
      // Try to fetch from real API first
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const token = localStorage.getItem('auth_token')
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      } else {
        headers['X-API-Key'] = 'fgk_live_demo_api_key_12345'
      }

      const response = await fetch(`${API_URL}/v1/cases`, { headers })
      
      if (response.ok) {
        const casesData = await response.json()
        // Transform API data to match Investigation interface
        const transformedCases: Investigation[] = casesData.map((caseItem: any) => ({
          id: caseItem.id || Math.random(),
          caseId: caseItem.caseId || `CASE-${caseItem.id}`,
          title: `Case ${caseItem.caseId} - Account ${caseItem.accountId}`,
          status: caseItem.status?.toLowerCase() || 'open',
          priority: caseItem.priority || 'medium',
          assignee: caseItem.investigator || 'Unassigned',
          created_at: caseItem.createdAt || new Date().toISOString(),
          updated_at: caseItem.updatedAt || new Date().toISOString(),
          timeline: (caseItem.notes || []).map((note: any, idx: number) => ({
            id: idx + 1,
            timestamp: note.createdAt || new Date().toISOString(),
            type: 'note' as const,
            description: note.content,
            user: note.author || 'System'
          })),
          evidence: (caseItem.attachments || []).map((att: any, idx: number) => ({
            id: idx + 1,
            name: att.filename || 'attachment',
            type: att.contentType?.split('/')[1]?.toUpperCase() || 'FILE',
            size: 'N/A',
            uploadedBy: 'System',
            uploadedAt: new Date().toISOString()
          })),
          notes: (caseItem.notes || []).map((n: any) => n.content).join('\n')
        }))
        setInvestigations(transformedCases)
        setLoading(false)
        return
      }
    } catch (error) {
      console.error('Failed to fetch investigations from API:', error)
    }

    // Fallback to mock data if API fails
    const mockData: Investigation[] = [
      {
        id: 1,
        caseId: 'INV-2025-001',
        title: 'Suspicious Velocity Pattern - Account A101',
        status: 'in_progress',
        priority: 'high',
        assignee: 'Jane Analyst',
        created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date().toISOString(),
        timeline: [
          {
            id: 1,
            timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
            type: 'alert',
            description: 'High-risk velocity alert triggered',
            user: 'System',
            metadata: { rule: 'VELOCITY_CHECK', severity: 'HIGH' }
          },
          {
            id: 2,
            timestamp: new Date(Date.now() - 1.5 * 24 * 60 * 60 * 1000).toISOString(),
            type: 'action',
            description: 'Investigation assigned to Jane Analyst',
            user: 'John Manager'
          },
          {
            id: 3,
            timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
            type: 'note',
            description: 'Account shows 15 transactions in 10 minutes. Reviewing transaction patterns.',
            user: 'Jane Analyst'
          },
          {
            id: 4,
            timestamp: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
            type: 'evidence',
            description: 'Added transaction logs and IP address records',
            user: 'Jane Analyst'
          }
        ],
        evidence: [
          {
            id: 1,
            name: 'transaction_logs_A101.csv',
            type: 'CSV',
            size: '245 KB',
            uploadedBy: 'Jane Analyst',
            uploadedAt: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString()
          },
          {
            id: 2,
            name: 'ip_analysis.pdf',
            type: 'PDF',
            size: '1.2 MB',
            uploadedBy: 'Jane Analyst',
            uploadedAt: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString()
          }
        ],
        notes: 'Account A101 shows suspicious velocity pattern. Further investigation required to confirm if legitimate or fraudulent.'
      },
      {
        id: 2,
        caseId: 'INV-2025-002',
        title: 'Large Transaction - Unusual Merchant',
        status: 'open',
        priority: 'medium',
        assignee: 'Unassigned',
        created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        timeline: [
          {
            id: 1,
            timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
            type: 'alert',
            description: 'Large amount transaction detected',
            user: 'System',
            metadata: { amount: 12500, merchant: 'Unknown Merchant X' }
          }
        ],
        evidence: [],
        notes: ''
      }
    ]

    setInvestigations(mockData)
    if (mockData.length > 0) {
      setSelectedInvestigation(mockData[0])
    }
    setLoading(false)
  }

  const addTimelineEvent = () => {
    if (!newEventDescription || !selectedInvestigation) return

    const newEvent: TimelineEvent = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      type: 'action',
      description: newEventDescription,
      user: 'Current User'
    }

    const updated = {
      ...selectedInvestigation,
      timeline: [...selectedInvestigation.timeline, newEvent],
      updated_at: new Date().toISOString()
    }

    setSelectedInvestigation(updated)
    setInvestigations(investigations.map(inv => 
      inv.id === selectedInvestigation.id ? updated : inv
    ))
    setNewEventDescription('')
  }

  const updateStatus = (status: Investigation['status']) => {
    if (!selectedInvestigation) return

    const updated = {
      ...selectedInvestigation,
      status,
      updated_at: new Date().toISOString()
    }

    setSelectedInvestigation(updated)
    setInvestigations(investigations.map(inv => 
      inv.id === selectedInvestigation.id ? updated : inv
    ))
  }

  const saveNotes = () => {
    if (!selectedInvestigation) return

    const updated = {
      ...selectedInvestigation,
      notes: newNote,
      updated_at: new Date().toISOString()
    }

    setSelectedInvestigation(updated)
    setInvestigations(investigations.map(inv => 
      inv.id === selectedInvestigation.id ? updated : inv
    ))
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
      case 'in_progress':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
      case 'completed':
        return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
      case 'closed':
        return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
      case 'medium':
        return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
      case 'low':
        return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
    }
  }

  const getTimelineIcon = (type: string) => {
    switch (type) {
      case 'alert':
        return <div className="w-8 h-8 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-full flex items-center justify-center">🚨</div>
      case 'action':
        return <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full flex items-center justify-center"><CheckCircle className="w-4 h-4" /></div>
      case 'note':
        return <div className="w-8 h-8 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded-full flex items-center justify-center"><MessageSquare className="w-4 h-4" /></div>
      case 'evidence':
        return <div className="w-8 h-8 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full flex items-center justify-center"><Paperclip className="w-4 h-4" /></div>
      default:
        return <div className="w-8 h-8 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full flex items-center justify-center">•</div>
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-300">Loading investigations...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <FileCheck className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            Investigation Workspace
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Collaborative investigation management with timeline, evidence, and notes
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Investigations List */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Investigations</h2>
                <button 
                  onClick={() => {
                    // Navigate to cases page to create new investigation
                    window.location.href = '/cases'
                  }}
                  className="p-2 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-colors"
                  title="Create New Investigation"
                >
                  <Plus className="w-5 h-5" />
                </button>
              </div>
              
              <div className="space-y-3">
                {investigations.map((inv) => (
                  <div
                    key={inv.id}
                    onClick={() => setSelectedInvestigation(inv)}
                    className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                      selectedInvestigation?.id === inv.id
                        ? 'border-blue-500 dark:border-blue-400 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <span className="text-xs font-mono text-gray-500 dark:text-gray-400">{inv.caseId}</span>
                      <span className={`px-2 py-1 text-xs rounded ${getPriorityColor(inv.priority)}`}>
                        {inv.priority.toUpperCase()}
                      </span>
                    </div>
                    <h3 className="font-medium text-gray-900 dark:text-white text-sm mb-2">{inv.title}</h3>
                    <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
                      <span className={`px-2 py-1 rounded ${getStatusColor(inv.status)}`}>
                        {inv.status.replace('_', ' ')}
                      </span>
                      <span>•</span>
                      <User className="w-3 h-3" />
                      <span>{inv.assignee}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Investigation Details */}
          {selectedInvestigation && (
            <div className="lg:col-span-2 space-y-6">
              {/* Header */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <span className="text-sm font-mono text-gray-500 dark:text-gray-400">{selectedInvestigation.caseId}</span>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{selectedInvestigation.title}</h2>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => updateStatus('in_progress')}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        selectedInvestigation.status === 'in_progress'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      In Progress
                    </button>
                    <button
                      onClick={() => updateStatus('completed')}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        selectedInvestigation.status === 'completed'
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      <CheckCircle className="w-4 h-4 inline mr-1" />
                      Complete
                    </button>
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Status</span>
                    <p className="font-medium text-gray-900 dark:text-white capitalize">{selectedInvestigation.status.replace('_', ' ')}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Priority</span>
                    <p className="font-medium text-gray-900 dark:text-white capitalize">{selectedInvestigation.priority}</p>
                  </div>
                  <div>
                    <span className="text-gray-500 dark:text-gray-400">Assignee</span>
                    <p className="font-medium text-gray-900 dark:text-white">{selectedInvestigation.assignee}</p>
                  </div>
                </div>
              </div>

              {/* Timeline */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  Investigation Timeline
                </h3>
                
                <div className="space-y-4 mb-6">
                  {selectedInvestigation.timeline.map((event) => (
                    <div key={event.id} className="flex gap-4">
                      {getTimelineIcon(event.type)}
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-gray-900 dark:text-white">{event.description}</span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {new Date(event.timestamp).toLocaleDateString()} {new Date(event.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-xs text-gray-600 dark:text-gray-400">by {event.user}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newEventDescription}
                    onChange={(e) => setNewEventDescription(e.target.value)}
                    placeholder="Add timeline event..."
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    onKeyPress={(e) => e.key === 'Enter' && addTimelineEvent()}
                  />
                  <button
                    onClick={addTimelineEvent}
                    className="px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 transition-colors"
                  >
                    Add
                  </button>
                </div>
              </div>

              {/* Evidence */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <Paperclip className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  Evidence ({selectedInvestigation.evidence.length})
                </h3>
                
                {selectedInvestigation.evidence.length > 0 ? (
                  <div className="space-y-3">
                    {selectedInvestigation.evidence.map((item) => (
                      <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded flex items-center justify-center font-bold text-sm">
                            {item.type}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-white text-sm">{item.name}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {item.size} • Uploaded by {item.uploadedBy}
                            </p>
                          </div>
                        </div>
                        <button 
                          onClick={() => {
                            // In production, this would open the file or download it
                            toast.info(`Viewing ${item.name} (would open file in production)`)
                          }}
                          className="p-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                          title={`View ${item.name}`}
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    <Paperclip className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>No evidence uploaded yet</p>
                  </div>
                )}
                
                <button 
                  onClick={() => {
                    // In production, this would open a file upload dialog
                    toast.info('Evidence upload feature (would open file dialog in production)')
                  }}
                  className="w-full mt-4 px-4 py-2 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-gray-600 dark:text-gray-400 hover:border-blue-500 dark:hover:border-blue-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                >
                  <Plus className="w-4 h-4 inline mr-2" />
                  Upload Evidence
                </button>
              </div>

              {/* Notes */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  Investigation Notes
                </h3>
                
                <textarea
                  value={newNote || selectedInvestigation.notes}
                  onChange={(e) => setNewNote(e.target.value)}
                  className="w-full h-32 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white resize-none"
                  placeholder="Add investigation notes, findings, or observations..."
                />
                
                <div className="flex justify-end mt-3">
                  <button
                    onClick={saveNotes}
                    className="px-6 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 transition-colors"
                  >
                    Save Notes
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

