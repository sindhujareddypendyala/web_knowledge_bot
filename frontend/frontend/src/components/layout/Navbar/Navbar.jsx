import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { FiMenu, FiMessageCircle, FiX } from 'react-icons/fi'
import { navItems } from '../../../utils/constants.js'
import SearchBar from '../../SearchBar/SearchBar.jsx'
import ThemeToggle from '../../ThemeToggle/ThemeToggle.jsx'

export default function Navbar() {
  const [open, setOpen] = useState(false)

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/72 backdrop-blur-xl">
      <nav className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 lg:px-6" aria-label="Primary">
        <NavLink to="/" className="focus-ring flex items-center gap-3 rounded-lg" onClick={() => setOpen(false)}>
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-blue-600 text-lg font-black text-white shadow-lg shadow-blue-600/30">T</span>
          <span className="hidden text-sm font-semibold text-slate-100 sm:block">TechDocs AI</span>
        </NavLink>

        <div className="hidden items-center gap-1 rounded-full border border-slate-800 bg-slate-950/65 p-1 lg:flex">
          {navItems.map((item) => (
            <NavLink
              key={item.href}
              to={item.href}
              className={({ isActive }) =>
                `rounded-full px-3 py-2 text-sm font-medium transition ${isActive ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white'}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <SearchBar compact />
          <ThemeToggle />
          <a
            href="#assistant"
            className="focus-ring hidden items-center gap-2 rounded-full bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-blue-600/25 transition hover:bg-blue-500 md:inline-flex"
          >
            <FiMessageCircle aria-hidden="true" /> AI Assistant
          </a>
          <button
            type="button"
            aria-label="Toggle navigation menu"
            className="focus-ring grid h-10 w-10 place-items-center rounded-full border border-slate-700 text-slate-100 lg:hidden"
            onClick={() => setOpen((value) => !value)}
          >
            {open ? <FiX aria-hidden="true" /> : <FiMenu aria-hidden="true" />}
          </button>
        </div>
      </nav>

      {open && (
        <div className="border-t border-slate-800 bg-slate-950 px-4 py-4 lg:hidden">
          <div className="mx-auto grid max-w-7xl gap-2">
            {navItems.map((item) => (
              <NavLink
                key={item.href}
                to={item.href}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-3 text-sm font-medium ${isActive ? 'bg-slate-800 text-white' : 'text-slate-300'}`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        </div>
      )}
    </header>
  )
}
