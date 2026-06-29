import { FiCopy } from 'react-icons/fi'
import { apiRows } from '../utils/constants.js'

export default function APIReference() {
  return (
    <section className="px-4 py-16 lg:px-6">
      <div className="mx-auto max-w-7xl">
        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-blue-300">API Reference</p>
        <h1 className="mt-3 text-4xl font-bold bg-gradient-to-r from-blue-400 via-cyan-300 to-teal-400 bg-clip-text text-transparent md:text-5xl">Frontend service contract</h1>
        <p className="mt-4 max-w-3xl leading-7 text-slate-300 font-medium">
          The UI is prepared to call these endpoints when your FastAPI or Flask backend is available.
        </p>
        <div className="mt-10 overflow-hidden rounded-lg border border-slate-700/60 bg-slate-800/40 backdrop-blur-xs">
          {apiRows.map((row) => (
            <div key={row.path} className="grid gap-3 border-b border-slate-700/50 p-5 last:border-b-0 md:grid-cols-[120px_220px_1fr_auto] md:items-center transition hover:bg-slate-800/20">
              <span className={`w-fit rounded-md px-3 py-1 text-xs font-extrabold tracking-wide ${row.method === 'GET' ? 'bg-emerald-500/15 text-emerald-350' : row.method === 'DELETE' ? 'bg-rose-500/15 text-rose-350' : 'bg-blue-500/15 text-blue-350'}`}>{row.method}</span>
              <code className="rounded-md bg-blue-500/8 border border-blue-400/20 px-3 py-2 text-sm font-bold text-blue-300 w-fit">{row.path}</code>
              <p className="text-sm leading-6 text-slate-300 font-medium">{row.description}</p>
              <button type="button" aria-label={`Copy ${row.path}`} className="focus-ring grid h-10 w-10 place-items-center rounded-lg border border-slate-700/60 text-slate-400 hover:border-blue-400 hover:text-blue-200 transition">
                <FiCopy aria-hidden="true" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
