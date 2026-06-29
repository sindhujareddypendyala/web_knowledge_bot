import { motion } from 'framer-motion'
import { docCards } from '../../utils/constants.js'

export default function Documentation({ title = 'Browse Documentation', intro = 'Beautifully organized references for every developer workflow.' }) {
  return (
    <section className="px-4 py-16 lg:px-6" id="documentation">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-blue-300">Documentation</p>
            <h2 className="mt-3 text-3xl font-bold bg-gradient-to-r from-blue-400 via-cyan-300 to-teal-400 bg-clip-text text-transparent md:text-4xl">{title}</h2>
          </div>
          <p className="max-w-2xl text-slate-300 font-medium">{intro}</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {docCards.map((card, index) => {
            const Icon = card.icon
            return (
              <motion.article
                key={card.title}
                initial={{ opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-80px' }}
                transition={{ duration: 0.35, delay: index * 0.03 }}
                whileHover={{ y: -6, scale: 1.01 }}
                className="group rounded-lg border border-slate-700/50 bg-slate-800/40 p-5 transition hover:border-blue-400 hover:bg-slate-800/60 hover:shadow-lg hover:shadow-blue-500/5 backdrop-blur-xs"
              >
                <div className="mb-5 grid h-11 w-11 place-items-center rounded-lg bg-blue-500/12 text-xl text-blue-350 group-hover:bg-blue-600 group-hover:text-white transition">
                  <Icon aria-hidden="true" />
                </div>
                <h3 className="text-lg font-semibold text-white group-hover:text-blue-200">{card.title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-350">{card.description}</p>
              </motion.article>
            )
          })}
        </div>
      </div>
    </section>
  )
}
