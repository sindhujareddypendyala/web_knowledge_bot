import { FiMoon, FiSun } from 'react-icons/fi'
import { useTheme } from '../../hooks/useTheme.js'

export default function ThemeToggle() {
  const { isDark, toggleTheme } = useTheme()
  const Icon = isDark ? FiSun : FiMoon

  return (
    <button
      type="button"
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      onClick={toggleTheme}
      className="focus-ring grid h-10 w-10 place-items-center rounded-full border border-slate-700/70 bg-slate-900/75 text-slate-100 transition hover:border-blue-400 hover:text-blue-200 data-[light=true]:border-slate-300 data-[light=true]:bg-white data-[light=true]:text-slate-700"
      data-light={!isDark}
      title={isDark ? 'Light mode' : 'Dark mode'}
    >
      <Icon aria-hidden="true" />
    </button>
  )
}
