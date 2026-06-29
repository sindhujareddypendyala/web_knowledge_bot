import { FiHelpCircle } from 'react-icons/fi'
import { faqItems } from '../utils/constants.js'

export default function FAQ() {
  return (
    <section className="px-4 py-16 lg:px-6">
      <div className="mx-auto max-w-4xl">
        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-blue-300">FAQ</p>
        <h1 className="mt-3 text-4xl font-bold bg-gradient-to-r from-blue-400 via-cyan-300 to-teal-400 bg-clip-text text-transparent md:text-5xl">Common questions</h1>
        <div className="mt-10 grid gap-4">
          {faqItems.map((item) => (
            <article key={item.question} className="group rounded-lg border border-slate-700/60 bg-slate-800/40 p-6 transition hover:border-blue-400/50 hover:bg-slate-800/65 hover:shadow-lg hover:shadow-blue-500/5 backdrop-blur-xs">
              <div className="flex items-start gap-3">
                <FiHelpCircle className="mt-1 shrink-0 text-blue-300 group-hover:text-blue-400 transition" aria-hidden="true" />
                <div>
                  <h2 className="text-xl font-semibold text-white group-hover:text-blue-200 transition">{item.question}</h2>
                  <p className="mt-3 leading-7 text-slate-350">{item.answer}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
