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
        {isAssistant && message.sources && message.sources.length > 0 && (
          <div className="mt-2 flex w-full flex-col gap-1.5 rounded-xl border border-slate-800 bg-slate-950/45 p-3 text-xs">
            <span className="font-semibold text-slate-400">Sources:</span>
            <ul className="flex flex-col gap-1 list-none p-0 m-0">
              {message.sources.map((src, idx) => (
                <li key={idx} className="flex items-center gap-1.5 text-slate-300">
                  <span className="text-blue-400 font-medium">[{idx + 1}]</span>
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 hover:underline transition truncate max-w-[280px]"
                    title={src.title || src.url}
                  >
                    {src.title || src.url}
                  </a>
                  {src.confidence && (
                    <span className="text-[10px] text-slate-500 font-medium ml-auto bg-slate-900/60 px-1.5 py-0.5 rounded-md">
                      {Math.round(src.confidence * 100)}% Match
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </article>
  )
}

