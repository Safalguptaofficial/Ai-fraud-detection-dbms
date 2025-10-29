'use client'

import { useState } from 'react'
import { Check, X, User, Mail, Trash2, Download } from 'lucide-react'
import { toast } from 'sonner'

interface BulkActionsProps {
  selectedIds: number[]
  onClearSelection: () => void
  onBulkUpdate: (action: string, value?: string) => void
}

export function BulkActions({ selectedIds, onClearSelection, onBulkUpdate }: BulkActionsProps) {
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [assignee, setAssignee] = useState('')

  if (selectedIds.length === 0) return null

  const handleApprove = () => {
    onBulkUpdate('approve')
    toast.success(`Approved ${selectedIds.length} alerts`)
  }

  const handleReject = () => {
    onBulkUpdate('reject')
    toast.success(`Rejected ${selectedIds.length} alerts`)
  }

  const handleAssign = () => {
    if (!assignee.trim()) {
      toast.error('Please enter an assignee name')
      return
    }
    onBulkUpdate('assign', assignee)
    toast.success(`Assigned ${selectedIds.length} alerts to ${assignee}`)
    setShowAssignModal(false)
    setAssignee('')
  }

  const handleDelete = () => {
    if (confirm(`Are you sure you want to delete ${selectedIds.length} alerts?`)) {
      onBulkUpdate('delete')
      toast.success(`Deleted ${selectedIds.length} alerts`)
    }
  }

  const handleExport = () => {
    onBulkUpdate('export')
    toast.success(`Exported ${selectedIds.length} alerts`)
  }

  return (
    <>
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50 animate-slide-up">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center gap-4">
          {/* Selection Count */}
          <div className="flex items-center gap-2 pr-4 border-r border-gray-300 dark:border-gray-600">
            <div className="w-6 h-6 bg-blue-600 dark:bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">
              {selectedIds.length}
            </div>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              selected
            </span>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleApprove}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 dark:bg-green-700 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-800 transition-colors text-sm font-medium"
            >
              <Check className="w-4 h-4" />
              Approve
            </button>

            <button
              onClick={handleReject}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 dark:bg-red-700 text-white rounded-lg hover:bg-red-700 dark:hover:bg-red-800 transition-colors text-sm font-medium"
            >
              <X className="w-4 h-4" />
              Reject
            </button>

            <button
              onClick={() => setShowAssignModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 dark:bg-purple-700 text-white rounded-lg hover:bg-purple-700 dark:hover:bg-purple-800 transition-colors text-sm font-medium"
            >
              <User className="w-4 h-4" />
              Assign
            </button>

            <button
              onClick={handleExport}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 transition-colors text-sm font-medium"
            >
              <Download className="w-4 h-4" />
              Export
            </button>

            <button
              onClick={handleDelete}
              className="flex items-center gap-2 px-4 py-2 bg-gray-600 dark:bg-gray-700 text-white rounded-lg hover:bg-gray-700 dark:hover:bg-gray-800 transition-colors text-sm font-medium"
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </button>
          </div>

          {/* Clear */}
          <button
            onClick={onClearSelection}
            className="ml-2 pl-4 border-l border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Assign Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 w-96 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Assign Alerts
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
              Assign {selectedIds.length} selected alerts to an investigator:
            </p>
            <input
              type="text"
              value={assignee}
              onChange={(e) => setAssignee(e.target.value)}
              placeholder="Enter investigator name or email"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              autoFocus
            />
            <div className="flex gap-3 mt-6">
              <button
                onClick={handleAssign}
                className="flex-1 px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 transition-colors font-medium"
              >
                Assign
              </button>
              <button
                onClick={() => {
                  setShowAssignModal(false)
                  setAssignee('')
                }}
                className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors font-medium"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes slide-up {
          from {
            transform: translate(-50%, 100%);
            opacity: 0;
          }
          to {
            transform: translate(-50%, 0);
            opacity: 1;
          }
        }
        .animate-slide-up {
          animation: slide-up 0.3s ease-out;
        }
      `}</style>
    </>
  )
}

