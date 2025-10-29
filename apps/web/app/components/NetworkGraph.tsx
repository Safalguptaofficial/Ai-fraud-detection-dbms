'use client'

import { useEffect, useRef, useState } from 'react'
import { Network, Users, DollarSign, Store } from 'lucide-react'

interface Node {
  id: string
  type: 'account' | 'transaction' | 'merchant' | 'ip' | 'device'
  label: string
  risk: 'high' | 'medium' | 'low'
  x?: number
  y?: number
  vx?: number
  vy?: number
}

interface Link {
  source: string
  target: string
  type: 'transaction' | 'shared_ip' | 'shared_device' | 'same_merchant'
  amount?: number
}

interface NetworkGraphProps {
  data?: { nodes: Node[]; links: Link[] }
}

export function NetworkGraph({ data }: NetworkGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [hoveredNode, setHoveredNode] = useState<Node | null>(null)
  const [graphData, setGraphData] = useState<{ nodes: Node[]; links: Link[] }>(
    data || generateMockData()
  )

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * window.devicePixelRatio
    canvas.height = rect.height * window.devicePixelRatio
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio)

    // Initialize positions if not set
    graphData.nodes.forEach((node, i) => {
      if (!node.x || !node.y) {
        const angle = (i / graphData.nodes.length) * 2 * Math.PI
        const radius = Math.min(rect.width, rect.height) * 0.3
        node.x = rect.width / 2 + radius * Math.cos(angle)
        node.y = rect.height / 2 + radius * Math.sin(angle)
        node.vx = 0
        node.vy = 0
      }
    })

    // Simple force simulation
    const simulate = () => {
      const nodes = graphData.nodes
      const links = graphData.links

      // Apply forces
      for (let i = 0; i < 50; i++) {
        // Repulsion between nodes
        for (let j = 0; j < nodes.length; j++) {
          for (let k = j + 1; k < nodes.length; k++) {
            const dx = nodes[k].x! - nodes[j].x!
            const dy = nodes[k].y! - nodes[j].y!
            const dist = Math.sqrt(dx * dx + dy * dy) || 1
            const force = 1000 / (dist * dist)
            
            nodes[j].vx! -= (dx / dist) * force
            nodes[j].vy! -= (dy / dist) * force
            nodes[k].vx! += (dx / dist) * force
            nodes[k].vy! += (dy / dist) * force
          }
        }

        // Attraction along links
        links.forEach(link => {
          const source = nodes.find(n => n.id === link.source)
          const target = nodes.find(n => n.id === link.target)
          if (!source || !target) return

          const dx = target.x! - source.x!
          const dy = target.y! - source.y!
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          const force = dist * 0.01

          source.vx! += (dx / dist) * force
          source.vy! += (dy / dist) * force
          target.vx! -= (dx / dist) * force
          target.vy! -= (dy / dist) * force
        })

        // Update positions
        nodes.forEach(node => {
          node.vx! *= 0.9 // Damping
          node.vy! *= 0.9
          node.x! += node.vx!
          node.y! += node.vy!

          // Keep in bounds
          node.x! = Math.max(50, Math.min(rect.width - 50, node.x!))
          node.y! = Math.max(50, Math.min(rect.height - 50, node.y!))
        })
      }

      setGraphData({ nodes: [...nodes], links })
    }

    simulate()
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const rect = canvas.getBoundingClientRect()
    
    // Clear canvas
    ctx.clearRect(0, 0, rect.width, rect.height)

    // Draw links
    graphData.links.forEach(link => {
      const source = graphData.nodes.find(n => n.id === link.source)
      const target = graphData.nodes.find(n => n.id === link.target)
      if (!source || !target || !source.x || !target.x) return

      ctx.beginPath()
      ctx.moveTo(source.x, source.y!)
      ctx.lineTo(target.x, target.y!)
      
      if (link.type === 'transaction') {
        ctx.strokeStyle = '#3b82f6'
        ctx.lineWidth = 2
      } else if (link.type === 'shared_ip') {
        ctx.strokeStyle = '#ef4444'
        ctx.lineWidth = 2
        ctx.setLineDash([5, 5])
      } else if (link.type === 'shared_device') {
        ctx.strokeStyle = '#f59e0b'
        ctx.lineWidth = 2
        ctx.setLineDash([3, 3])
      } else {
        ctx.strokeStyle = '#6b7280'
        ctx.lineWidth = 1
      }
      
      ctx.stroke()
      ctx.setLineDash([])
    })

    // Draw nodes
    graphData.nodes.forEach(node => {
      if (!node.x || !node.y) return

      const isSelected = selectedNode?.id === node.id
      const isHovered = hoveredNode?.id === node.id
      const radius = isSelected ? 20 : isHovered ? 18 : 15

      // Node circle
      ctx.beginPath()
      ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI)
      
      // Color by type and risk
      if (node.type === 'account') {
        ctx.fillStyle = node.risk === 'high' ? '#ef4444' : node.risk === 'medium' ? '#f59e0b' : '#10b981'
      } else if (node.type === 'transaction') {
        ctx.fillStyle = '#3b82f6'
      } else if (node.type === 'merchant') {
        ctx.fillStyle = '#8b5cf6'
      } else {
        ctx.fillStyle = '#6b7280'
      }
      
      ctx.fill()
      
      if (isSelected || isHovered) {
        ctx.strokeStyle = '#fff'
        ctx.lineWidth = 3
        ctx.stroke()
      }

      // Label
      if (isHovered || isSelected) {
        ctx.fillStyle = '#1f2937'
        ctx.font = 'bold 12px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(node.label, node.x, node.y - radius - 10)
      }
    })
  }, [graphData, selectedNode, hoveredNode])

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    const hovered = graphData.nodes.find(node => {
      if (!node.x || !node.y) return false
      const dx = x - node.x
      const dy = y - node.y
      return Math.sqrt(dx * dx + dy * dy) < 15
    })

    setHoveredNode(hovered || null)
    canvas.style.cursor = hovered ? 'pointer' : 'default'
  }

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (hoveredNode) {
      setSelectedNode(hoveredNode)
    } else {
      setSelectedNode(null)
    }
  }

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Network className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Fraud Network Graph
            </h2>
          </div>
          <div className="flex gap-2 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-gray-600 dark:text-gray-300">High Risk</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
              <span className="text-gray-600 dark:text-gray-300">Medium Risk</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-gray-600 dark:text-gray-300">Low Risk</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 relative">
        <canvas
          ref={canvasRef}
          onMouseMove={handleMouseMove}
          onClick={handleClick}
          className="w-full h-full"
          style={{ width: '100%', height: '100%' }}
        />
        
        {selectedNode && (
          <div className="absolute top-4 right-4 bg-white dark:bg-gray-700 p-4 rounded-lg shadow-lg border border-gray-200 dark:border-gray-600 min-w-[250px]">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900 dark:text-white">Node Details</h3>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-2 text-sm">
              <div>
                <span className="text-gray-500 dark:text-gray-400">ID:</span>
                <span className="ml-2 font-mono text-gray-900 dark:text-white">{selectedNode.id}</span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Type:</span>
                <span className="ml-2 font-medium text-gray-900 dark:text-white capitalize">{selectedNode.type}</span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Label:</span>
                <span className="ml-2 text-gray-900 dark:text-white">{selectedNode.label}</span>
              </div>
              <div>
                <span className="text-gray-500 dark:text-gray-400">Risk:</span>
                <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                  selectedNode.risk === 'high' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' :
                  selectedNode.risk === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' :
                  'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                }`}>
                  {selectedNode.risk.toUpperCase()}
                </span>
              </div>
              
              <div className="pt-3 border-t border-gray-200 dark:border-gray-600">
                <p className="text-gray-500 dark:text-gray-400 mb-2">Connected to:</p>
                <div className="space-y-1">
                  {graphData.links
                    .filter(l => l.source === selectedNode.id || l.target === selectedNode.id)
                    .map((link, i) => (
                      <div key={i} className="text-xs text-gray-700 dark:text-gray-300">
                        {link.source === selectedNode.id ? 
                          graphData.nodes.find(n => n.id === link.target)?.label :
                          graphData.nodes.find(n => n.id === link.source)?.label
                        } ({link.type})
                      </div>
                    ))
                  }
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {graphData.nodes.length}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Total Nodes</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
              {graphData.links.length}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Connections</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-red-600 dark:text-red-400">
              {graphData.nodes.filter(n => n.risk === 'high').length}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400">High Risk</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {graphData.links.filter(l => l.type === 'shared_ip' || l.type === 'shared_device').length}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Suspicious Links</div>
          </div>
        </div>
      </div>
    </div>
  )
}

function generateMockData(): { nodes: Node[]; links: Link[] } {
  const nodes: Node[] = [
    { id: 'A1', type: 'account', label: 'Account A1', risk: 'high' },
    { id: 'A2', type: 'account', label: 'Account A2', risk: 'high' },
    { id: 'A3', type: 'account', label: 'Account A3', risk: 'medium' },
    { id: 'A4', type: 'account', label: 'Account A4', risk: 'low' },
    { id: 'M1', type: 'merchant', label: 'Merchant X', risk: 'medium' },
    { id: 'M2', type: 'merchant', label: 'Merchant Y', risk: 'low' },
    { id: 'IP1', type: 'ip', label: '192.168.1.1', risk: 'high' },
    { id: 'D1', type: 'device', label: 'Device ABC123', risk: 'high' },
  ]

  const links: Link[] = [
    { source: 'A1', target: 'M1', type: 'transaction', amount: 5000 },
    { source: 'A2', target: 'M1', type: 'transaction', amount: 4800 },
    { source: 'A3', target: 'M2', type: 'transaction', amount: 200 },
    { source: 'A4', target: 'M2', type: 'transaction', amount: 150 },
    { source: 'A1', target: 'A2', type: 'shared_ip' },
    { source: 'A1', target: 'IP1', type: 'shared_ip' },
    { source: 'A2', target: 'IP1', type: 'shared_ip' },
    { source: 'A1', target: 'D1', type: 'shared_device' },
    { source: 'A2', target: 'D1', type: 'shared_device' },
  ]

  return { nodes, links }
}

