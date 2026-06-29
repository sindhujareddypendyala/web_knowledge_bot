import { useState } from 'react'
import { FiCopy, FiRefreshCw, FiThumbsDown, FiThumbsUp } from 'react-icons/fi'
import SourceBadge from '../SourceBadge/SourceBadge.jsx'
import { renderMarkdownLite } from '../../utils/helpers.js'

export default function ChatMessage({ message, onRegenerate }) {
  const [copied, setCopied] = useState(false)
  const isAssistant = message.role === 'assistant'

  async function copyMessage() {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1200)
  }

  return (
    <article className={`flex ${isAssistant ? 'justify-start' : 'justify-end'}`}>
      <div className={`max-w-[88%] ${isAssistant ? 'items-start' : 'items-end'} flex flex-col`}>
        <div
          className={`prose-chat rounded-2xl px-4 py-3 text-sm leading-6 shadow-lg ${isAssistant ? 'rounded-bl-md border border-slate-800 bg-slate-900 text-slate-100' : 'rounded-br-md bg-blue-600 text-white'}`}
          dangerouslySetInnerHTML={{ __html: renderMarkdownLite(message.content) }}
        />
        <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
          <span>{message.time}</span>
          <button type="button" aria-label="Copy message" className="focus-ring rounded p-1 hover:text-blue-300" onClick={copyMessage}>
            <FiCopy aria-hidden="true" />
          </button>
          {isAssistant && (
            <>
              <button type="button" aria-label="Like response" className="focus-ring rounded p-1 hover:text-emerald-300"><FiThumbsUp aria-hidden="true" /></button>
              <button type="button" aria-label="Dislike response" className="focus-ring rounded p-1 hover:text-rose-300"><FiThumbsDown aria-hidden="true" /></button>
              <button type="button" aria-label="Regenerate response" className="focus-ring rounded p-1 hover:text-blue-300" onClick={onRegenerate}><FiRefreshCw aria-hidden="true" /></button>
            </>
          )}
          {copied && <span className="text-blue-300">Copied</span>}
        </div>
        {isAssistant && <SourceBadge source={message.source} />}
      </div>
    </article>
  )
}
