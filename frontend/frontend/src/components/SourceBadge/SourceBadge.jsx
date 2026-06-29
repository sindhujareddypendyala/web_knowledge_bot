import { FiFileText, FiGlobe } from 'react-icons/fi'

export default function SourceBadge({ source = 'website' }) {
  const content = {
    website: { label: 'Website Knowledge', icon: FiGlobe },
    pdf: { label: 'PDF Knowledge', icon: FiFileText },
    both: { label: 'Website + PDF', icon: FiGlobe },
  }[source]

  const Icon = content.icon

  return (
    <span className="mt-3 inline-flex w-fit items-center gap-2 rounded-full border border-slate-700 bg-slate-950/70 px-3 py-1 text-xs font-medium text-slate-300">
      <Icon aria-hidden="true" />
      {content.label}
    </span>
  )
}
