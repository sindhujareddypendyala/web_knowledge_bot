import { motion } from 'framer-motion'

export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 rounded-2xl rounded-bl-md border border-slate-800 bg-slate-900 px-4 py-3 text-slate-300">
      <span className="text-sm">AI is thinking</span>
      {[0, 1, 2].map((dot) => (
        <motion.span
          key={dot}
          animate={{ opacity: [0.25, 1, 0.25], y: [0, -3, 0] }}
          transition={{ duration: 0.9, repeat: Infinity, delay: dot * 0.15 }}
          className="h-1.5 w-1.5 rounded-full bg-blue-300"
        />
      ))}
    </div>
  )
}
