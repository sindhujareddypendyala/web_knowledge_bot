import { useEffect, useMemo, useState } from 'react'
import { ThemeContext } from './useTheme.js'

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => localStorage.getItem('techdocs-theme') || 'dark')

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('techdocs-theme', theme)
  }, [theme])

  const value = useMemo(
    () => ({
      theme,
      isDark: theme === 'dark',
      toggleTheme: () => setTheme((current) => (current === 'dark' ? 'light' : 'dark')),
    }),
    [theme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
