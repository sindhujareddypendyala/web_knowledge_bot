import { motion } from 'framer-motion'
import { FiCommand, FiSearch } from 'react-icons/fi'

export default function SearchBar({ compact = false }) {
  return (
    <motion.label
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
      className={`group focus-within:border-blue-400 focus-within:ring-4 focus-within:ring-blue-500/15 ${compact ? 'hidden w-56 lg:flex' : 'mx-auto flex w-full max-w-3xl'} items-center gap-3 rounded-full border border-slate-700/70 bg-slate-950/70 px-4 py-3 text-slate-300 shadow-2xl shadow-blue-950/20 backdrop-blur data-[compact=true]:py-2`}
      data-compact={compact}
    >
      <FiSearch className="shrink-0 text-blue-300" aria-hidden="true" />
      <input
        aria-label="Search documentation"
        placeholder="Search documentation..."
        className="min-w-0 flex-1 bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500"
      />
      <span className="hidden items-center gap-1 rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-400 sm:flex">
        <FiCommand aria-hidden="true" /> K
      </span>
    </motion.label>
  )
}
