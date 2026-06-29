import { NavLink } from 'react-router-dom'
import { navItems, recentChats } from '../../../utils/constants.js'

export default function Sidebar() {
  return (
    <aside className="glass-panel hidden w-72 shrink-0 rounded-lg p-4 lg:block">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-blue-300">Workspace</p>
      <div className="mt-4 grid gap-1">
        {navItems.slice(1).map((item) => (
          <NavLink
            key={item.href}
            to={item.href}
            className={({ isActive }) =>
              `rounded-lg px-3 py-2 text-sm transition ${isActive ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800/80'}`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </div>
      <div className="mt-7">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Recent chats</p>
        <div className="mt-3 grid gap-2">
          {recentChats.map((chat) => (
            <button key={chat} type="button" className="focus-ring rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-2 text-left text-sm text-slate-300 hover:border-blue-500">
              {chat}
            </button>
          ))}
        </div>
      </div>
    </aside>
  )
}
