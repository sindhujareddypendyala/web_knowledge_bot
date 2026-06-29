import DocumentationSection from '../components/Documentation/Documentation.jsx'
import Sidebar from '../components/layout/Sidebar/Sidebar.jsx'
import SearchBar from '../components/SearchBar/SearchBar.jsx'

export default function Documentation() {
  return (
    <section className="px-4 py-10 lg:px-6">
      <div className="mx-auto flex max-w-7xl gap-6">
        <Sidebar />
        <div className="min-w-0 flex-1">
          <div className="mb-8 rounded-lg border border-slate-700/60 bg-slate-800/45 p-6 backdrop-blur-xs">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-blue-300">Docs Hub</p>
            <h1 className="mt-3 text-4xl font-bold bg-gradient-to-r from-white via-blue-100 to-cyan-200 bg-clip-text text-transparent">Documentation</h1>
            <p className="mt-3 max-w-3xl text-slate-350 leading-relaxed">Browse authentication, APIs, SDK setup, webhooks, errors, examples, GraphQL, and CLI guidance.</p>
            <div className="mt-6"><SearchBar /></div>
          </div>
          <DocumentationSection title="Core Documentation" intro="Everything needed to connect your app to a future AI documentation backend." />
        </div>
      </div>
    </section>
  )
}
