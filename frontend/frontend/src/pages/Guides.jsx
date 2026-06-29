import { FiCheckCircle } from 'react-icons/fi'

const guideItems = [
  'Install the SDK package for your platform.',
  'Create a client with environment-provided credentials.',
  'Send documentation queries through your backend.',
  'Render assistant responses with source badges.',
  'Upload PDFs only through secure server endpoints.',
]

export default function Guides({ sdkOnly = false }) {
  return (
    <section className="px-4 py-16 lg:px-6">
      <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-cyan-300">{sdkOnly ? 'SDK' : 'Guides'}</p>
          <h1 className="mt-3 text-4xl font-bold bg-gradient-to-r from-cyan-400 via-teal-300 to-blue-450 bg-clip-text text-transparent md:text-5xl">{sdkOnly ? 'SDK integration guide' : 'Developer implementation guides'}</h1>
          <p className="mt-4 leading-7 text-slate-300 font-medium">
            Practical guidance for connecting this frontend to production documentation search, chat, source attribution, and PDF workflows.
          </p>
        </div>
        <div className="rounded-lg border border-slate-700/60 bg-slate-800/40 p-6 backdrop-blur-xs">
          <div className="rounded-lg bg-slate-950/70 border border-slate-850 p-4 font-mono text-sm leading-7 text-blue-200">
            npm install @your-org/techdocs-ai<br />
            export VITE_API_BASE_URL=http://localhost:8000<br />
            npm run dev
          </div>
          <div className="mt-6 grid gap-3">
            {guideItems.map((item) => (
              <div key={item} className="flex items-start gap-3 rounded-lg border border-slate-800/60 bg-slate-950/30 p-3 text-slate-300 hover:border-emerald-400/45 transition">
                <FiCheckCircle className="mt-1 shrink-0 text-emerald-350" aria-hidden="true" />
                <span className="text-sm font-medium">{item}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
