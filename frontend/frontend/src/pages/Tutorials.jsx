import { FiArrowRight, FiClock } from 'react-icons/fi'
import { tutorials } from '../utils/constants.js'

export default function Tutorials() {
  return (
    <section className="px-4 py-16 lg:px-6">
      <div className="mx-auto max-w-7xl">
        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-emerald-300">Tutorials</p>
        <h1 className="mt-3 text-4xl font-bold bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent md:text-5xl">Build AI documentation experiences step by step</h1>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {tutorials.map((tutorial) => (
            <article key={tutorial.title} className="group rounded-lg border border-slate-700/60 bg-slate-800/40 p-6 transition hover:border-emerald-400/50 hover:bg-slate-800/65 hover:shadow-lg hover:shadow-emerald-500/5 backdrop-blur-xs">
              <span className="rounded-full bg-emerald-500/12 px-3 py-1 text-xs font-extrabold text-emerald-300 group-hover:bg-emerald-500 group-hover:text-slate-950 transition">{tutorial.level}</span>
              <h2 className="mt-5 text-xl font-semibold text-white group-hover:text-emerald-200 transition">{tutorial.title}</h2>
              <p className="mt-3 leading-6 text-slate-350">{tutorial.description}</p>
              <div className="mt-6 flex items-center justify-between text-sm">
                <span className="inline-flex items-center gap-2 text-slate-400"><FiClock aria-hidden="true" /> {tutorial.time}</span>
                <button type="button" className="focus-ring inline-flex items-center gap-2 rounded-md font-semibold text-cyan-300 hover:text-cyan-200 hover:underline">
                  Start <FiArrowRight aria-hidden="true" />
                </button>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
