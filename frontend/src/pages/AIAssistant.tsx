import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Leaf, AlertTriangle, Loader2, BookOpen } from 'lucide-react'
import { chat } from '../services/api'
import type { ChatMessage } from '../types'

interface DisplayMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  warning?: string | null
  evidence_used?: boolean
}

const QUICK_QUESTIONS = [
  'Is pizza high in calories?',
  'What makes chicken curry nutritious?',
  'How much protein does steak have?',
  'What is dietary fiber and why does it matter?',
  'Are donuts high in sugar?',
  'Explain the difference between simple and complex carbohydrates.',
]

export default function AIAssistant() {
  const [messages, setMessages] = useState<DisplayMessage[]>([
    {
      role: 'assistant',
      content:
        'Hello! I\'m NutriGuide AI, your nutrition assistant powered by Google Gemini and a curated nutrition knowledge base. I can answer questions about food nutrition, ingredients, and dietary information. Ask me anything about food!',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return
    const userMsg: DisplayMessage = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    // Build history for API (last 8 messages, excluding welcome)
    const historyForApi: ChatMessage[] = messages
      .slice(-8)
      .map((m) => ({ role: m.role, content: m.content }))

    try {
      const response = await chat(text, undefined, historyForApi)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.answer,
          sources: response.sources,
          warning: response.warning,
          evidence_used: response.evidence_used,
        },
      ])
    } catch (e: unknown) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `I'm sorry, I couldn't process that request. ${e instanceof Error ? e.message : 'Please try again.'}`,
          warning: 'Service error',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 bg-white border-b border-gray-100 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-[#e8f4ed] flex items-center justify-center">
          <Bot className="w-6 h-6 text-[#2d6a4f]" />
        </div>
        <div>
          <h2 className="font-bold text-gray-900">AI Nutrition Assistant</h2>
          <p className="text-xs text-gray-500">Powered by Gemini + RAG knowledge base</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-[#52b788]" />
          <span className="text-xs text-gray-500">Evidence-grounded</span>
        </div>
      </div>

      {/* Quick questions */}
      <div className="px-6 py-3 bg-[#f8fdf9] border-b border-gray-100 flex gap-2 overflow-x-auto flex-shrink-0">
        {QUICK_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => sendMessage(q)}
            disabled={loading}
            className="flex-shrink-0 px-3 py-1.5 bg-white border border-[#b7e4c7] text-[#2d6a4f] text-xs font-medium rounded-full hover:bg-[#e8f4ed] transition-all disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            {/* Avatar */}
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                msg.role === 'user'
                  ? 'bg-[#2d6a4f] text-white'
                  : 'bg-[#e8f4ed] text-[#2d6a4f]'
              }`}
            >
              {msg.role === 'user' ? <User className="w-4 h-4" /> : <Leaf className="w-4 h-4" />}
            </div>

            {/* Bubble */}
            <div className={`max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
              <div
                className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-[#2d6a4f] text-white rounded-tr-sm'
                    : 'bg-white border border-gray-100 shadow-sm text-gray-800 rounded-tl-sm'
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
              </div>

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {msg.sources.map((s) => (
                    <span
                      key={s}
                      className="text-xs px-2 py-0.5 bg-[#e8f4ed] text-[#2d6a4f] rounded-full"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              )}

              {/* Warning */}
              {msg.warning && (
                <div className="flex items-center gap-1 text-xs text-amber-600">
                  <AlertTriangle className="w-3 h-3" />
                  {msg.warning}
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-[#e8f4ed] flex items-center justify-center flex-shrink-0">
              <Leaf className="w-4 h-4 text-[#2d6a4f]" />
            </div>
            <div className="bg-white border border-gray-100 shadow-sm rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 text-[#2d6a4f] animate-spin" />
                <span className="text-sm text-gray-500">Retrieving information...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 bg-white border-t border-gray-100">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
            placeholder="Ask about nutrition, ingredients, allergens..."
            className="flex-1 px-4 py-3 rounded-xl border border-gray-200 bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#52b788] focus:border-transparent transition-all text-sm"
            disabled={loading}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={loading || !input.trim()}
            className="px-4 py-3 bg-[#2d6a4f] hover:bg-[#1a3d2b] disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl transition-all"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2 text-center">
          Answers are grounded in retrieved evidence. This is not medical advice.
        </p>
      </div>
    </div>
  )
}
