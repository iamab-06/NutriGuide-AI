import { useState, useRef, useEffect } from 'react'
import {
  Send,
  User,
  Leaf,
  AlertTriangle,
  Loader2,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Plus,
  Trash2,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react'
import { chat, streamChat } from '../services/api'
import type { ChatMessage } from '../types'

// Web Speech API interface for TypeScript
interface SpeechRecognitionEvent {
  resultIndex: number
  results: {
    [index: number]: {
      [index: number]: {
        transcript: string
      }
      isFinal: boolean
    }
  }
}

interface SpeechRecognitionInstance {
  continuous: boolean
  interimResults: boolean
  lang: string
  start: () => void
  stop: () => void
  abort: () => void
  onstart: (() => void) | null
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onerror: ((event: { error: string }) => void) | null
  onend: (() => void) | null
}

interface DisplayMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  warning?: string | null
  evidence_used?: boolean
}

export interface ChatSession {
  id: string
  title: string
  createdAt: number
  updatedAt: number
  messages: DisplayMessage[]
}

const QUICK_QUESTIONS = [
  'Is pizza high in calories?',
  'What makes chicken curry nutritious?',
  'How much protein does steak have?',
  'What is dietary fiber and why does it matter?',
  'Are donuts high in sugar?',
  'Explain the difference between simple and complex carbohydrates.',
]

const SESSIONS_STORAGE_KEY = 'nutriguide_chat_sessions'
const ACTIVE_SESSION_STORAGE_KEY = 'nutriguide_active_session_id'

const DEFAULT_WELCOME_MESSAGE: DisplayMessage = {
  role: 'assistant',
  content:
    'Hello! I\'m NutriGuide AI, your nutrition assistant powered by local Gemma 3 4B IT and a curated nutrition knowledge base. I can answer questions about food nutrition, ingredients, and dietary information. Ask me anything about food!',
}

const createNewSession = (title = 'New conversation'): ChatSession => ({
  id: 'session_' + Date.now() + '_' + Math.random().toString(36).slice(2, 7),
  title,
  createdAt: Date.now(),
  updatedAt: Date.now(),
  messages: [DEFAULT_WELCOME_MESSAGE],
})

function loadInitialSessions(): { sessions: ChatSession[]; activeId: string } {
  try {
    const rawSessions = localStorage.getItem(SESSIONS_STORAGE_KEY)
    if (rawSessions) {
      const parsed: ChatSession[] = JSON.parse(rawSessions)
      if (Array.isArray(parsed) && parsed.length > 0) {
        const cleanSessions = parsed
          .map((s) => ({
            ...s,
            messages:
              Array.isArray(s.messages) && s.messages.length > 0
                ? s.messages.filter((m) => m && typeof m.content === 'string' && m.content.trim().length > 0)
                : [DEFAULT_WELCOME_MESSAGE],
          }))
          .filter((s) => s.messages.length > 0)

        if (cleanSessions.length > 0) {
          const savedActiveId = localStorage.getItem(ACTIVE_SESSION_STORAGE_KEY)
          const validActive = cleanSessions.find((s) => s.id === savedActiveId)
            ? savedActiveId!
            : cleanSessions[0].id
          return { sessions: cleanSessions, activeId: validActive }
        }
      }
    }

    // Check legacy single-chat storage to retain user's existing history
    const legacy = localStorage.getItem('nutriguide_chat_history')
    if (legacy) {
      const parsedLegacy: DisplayMessage[] = JSON.parse(legacy)
      if (Array.isArray(parsedLegacy) && parsedLegacy.length > 0) {
        const firstUser = parsedLegacy.find((m) => m.role === 'user')
        const title = firstUser?.content
          ? firstUser.content.slice(0, 30).trim() + (firstUser.content.length > 30 ? '...' : '')
          : 'Diet plan conversation'
        const initialSession: ChatSession = {
          id: 'session_' + Date.now(),
          title,
          createdAt: Date.now(),
          updatedAt: Date.now(),
          messages: parsedLegacy,
        }
        return { sessions: [initialSession], activeId: initialSession.id }
      }
    }
  } catch (e) {
    console.warn('Failed to load chat sessions:', e)
  }

  const fresh = createNewSession()
  return { sessions: [fresh], activeId: fresh.id }
}

export default function AIAssistant() {
  const [{ sessions, activeId: initialActiveId }] = useState(loadInitialSessions)
  const [sessionsState, setSessionsState] = useState<ChatSession[]>(sessions)
  const [activeSessionId, setActiveSessionId] = useState<string>(initialActiveId)
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [isListening, setIsListening] = useState(false)
  const [speechError, setSpeechError] = useState<string | null>(null)
  const [speakingIndex, setSpeakingIndex] = useState<number | null>(null)

  const bottomRef = useRef<HTMLDivElement>(null)
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null)
  const shouldListenRef = useRef(false)
  const baseInputRef = useRef('')
  const inputRef = useRef(input)
  const restartTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const activeSession =
    sessionsState.find((s) => s.id === activeSessionId) ||
    sessionsState[0] ||
    createNewSession()
  const messages = activeSession.messages

  // Persist sessions whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(SESSIONS_STORAGE_KEY, JSON.stringify(sessionsState))
    } catch (e) {
      console.warn('Failed to save chat sessions to localStorage', e)
    }
  }, [sessionsState])

  // Persist active session id
  useEffect(() => {
    try {
      localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, activeSessionId)
    } catch (e) {
      console.warn('Failed to save active session ID to localStorage', e)
    }
  }, [activeSessionId])

  useEffect(() => {
    inputRef.current = input
  }, [input])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, activeSessionId])

  // Clean up speech recognition & synthesis on unmount
  useEffect(() => {
    return () => {
      shouldListenRef.current = false
      if (restartTimeoutRef.current) {
        clearTimeout(restartTimeoutRef.current)
      }
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort()
        } catch {
          // ignore
        }
      }
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel()
      }
    }
  }, [])

  const handleNewChat = () => {
    if (loading) return
    if (speakingIndex !== null && typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      setSpeakingIndex(null)
    }

    // If active session is already untouched, don't create duplicate empty sessions
    if (activeSession.messages.length <= 1) {
      return
    }

    const fresh = createNewSession()
    setSessionsState((prev) => [fresh, ...prev])
    setActiveSessionId(fresh.id)
  }

  const handleSelectSession = (sessionId: string) => {
    if (sessionId === activeSessionId) return
    if (speakingIndex !== null && typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      setSpeakingIndex(null)
    }
    setActiveSessionId(sessionId)
  }

  const handleDeleteSession = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation()
    if (speakingIndex !== null && typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel()
      setSpeakingIndex(null)
    }

    if (sessionsState.length <= 1) {
      const fresh = createNewSession()
      setSessionsState([fresh])
      setActiveSessionId(fresh.id)
      return
    }

    const remaining = sessionsState.filter((s) => s.id !== sessionId)
    setSessionsState(remaining)
    if (activeSessionId === sessionId) {
      setActiveSessionId(remaining[0].id)
    }
  }

  const toggleListening = () => {
    setSpeechError(null)

    if (isListening || shouldListenRef.current) {
      shouldListenRef.current = false
      setIsListening(false)
      if (restartTimeoutRef.current) {
        clearTimeout(restartTimeoutRef.current)
      }
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop()
        } catch {
          // ignore
        }
      }
      return
    }

    const SpeechRecognition =
      (window as unknown as { SpeechRecognition?: new () => SpeechRecognitionInstance; webkitSpeechRecognition?: new () => SpeechRecognitionInstance }).SpeechRecognition ||
      (window as unknown as { SpeechRecognition?: new () => SpeechRecognitionInstance; webkitSpeechRecognition?: new () => SpeechRecognitionInstance }).webkitSpeechRecognition

    if (!SpeechRecognition) {
      setSpeechError('Speech recognition is not supported in this browser. Please open NutriGuide in Google Chrome or Microsoft Edge.')
      return
    }

    try {
      shouldListenRef.current = true
      setIsListening(true)
      baseInputRef.current = inputRef.current ? inputRef.current.trim() + ' ' : ''

      const recognition = new SpeechRecognition()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.lang = 'en-IN'

      recognition.onstart = () => {
        setIsListening(true)
        setSpeechError(null)
      }

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let sessionTranscript = ''
        const resultCount = Object.keys(event.results).length
        for (let i = 0; i < resultCount; i++) {
          if (event.results[i] && event.results[i][0]) {
            sessionTranscript += event.results[i][0].transcript
          }
        }
        if (sessionTranscript) {
          setInput(baseInputRef.current + sessionTranscript)
        }
      }

      recognition.onerror = (event: { error: string }) => {
        console.warn('Speech recognition error event:', event.error)
        if (event.error === 'no-speech') {
          return
        }
        if (event.error === 'not-allowed') {
          shouldListenRef.current = false
          setIsListening(false)
          setSpeechError('Microphone permission was denied. Please allow microphone access in your browser URL bar.')
        } else if (event.error === 'network') {
          shouldListenRef.current = false
          setIsListening(false)
          const isBrave =
            (navigator as unknown as { brave?: unknown }).brave !== undefined ||
            navigator.userAgent.includes('Brave')
          if (isBrave) {
            setSpeechError(
              'Brave Browser blocks cloud speech recognition by default for privacy. Please open NutriGuide in Google Chrome or Microsoft Edge, or enable "Use Google services for push messaging and speech recognition" in brave://settings/privacy.'
            )
          } else {
            setSpeechError(
              'Speech recognition network error: The browser speech server is unreachable. Please open NutriGuide in Google Chrome or Microsoft Edge.'
            )
          }
        } else {
          setSpeechError(`Speech recognition notice: ${event.error}`)
        }
      }

      recognition.onend = () => {
        if (shouldListenRef.current) {
          baseInputRef.current = inputRef.current ? inputRef.current.trim() + ' ' : ''
          if (restartTimeoutRef.current) clearTimeout(restartTimeoutRef.current)
          restartTimeoutRef.current = setTimeout(() => {
            if (shouldListenRef.current) {
              try {
                recognition.start()
              } catch (err) {
                console.debug('Recognition restart notice:', err)
              }
            }
          }, 150)
        } else {
          setIsListening(false)
        }
      }

      recognitionRef.current = recognition
      recognition.start()
    } catch (err: unknown) {
      shouldListenRef.current = false
      setIsListening(false)
      setSpeechError(`Failed to start speech recognition: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
  }

  const speakMessage = (index: number, text: string) => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      return
    }

    if (speakingIndex === index) {
      window.speechSynthesis.cancel()
      setSpeakingIndex(null)
      return
    }

    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.rate = 1.0
    utterance.pitch = 1.0

    utterance.onend = () => {
      setSpeakingIndex(null)
    }
    utterance.onerror = () => {
      setSpeakingIndex(null)
    }

    setSpeakingIndex(index)
    window.speechSynthesis.speak(utterance)
  }

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return

    // If user sends message while mic is still listening, stop listening
    if (shouldListenRef.current || isListening) {
      shouldListenRef.current = false
      setIsListening(false)
      if (restartTimeoutRef.current) {
        clearTimeout(restartTimeoutRef.current)
      }
      try {
        recognitionRef.current?.stop()
      } catch {
        // ignore
      }
    }

    const currentSessionId = activeSessionId
    const currentSession = sessionsState.find((s) => s.id === currentSessionId)
    const currentMessages = currentSession ? currentSession.messages : []

    const userMsg: DisplayMessage = { role: 'user', content: text }
    const assistantIndex = currentMessages.length + 1
    const assistantPlaceholder: DisplayMessage = {
      role: 'assistant',
      content: '',
      sources: [],
    }

    // Determine auto-title if session title is still default
    let newTitle: string | null = null
    if (!currentSession || currentSession.title === 'New conversation' || currentSession.title === 'New Chat') {
      newTitle = text.slice(0, 32).trim() + (text.length > 32 ? '...' : '')
    }

    setSessionsState((prev) =>
      prev.map((s) => {
        if (s.id === currentSessionId) {
          return {
            ...s,
            title: newTitle || s.title,
            updatedAt: Date.now(),
            messages: [...s.messages, userMsg, assistantPlaceholder],
          }
        }
        return s
      })
    )

    setInput('')
    setLoading(true)

    // Build history for API (last 8 messages, excluding welcome)
    const historyForApi: ChatMessage[] = currentMessages
      .slice(-8)
      .map((m) => ({ role: m.role, content: m.content }))

    try {
      let accumulated = ''
      await streamChat(
        text,
        undefined,
        historyForApi,
        {
          onToken: (tok) => {
            accumulated += tok
            setSessionsState((prev) =>
              prev.map((s) => {
                if (s.id === currentSessionId) {
                  const updated = [...s.messages]
                  if (updated[assistantIndex]) {
                    updated[assistantIndex] = {
                      ...updated[assistantIndex],
                      content: accumulated,
                    }
                  }
                  return { ...s, messages: updated, updatedAt: Date.now() }
                }
                return s
              })
            )
          },
          onMeta: (meta) => {
            setSessionsState((prev) =>
              prev.map((s) => {
                if (s.id === currentSessionId) {
                  const updated = [...s.messages]
                  if (updated[assistantIndex]) {
                    updated[assistantIndex] = {
                      ...updated[assistantIndex],
                      sources: meta.sources,
                      evidence_used: meta.evidence_used,
                    }
                  }
                  return { ...s, messages: updated, updatedAt: Date.now() }
                }
                return s
              })
            )
          },
          onError: (err) => {
            setSessionsState((prev) =>
              prev.map((s) => {
                if (s.id === currentSessionId) {
                  const updated = [...s.messages]
                  if (updated[assistantIndex]) {
                    updated[assistantIndex] = {
                      ...updated[assistantIndex],
                      content: updated[assistantIndex].content || `I'm sorry, I encountered an issue: ${err}`,
                      warning: 'Service error',
                    }
                  }
                  return { ...s, messages: updated, updatedAt: Date.now() }
                }
                return s
              })
            )
          },
        }
      )
    } catch {
      // Fallback to standard chat() endpoint if streaming fails
      try {
        const response = await chat(text, undefined, historyForApi)
        setSessionsState((prev) =>
          prev.map((s) => {
            if (s.id === currentSessionId) {
              const updated = [...s.messages]
              if (updated[assistantIndex]) {
                updated[assistantIndex] = {
                  role: 'assistant',
                  content: response.answer,
                  sources: response.sources,
                  warning: response.warning,
                  evidence_used: response.evidence_used,
                }
              }
              return { ...s, messages: updated, updatedAt: Date.now() }
            }
            return s
          })
        )
      } catch (fallbackErr: unknown) {
        setSessionsState((prev) =>
          prev.map((s) => {
            if (s.id === currentSessionId) {
              const updated = [...s.messages]
              if (updated[assistantIndex]) {
                updated[assistantIndex] = {
                  role: 'assistant',
                  content: `I'm sorry, I couldn't process that request. ${
                    fallbackErr instanceof Error ? fallbackErr.message : 'Please try again.'
                  }`,
                  warning: 'Service error',
                }
              }
              return { ...s, messages: updated, updatedAt: Date.now() }
            }
            return s
          })
        )
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-full min-w-0 bg-white relative">
      {/* Mobile Drawer Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* History Sidebar */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-30 w-72 bg-[#f8faf9] border-r border-gray-200 flex flex-col transition-all duration-200 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full md:hidden'
        }`}
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-200/80 flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-800 font-semibold text-sm">
            <MessageSquare className="w-4 h-4 text-[#2d6a4f]" />
            <span>Chat History</span>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-200/60 rounded-lg transition-colors"
            title="Collapse history"
          >
            <PanelLeftClose className="w-4 h-4" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={handleNewChat}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-3 bg-[#2d6a4f] hover:bg-[#1b4332] text-white rounded-xl text-sm font-medium transition-all shadow-xs disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto px-3 py-1 space-y-1">
          {sessionsState.map((session) => {
            const isActive = session.id === activeSessionId
            return (
              <div
                key={session.id}
                onClick={() => handleSelectSession(session.id)}
                className={`group relative flex items-center gap-2.5 px-3 py-2.5 rounded-xl cursor-pointer text-sm transition-all ${
                  isActive
                    ? 'bg-[#e8f4ed] text-[#1b4332] font-semibold border border-[#b7e4c7] shadow-2xs'
                    : 'text-gray-700 hover:bg-gray-100/80 hover:text-gray-900 border border-transparent'
                }`}
              >
                <MessageSquare
                  className={`w-4 h-4 flex-shrink-0 ${
                    isActive ? 'text-[#2d6a4f]' : 'text-gray-400 group-hover:text-gray-600'
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <p className="truncate text-xs sm:text-sm">{session.title}</p>
                </div>
                <button
                  type="button"
                  onClick={(e) => handleDeleteSession(e, session.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-md transition-all flex-shrink-0"
                  title="Delete chat"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            )
          })}
        </div>
      </aside>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden bg-white">
        {/* Top Chat Bar with Toggle Sidebar & New Chat shortcut */}
        <div className="px-6 py-2.5 bg-[#f8fdf9] border-b border-gray-100 flex items-center justify-between gap-3 flex-shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-gray-600 hover:text-[#2d6a4f] hover:bg-white rounded-lg border border-gray-200 transition-all shadow-2xs"
                title="Open chat history"
              >
                <PanelLeftOpen className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Chats</span>
              </button>
            )}
            <span className="text-xs font-semibold text-gray-600 truncate max-w-[200px] sm:max-w-[400px]">
              {activeSession.title}
            </span>
          </div>

          <button
            onClick={handleNewChat}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-[#2d6a4f] bg-white hover:bg-[#e8f4ed] border border-[#b7e4c7] rounded-full transition-all disabled:opacity-50 shadow-2xs flex-shrink-0"
            title="Start a new chat"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Quick questions */}
        <div className="px-6 py-2 bg-white border-b border-gray-100 flex gap-2 overflow-x-auto flex-shrink-0">
          {QUICK_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => sendMessage(q)}
              disabled={loading}
              className="flex-shrink-0 px-3 py-1 bg-[#f8fdf9] border border-[#b7e4c7] text-[#2d6a4f] text-xs font-medium rounded-full hover:bg-[#e8f4ed] transition-all disabled:opacity-50"
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
                  {msg.content ? (
                    <div>
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                      {msg.role === 'assistant' && (
                        <div className="mt-2 pt-2 border-t border-gray-100 flex items-center justify-end">
                          <button
                            type="button"
                            onClick={() => speakMessage(i, msg.content)}
                            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
                              speakingIndex === i
                                ? 'bg-red-50 text-red-600 border border-red-200'
                                : 'text-gray-500 hover:text-[#2d6a4f] hover:bg-[#e8f4ed]'
                            }`}
                            title={speakingIndex === i ? 'Stop audio' : 'Listen to response'}
                          >
                            {speakingIndex === i ? (
                              <>
                                <VolumeX className="w-3.5 h-3.5 animate-pulse text-red-600" />
                                <span>Stop Speaking</span>
                              </>
                            ) : (
                              <>
                                <Volume2 className="w-3.5 h-3.5 text-[#2d6a4f]" />
                                <span>Read Aloud</span>
                              </>
                            )}
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 py-0.5">
                      <Loader2 className="w-4 h-4 text-[#2d6a4f] animate-spin" />
                      <span className="text-sm text-gray-500">Retrieving verified evidence...</span>
                    </div>
                  )}
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
          {loading && messages.length > 0 && messages[messages.length - 1].role === 'user' && (
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
          {/* Live Continuous Listening Status Banner */}
          {isListening && (
            <div className="mb-2.5 px-3 py-2 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between text-xs text-red-700 shadow-sm">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block animate-ping"></span>
                <span className="font-bold text-red-900">Microphone ON (Continuous Mode):</span>
                <span className="text-red-800">You can pause and think freely. Speech will not stop until you turn it off.</span>
              </div>
              <button
                type="button"
                onClick={toggleListening}
                className="text-xs font-bold text-white bg-red-600 hover:bg-red-700 px-2.5 py-1 rounded-md transition-all ml-2 flex-shrink-0 shadow-xs"
              >
                Done / Stop
              </button>
            </div>
          )}

          {/* Speech Error Banner */}
          {speechError && (
            <div className="mb-2.5 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900 flex items-start justify-between gap-2 shadow-sm">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                <div className="leading-relaxed">
                  <span className="font-semibold block text-amber-950 mb-0.5">Voice Recognition Notice:</span>
                  <span>{speechError}</span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSpeechError(null)}
                className="text-xs text-amber-700 hover:text-amber-950 font-bold ml-2 underline flex-shrink-0"
              >
                Dismiss
              </button>
            </div>
          )}

          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage(input)}
              placeholder={isListening ? 'Listening to your voice... Speak now' : 'Ask about nutrition, ingredients, allergens...'}
              className={`flex-1 px-4 py-3 rounded-xl border text-sm transition-all ${
                isListening
                  ? 'border-red-400 bg-red-50/40 ring-2 ring-red-300 focus:outline-none'
                  : 'border-gray-200 bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#52b788] focus:border-transparent'
              }`}
              disabled={loading}
            />

            {/* Voice input button */}
            <button
              type="button"
              onClick={toggleListening}
              disabled={loading}
              title={isListening ? 'Stop listening' : 'Talk with AI Assistant (Voice Recognition)'}
              className={`px-3.5 py-3 rounded-xl border transition-all flex items-center justify-center ${
                isListening
                  ? 'bg-red-500 hover:bg-red-600 text-white border-red-600 animate-pulse shadow-md shadow-red-200'
                  : 'bg-white hover:bg-[#e8f4ed] text-[#2d6a4f] border-gray-200 hover:border-[#b7e4c7]'
              }`}
            >
              {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>

            {/* Send message button */}
            <button
              onClick={() => sendMessage(input)}
              disabled={loading || !input.trim()}
              title="Send Message"
              className="px-4 py-3 bg-[#2d6a4f] hover:bg-[#1a3d2b] disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl transition-all flex items-center justify-center"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-2 text-center">
            Answers are grounded in retrieved evidence. Voice recognition supported in Chrome & Edge.
          </p>
        </div>
      </div>
    </div>
  )
}
