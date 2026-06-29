import { useEffect, useRef } from 'react'
import { FiMinus, FiSend, FiUploadCloud, FiX, FiCpu } from 'react-icons/fi'
import ChatMessage from '../ChatMessage/ChatMessage.jsx'
import SuggestionChips from '../SuggestionChips/SuggestionChips.jsx'
import TypingIndicator from '../TypingIndicator/TypingIndicator.jsx'
import UploadPDF from '../UploadPDF/UploadPDF.jsx'
import { useChat } from '../../hooks/useChat.js'
import { uploadPDF } from '../../services/api.js'

export default function ChatWidget({ onClose, onMinimize }) {
  const chat = useChat()
  const bottomRef = useRef(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chat.messages, chat.isTyping])

  useEffect(() => {
    function handleShortcut(event) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        document.getElementById('assistant-input')?.focus()
      }
    }
    window.addEventListener('keydown', handleShortcut)
    return () => window.removeEventListener('keydown', handleShortcut)
  }, [])

  async function handleFileInputChange(event) {
    const file = event.target.files[0]
    if (!file) return
    if (file.type !== 'application/pdf') {
      chat.setToast('Please upload a valid PDF file.')
      return
    }

    chat.setToast(`Uploading and indexing ${file.name}...`)
    try {
      await uploadPDF(file)
      chat.setToast(`Successfully indexed ${file.name}!`)
      
      const successMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `Successfully uploaded and indexed **"${file.name}"**! You can now ask questions about its contents.`,
        source: 'pdf',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        createdAt: Date.now()
      }
      chat.setMessages((current) => [...current, successMessage])
    } catch (err) {
      console.error('Failed to upload PDF:', err)
      chat.setToast('Failed to upload and index PDF.')
    }
  }

  return (
    <section
      id="assistant"
      aria-label="AI Assistant chat panel"
      className="flex h-full flex-col overflow-hidden bg-slate-900 text-slate-100 shadow-2xl shadow-slate-950/80"
    >
      <header className="flex items-center justify-between border-b border-slate-700/60 px-4 py-4 bg-slate-950/20 backdrop-blur-xs">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-blue-500 via-indigo-500 to-yellow-400 text-slate-950 shadow-lg shadow-blue-500/10">
            <FiCpu aria-hidden="true" className="text-xl" />
          </div>
          <div>
            <h2 className="text-sm font-extrabold tracking-tight text-white">AI Assistant</h2>
            <p className="text-[10px] font-bold text-yellow-400 uppercase tracking-wider">Web & PDF RAG</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <button type="button" aria-label="Minimize assistant" title="Minimize" className="focus-ring rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition" onClick={onMinimize}>
            <FiMinus aria-hidden="true" className="text-sm" />
          </button>
          <button type="button" aria-label="Close assistant" title="Close" className="focus-ring rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition" onClick={onClose}>
            <FiX aria-hidden="true" className="text-sm" />
          </button>
        </div>
      </header>

      {chat.toast && (
        <div role="status" className="mx-4 mt-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
          {chat.toast}
        </div>
      )}

      <div className="scrollbar-slim flex-1 overflow-y-auto px-4 py-5">
        {!chat.hasMessages && (
          <div className="grid gap-5">
            <div className="rounded-xl border border-blue-500/20 bg-gradient-to-br from-blue-950/20 via-slate-900 to-yellow-950/10 p-6 text-center backdrop-blur-xs">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-yellow-400 p-0.5 shadow-md shadow-blue-500/10">
                <div className="flex h-full w-full items-center justify-center rounded-full bg-slate-900 text-yellow-400 text-sm font-extrabold">
                  AI
                </div>
              </div>
              <h3 className="mt-4 text-base font-extrabold text-white">How can I help?</h3>
              <p className="mt-1.5 text-xs text-slate-305 leading-relaxed">
                Ask questions or upload a PDF to get started with <span className="text-blue-300 font-semibold">TechDocs</span> <span className="text-yellow-450 font-semibold">AI</span>.
              </p>
            </div>
            <SuggestionChips onSelect={chat.selectSuggestion} />
            <UploadPDF onUploaded={(file) => {
              chat.setToast(`Successfully indexed ${file.name}!`)
              const successMessage = {
                id: crypto.randomUUID(),
                role: 'assistant',
                content: `Successfully uploaded and indexed **"${file.name}"**! You can now ask questions about its contents.`,
                source: 'pdf',
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                createdAt: Date.now()
              }
              chat.setMessages((current) => [...current, successMessage])
            }} />
          </div>
        )}

        <div className="grid gap-5">
          {chat.messages.map((message) => (
            <ChatMessage key={message.id} message={message} onRegenerate={chat.regenerateLast} />
          ))}
          {chat.isTyping && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      </div>

      <div className="border-t border-slate-700/60 p-4 bg-slate-950/10">
        <form
          onSubmit={(event) => {
            event.preventDefault()
            chat.sendDraft()
          }}
          className="flex items-center gap-2 rounded-full border border-blue-500/30 bg-slate-950/40 p-1.5 focus-within:border-blue-450 focus-within:ring-4 focus-within:ring-blue-500/15"
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            className="sr-only"
            onChange={handleFileInputChange}
          />
          <button
            type="button"
            aria-label="Upload PDF"
            title="Upload PDF documentation"
            onClick={() => fileInputRef.current?.click()}
            className="focus-ring grid h-9 w-9 shrink-0 place-items-center rounded-full text-slate-400 hover:bg-slate-800 hover:text-blue-300 transition"
          >
            <FiUploadCloud aria-hidden="true" />
          </button>
          <input
            id="assistant-input"
            type="text"
            aria-label="Ask anything about the documentation"
            value={chat.draft}
            onChange={(event) => chat.setDraft(event.target.value)}
            placeholder="Ask AI assistant..."
            className="min-w-0 flex-1 bg-transparent px-1 text-sm text-white outline-none placeholder:text-slate-500"
          />
          <button
            type="submit"
            disabled={!chat.draft.trim() || chat.isTyping}
            aria-label="Send message"
            className="focus-ring grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gradient-to-r from-blue-500 to-yellow-400 text-slate-950 font-bold shadow-md hover:brightness-110 disabled:opacity-40 transition"
          >
            <FiSend aria-hidden="true" className="text-sm" />
          </button>
        </form>
      </div>
    </section>
  )
}
