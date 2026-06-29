import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { FiCpu } from 'react-icons/fi'
import ChatWidget from '../ChatWidget/ChatWidget.jsx'

export default function FloatingAssistant() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <button
        type="button"
        aria-label="AI Assistant"
        title="AI Assistant"
        onClick={() => setOpen(true)}
        className="focus-ring fixed bottom-5 right-5 z-50 grid h-16 w-16 place-items-center rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 text-2xl text-white shadow-2xl shadow-blue-500/40 transition hover:scale-105"
      >
        <motion.span
          animate={{ scale: [1, 1.1, 1], opacity: [1, 0.86, 1] }}
          transition={{ duration: 1.8, repeat: Infinity }}
          className="absolute inset-0 rounded-full ring-4 ring-blue-400/30"
        />
        <FiCpu aria-hidden="true" className="relative" />
        <span className="pointer-events-none absolute right-20 hidden whitespace-nowrap rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm font-medium text-slate-100 shadow-xl md:block">
          AI Assistant
        </span>
      </button>

      <AnimatePresence>
        {open && (
          <>
            <motion.button
              type="button"
              aria-label="Close assistant overlay"
              className="fixed inset-0 z-50 bg-slate-950/55 backdrop-blur-sm md:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setOpen(false)}
            />
            <motion.div
              className="fixed bottom-0 right-0 z-50 h-[100dvh] w-full overflow-hidden border-l border-slate-700/60 bg-slate-900 shadow-2xl sm:w-[380px] lg:w-[420px]"
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', stiffness: 280, damping: 32 }}
            >
              <ChatWidget onClose={() => setOpen(false)} onMinimize={() => setOpen(false)} />
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
