import { Link } from 'react-router-dom'
import { FiGithub, FiLayers, FiShield, FiCpu, FiBookOpen } from 'react-icons/fi'

export default function Footer() {
  return (
    <footer className="relative z-10 border-t border-yellow-400/40 bg-gradient-to-br from-yellow-300 via-amber-300 to-yellow-500 py-16 px-4 md:px-8 text-slate-950 shadow-2xl">
      <div className="mx-auto max-w-7xl">
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-4 pb-12 border-b border-slate-950/15">
          {/* Column 1: Brand */}
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-slate-950 text-lg font-black text-yellow-400">T</span>
              <span className="text-xl font-extrabold tracking-tight">TechDocs AI</span>
            </div>
            <p className="text-sm font-semibold leading-relaxed text-slate-800">
              Interactive technical documentation hub with RAG-ready PDF analysis, instant semantic search, and developer-focused playground.
            </p>
            <div className="mt-2 text-xs font-bold bg-slate-950/10 p-3 rounded-lg border border-slate-950/10">
              Built by <span className="font-extrabold text-slate-950">Team Hufflepuff</span> for GenAI Internship
              <br />
              <span className="text-slate-700">Guided by Augur CyberX Intelligence System</span>
            </div>
          </div>

          {/* Column 2: Navigation */}
          <div>
            <h3 className="text-sm font-extrabold uppercase tracking-wider text-slate-950 mb-4">Workspace</h3>
            <ul className="grid gap-2.5 text-sm font-bold text-slate-800">
              <li><Link to="/" className="hover:text-slate-950 hover:underline">Home Dashboard</Link></li>
              <li><Link to="/documentation" className="hover:text-slate-950 hover:underline">Core Documentation</Link></li>
              <li><Link to="/api-reference" className="hover:text-slate-950 hover:underline">API References</Link></li>
              <li><Link to="/sdk" className="hover:text-slate-950 hover:underline">SDK Integration</Link></li>
            </ul>
          </div>

          {/* Column 3: Resources */}
          <div>
            <h3 className="text-sm font-extrabold uppercase tracking-wider text-slate-950 mb-4">Resources</h3>
            <ul className="grid gap-2.5 text-sm font-bold text-slate-800">
              <li><Link to="/tutorials" className="hover:text-slate-950 hover:underline">Step-by-Step Tutorials</Link></li>
              <li><Link to="/guides" className="hover:text-slate-950 hover:underline">Developer Guides</Link></li>
              <li><Link to="/faq" className="hover:text-slate-950 hover:underline">Frequently Asked Questions</Link></li>
              <li><a href="#assistant" className="hover:text-slate-950 hover:underline">Ask AI Assistant</a></li>
            </ul>
          </div>

          {/* Column 4: Platform capabilities */}
          <div>
            <h3 className="text-sm font-extrabold uppercase tracking-wider text-slate-950 mb-4">Capabilities</h3>
            <div className="flex flex-col gap-2">
              <span className="inline-flex items-center gap-2 rounded-lg bg-slate-950/10 px-3.5 py-2 text-xs font-bold border border-slate-950/5">
                <FiShield className="text-slate-950 text-sm" /> Accessible Design UI
              </span>
              <span className="inline-flex items-center gap-2 rounded-lg bg-slate-950/10 px-3.5 py-2 text-xs font-bold border border-slate-950/5">
                <FiLayers className="text-slate-950 text-sm" /> PDF RAG Engine Ready
              </span>
              <span className="inline-flex items-center gap-2 rounded-lg bg-slate-950/10 px-3.5 py-2 text-xs font-bold border border-slate-950/5">
                <FiCpu className="text-slate-950 text-sm" /> Gemini & Groq Ready
              </span>
            </div>
          </div>
        </div>

        <div className="mt-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between text-xs font-bold text-slate-700">
          <p>© {new Date().getFullYear()} TechDocs AI & Team Hufflepuff. All rights reserved.</p>
          <div className="flex gap-4">
            <a href="https://github.com" target="_blank" rel="noreferrer" className="flex items-center gap-1.5 hover:text-slate-950">
              <FiGithub className="text-sm" /> GitHub Repository
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}
