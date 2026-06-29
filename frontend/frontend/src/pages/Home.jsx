import Hero from '../components/Hero/Hero.jsx'
import DocumentationSection from '../components/Documentation/Documentation.jsx'
import FeatureCards from '../components/FeatureCards/FeatureCards.jsx'
import UploadPDF from '../components/UploadPDF/UploadPDF.jsx'

export default function Home() {
  return (
    <>
      <Hero />
      <DocumentationSection />
      <FeatureCards />
      <section className="px-4 py-16 lg:px-6">
        <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-cyan-300">PDF Knowledge</p>
            <h2 className="mt-3 text-3xl font-bold text-white md:text-4xl">Upload documentation and keep the conversation grounded</h2>
            <p className="mt-4 leading-7 text-slate-400">
              The frontend validates PDF files, shows progress, and presents success states so a future backend can focus on parsing, embeddings, and retrieval.
            </p>
          </div>
          <UploadPDF />
        </div>
      </section>
    </>
  )
}
