'use client'

import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, Bot, User, Sparkles } from 'lucide-react'
import { toast } from 'sonner'

interface Message {
  id: string
  type: 'user' | 'bot'
  content: string
  timestamp: Date
}

export function FraudChatbot() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'bot',
      content: 'Hi! I\'m your AI Fraud Detection Assistant. I can help you analyze alerts, search transactions, and provide insights. What would you like to know?',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const quickActions = [
    '🚨 Show high-risk alerts',
    '📊 Transaction summary',
    '🌍 Geographic patterns',
    '💰 Large transactions'
  ]

  const handleSend = async () => {
    if (!input.trim()) return

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsTyping(true)

    // Simulate AI response
    setTimeout(() => {
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: generateResponse(input),
        timestamp: new Date()
      }
      setMessages(prev => [...prev, botMessage])
      setIsTyping(false)
    }, 1500)
  }

  const generateResponse = (query: string): string => {
    const lowerQuery = query.toLowerCase()

    // High-risk alerts
    if (lowerQuery.includes('high') && lowerQuery.includes('risk')) {
      return '🚨 I found 12 high-risk alerts in the last 24 hours:\n\n• 5 velocity checks (multiple transactions in short time)\n• 4 large amount anomalies (>$10,000)\n• 3 location anomalies (unusual geographic patterns)\n\nWould you like me to show details for any category?'
    }

    // Transaction summary
    if (lowerQuery.includes('transaction') && (lowerQuery.includes('summary') || lowerQuery.includes('total'))) {
      return '📊 Transaction Summary (Last 24h):\n\n• Total Transactions: 1,247\n• Total Amount: $2.4M\n• Avg Transaction: $1,925\n• Flagged: 23 (1.8%)\n• Top Merchant: AMAZON ($145K)\n\nNeed more details on any metric?'
    }

    // Geographic patterns
    if (lowerQuery.includes('geographic') || lowerQuery.includes('location') || lowerQuery.includes('pattern')) {
      return '🌍 Geographic Analysis:\n\n• Most fraud: New York (23%), LA (18%), Miami (15%)\n• Cross-border transactions: 8% of total\n• Unusual location changes: 12 cases\n• Velocity across states: 5 accounts\n\nWant to see the fraud map?'
    }

    // Large transactions
    if (lowerQuery.includes('large') && lowerQuery.includes('transaction')) {
      return '💰 Large Transactions (>$5,000):\n\n• Count: 47 transactions\n• Total: $1.2M\n• Highest: $45,000 (Account #1234)\n• Flagged: 8 (17%)\n• Common merchants: Jewelry, Electronics, Travel\n\nShould I export these for review?'
    }

    // Help/what can you do
    if (lowerQuery.includes('help') || lowerQuery.includes('what') || lowerQuery.includes('can')) {
      return '🤖 I can help you with:\n\n• 🔍 Search & analyze alerts\n• 📊 Generate reports & summaries\n• 🌍 Geographic fraud patterns\n• 💳 Transaction analysis\n• 👤 Account risk assessment\n• 📈 Trend analysis\n\nJust ask me anything about your fraud data!'
    }

    // Account lookup
    if (lowerQuery.includes('account') && lowerQuery.match(/\d+/)) {
      const accountNum = lowerQuery.match(/\d+/)[0]
      return `👤 Account #${accountNum} Analysis:\n\n• Status: Active\n• Risk Score: 68/100 (Medium)\n• Transactions (24h): 12\n• Total Amount: $8,450\n• Flagged Alerts: 2\n• Last Activity: 15 min ago\n\nWant to see transaction details?`
    }

    // Default response
    return `I understand you're asking about "${query}". \n\nI can help you analyze:\n• Fraud alerts & patterns\n• Transaction trends\n• Account risk scores\n• Geographic data\n\nTry asking something like "Show me high-risk alerts" or click a quick action above!`
  }

  const handleQuickAction = (action: string) => {
    setInput(action.replace(/[🚨📊🌍💰]/g, '').trim())
    handleSend()
  }

  return (
    <>
      {/* Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-700 dark:to-purple-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all hover:scale-110 flex items-center justify-center z-40 animate-bounce-subtle"
        >
          <MessageCircle className="w-6 h-6" />
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-white dark:bg-gray-800 rounded-2xl shadow-2xl flex flex-col z-50 border border-gray-200 dark:border-gray-700 animate-slide-up-chat">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-700 dark:to-purple-700 p-4 rounded-t-2xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-white font-semibold flex items-center gap-2">
                  Fraud AI Assistant
                  <Sparkles className="w-4 h-4" />
                </h3>
                <p className="text-xs text-white/80">Always online</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="text-white/80 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-gray-900">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.type === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.type === 'user' 
                    ? 'bg-blue-600 dark:bg-blue-700' 
                    : 'bg-purple-600 dark:bg-purple-700'
                }`}>
                  {message.type === 'user' ? (
                    <User className="w-5 h-5 text-white" />
                  ) : (
                    <Bot className="w-5 h-5 text-white" />
                  )}
                </div>
                <div className={`flex-1 ${message.type === 'user' ? 'flex justify-end' : ''}`}>
                  <div className={`inline-block px-4 py-2 rounded-2xl max-w-[85%] ${
                    message.type === 'user'
                      ? 'bg-blue-600 dark:bg-blue-700 text-white'
                      : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700'
                  }`}>
                    <p className="text-sm whitespace-pre-line">{message.content}</p>
                    <p className="text-xs mt-1 opacity-60">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-purple-600 dark:bg-purple-700 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-4 py-3 rounded-2xl">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions */}
          <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div className="flex gap-2 overflow-x-auto pb-2">
              {quickActions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickAction(action)}
                  className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-full text-xs font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap transition-colors"
                >
                  {action}
                </button>
              ))}
            </div>
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 rounded-b-2xl">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask me anything..."
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-700 dark:to-purple-700 text-white rounded-xl hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes bounce-subtle {
          0%, 100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-4px);
          }
        }
        @keyframes slide-up-chat {
          from {
            transform: translateY(100%);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
        .animate-bounce-subtle {
          animation: bounce-subtle 2s ease-in-out infinite;
        }
        .animate-slide-up-chat {
          animation: slide-up-chat 0.3s ease-out;
        }
      `}</style>
    </>
  )
}

