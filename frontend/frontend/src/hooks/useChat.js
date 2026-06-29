import { useCallback, useMemo, useRef, useState } from 'react'
import { suggestedQuestions } from '../utils/constants.js'
import { buildChatExport, downloadTextFile, formatTime } from '../utils/helpers.js'

const assistantReplies = {
  auth: 'Use an API key for server-to-server calls and OAuth when users need scoped access. Send the key in `Authorization: Bearer YOUR_API_KEY`, rotate it regularly, and store it outside client bundles.',
  rate: 'Rate limits protect shared infrastructure. Read limit headers, back off on `429`, retry with jitter, and design queues for bursty imports.',
  sdk: 'SDKs wrap raw API calls with typed helpers, retries, and response parsing. Install the package, configure the client with your key, then call focused methods like `client.docs.search()`.',
  upload: 'Open the PDF upload panel, choose a `.pdf` file, and wait for the success state. The real parsing pipeline can later live behind `POST /upload-pdf`.',
  default: 'I can help navigate docs, explain API behavior, summarize guides, and reason over uploaded PDFs. This frontend is ready to connect to a real RAG backend through the API service.',
}

function createMessage(role, content, source = 'website') {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    source,
    time: formatTime(),
    createdAt: Date.now(),
  }
}

function getAssistantReply(prompt) {
  const lower = prompt.toLowerCase()
  if (lower.includes('auth')) return assistantReplies.auth
  if (lower.includes('rate')) return assistantReplies.rate
  if (lower.includes('sdk')) return assistantReplies.sdk
  if (lower.includes('pdf') || lower.includes('upload')) return assistantReplies.upload
  return assistantReplies.default
}

export function useChat() {
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [toast, setToast] = useState('')
  const [selectedSuggestion, setSelectedSuggestion] = useState(suggestedQuestions[0])
  const typingTimer = useRef(null)

  const hasMessages = messages.length > 0

  const sendDraft = useCallback(
    (value = draft) => {
      const cleanValue = value.trim()
      if (!cleanValue || isTyping) return

      const userMessage = createMessage('user', cleanValue, 'website')
      setMessages((current) => [...current, userMessage])
      setDraft('')
      setIsTyping(true)

      window.clearTimeout(typingTimer.current)
      typingTimer.current = window.setTimeout(() => {
        const source = cleanValue.toLowerCase().includes('pdf') ? 'both' : 'website'
        const assistantMessage = createMessage('assistant', getAssistantReply(cleanValue), source)
        setMessages((current) => [...current, assistantMessage])
        setIsTyping(false)
      }, 850)
    },
    [draft, isTyping],
  )

  const selectSuggestion = useCallback((suggestion) => {
    setSelectedSuggestion(suggestion)
    setDraft(suggestion)
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
    setToast('Chat cleared')
  }, [])

  const exportChat = useCallback(() => {
    if (!messages.length) {
      setToast('No messages to export')
      return
    }
    downloadTextFile('tech-docs-ai-chat.txt', buildChatExport(messages))
    setToast('Chat exported')
  }, [messages])

  const regenerateLast = useCallback(() => {
    const lastUserMessage = [...messages].reverse().find((message) => message.role === 'user')
    if (lastUserMessage) sendDraft(lastUserMessage.content)
  }, [messages, sendDraft])

  const value = useMemo(
    () => ({
      messages,
      draft,
      setDraft,
      isTyping,
      hasMessages,
      selectedSuggestion,
      toast,
      setToast,
      sendDraft,
      selectSuggestion,
      clearMessages,
      exportChat,
      regenerateLast,
    }),
    [messages, draft, isTyping, hasMessages, selectedSuggestion, toast, sendDraft, selectSuggestion, clearMessages, exportChat, regenerateLast],
  )

  return value
}
