import { suggestedQuestions } from '../../utils/constants.js'

export default function SuggestionChips({ onSelect }) {
  return (
    <div className="flex flex-wrap gap-2">
      {suggestedQuestions.map((question) => (
        <button
          key={question}
          type="button"
          onClick={() => onSelect(question)}
          className="focus-ring rounded-full border border-blue-500/20 bg-blue-950/15 px-3 py-1.5 text-xs font-semibold text-blue-350 transition hover:border-yellow-400/50 hover:text-yellow-400 hover:bg-yellow-500/5 hover:shadow-xs hover:shadow-yellow-500/5 cursor-pointer"
        >
          {question}
        </button>
      ))}
    </div>
  )
}
