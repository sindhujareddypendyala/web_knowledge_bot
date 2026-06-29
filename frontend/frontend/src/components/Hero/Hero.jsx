import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { FiArrowRight, FiBookOpen, FiCpu, FiFileText, FiMessageCircle, FiZap } from 'react-icons/fi'

export default function Hero() {
  return (
    <section className="relative overflow-hidden px-4 pb-16 pt-14 lg:px-6 lg:pb-24 lg:pt-20">
      <div className="mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-[1.03fr_0.97fr]">
        <motion.div initial={{ opacity: 0, y: 22 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55 }}>
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-amber-300/40 bg-amber-300/12 px-3 py-1.5 text-sm font-medium text-amber-100 shadow-lg shadow-amber-500/10">
            <FiZap aria-hidden="true" /> Documentation, PDFs, and AI in one workspace
          </div>
          <h1 className="text-balance bg-gradient-to-r from-white via-cyan-100 to-amber-100 bg-clip-text text-4xl font-extrabold leading-tight text-transparent sm:text-5xl lg:text-7xl">
            AI-Powered Technical Documentation
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
            Search documentation, ask AI questions, upload PDFs, and explore APIs in one place.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link to="/documentation" className="focus-ring inline-flex items-center justify-center gap-2 rounded-full bg-gradient-to-r from-blue-600 via-cyan-500 to-emerald-500 px-6 py-3 font-semibold text-white shadow-xl shadow-cyan-600/25 transition hover:brightness-110">
              Explore Documentation <FiArrowRight aria-hidden="true" />
            </Link>
            <a href="#assistant" className="focus-ring inline-flex items-center justify-center gap-2 rounded-full border border-amber-300/40 bg-amber-300/12 px-6 py-3 font-semibold text-amber-100 transition hover:border-amber-200 hover:bg-amber-300/18">
              Ask AI <FiMessageCircle aria-hidden="true" />
            </a>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.65, delay: 0.12 }}
          className="relative min-h-[420px]"
          aria-label="Developer, AI assistant, API connections, and documentation illustration"
        >
          <div className="glass-panel absolute inset-x-0 top-8 rounded-lg p-5">
            <div className="flex items-center justify-between border-b border-slate-700/70 pb-4">
              <div className="flex items-center gap-3">
                <span className="grid h-11 w-11 place-items-center rounded-lg bg-gradient-to-br from-cyan-400/25 to-blue-500/25 text-cyan-100"><FiCpu aria-hidden="true" /></span>
                <div>
                  <p className="font-semibold text-white">AI Documentation Runtime</p>
                  <p className="text-sm text-slate-400">Indexing docs and PDF sources</p>
                </div>
              </div>
              <span className="rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-300">Live</span>
            </div>
            <div className="mt-5 grid gap-3">
              {[
                ['Developer query', FiMessageCircle, 'How do webhooks retry?'],
                ['API connection', FiZap, 'POST /chat'],
                ['Documentation source', FiBookOpen, 'Webhook guide'],
                ['PDF source', FiFileText, 'Integration manual.pdf'],
              ].map(([label, Icon, text]) => (
                <motion.div
                  key={label}
                  animate={{ y: [0, -4, 0] }}
                  transition={{ duration: 3, repeat: Infinity, delay: label.length / 20 }}
                  className="flex items-center gap-3 rounded-lg border border-slate-600/70 bg-slate-800/55 p-3"
                >
                  <span className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-blue-500/20 via-cyan-400/20 to-amber-300/20 text-cyan-100"><Icon aria-hidden="true" /></span>
                  <div>
                    <p className="text-xs text-slate-500">{label}</p>
                    <p className="text-sm font-medium text-slate-100">{text}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
          <motion.div
            animate={{ rotate: [0, 2, -2, 0], y: [0, -8, 0] }}
            transition={{ duration: 5, repeat: Infinity }}
            className="absolute bottom-2 right-6 grid h-24 w-24 place-items-center rounded-full border border-amber-200/50 bg-gradient-to-br from-blue-600 via-cyan-500 to-amber-400 text-4xl text-white shadow-2xl shadow-cyan-600/35"
          >
            <FiCpu aria-hidden="true" />
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}
