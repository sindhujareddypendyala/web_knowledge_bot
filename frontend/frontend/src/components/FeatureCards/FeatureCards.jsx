import { motion } from 'framer-motion'
import { featureCards } from '../../utils/constants.js'

export default function FeatureCards() {
  return (
    <section className="border-y border-slate-700/50 bg-slate-800/20 px-4 py-16 lg:px-6 backdrop-blur-xs">
      <div className="mx-auto max-w-7xl">
        <div className="mb-9 max-w-3xl">
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-emerald-300">Platform Features</p>
          <h2 className="mt-3 text-3xl font-bold bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent md:text-4xl">Premium AI documentation workflows</h2>
          <p className="mt-4 text-slate-300 font-medium">Every surface is ready for real retrieval, attribution, and model orchestration once the backend is connected.</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {featureCards.map((feature, index) => {
            const Icon = feature.icon
            return (
              <motion.article
                key={feature.title}
                initial={{ opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.35, delay: index * 0.025 }}
                whileHover={{ y: -5, scale: 1.02 }}
                className="group rounded-lg border border-slate-700/60 bg-slate-800/40 p-5 transition hover:border-emerald-400/50 hover:bg-slate-800/65 hover:shadow-lg hover:shadow-emerald-500/5 backdrop-blur-xs"
              >
                <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/12 text-2xl text-emerald-300 transition group-hover:bg-emerald-500 group-hover:text-slate-950">
                  <Icon aria-hidden="true" />
                </div>
                <h3 className="mt-4 font-semibold text-white group-hover:text-emerald-200">{feature.title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-350">{feature.description}</p>
              </motion.article>
            )
          })}
        </div>
      </div>
    </section>
  )
}
