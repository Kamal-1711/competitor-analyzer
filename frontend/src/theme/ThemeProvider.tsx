import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { applyResolvedTheme, getInitialTheme, getSystemTheme, persistTheme, resolveTheme, type Theme } from './theme'

type ThemeContextValue = {
  theme: Theme
  resolvedTheme: 'light' | 'dark'
  setTheme: (t: Theme) => void
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => getInitialTheme())
  const [systemTheme, setSystemTheme] = useState<'light' | 'dark'>(() => getSystemTheme())

  // Track system theme changes (only relevant when theme === 'system')
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    const mql = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => setSystemTheme(mql.matches ? 'dark' : 'light')

    // Initial sync
    handler()

    // Add listener (browser compatibility)
    if (typeof mql.addEventListener === 'function') {
      mql.addEventListener('change', handler)
      return () => mql.removeEventListener('change', handler)
    }
    // Older Safari
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(mql as any).addListener?.(handler)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return () => (mql as any).removeListener?.(handler)
  }, [])

  const resolvedTheme = useMemo(() => {
    return theme === 'system' ? systemTheme : resolveTheme(theme)
  }, [theme, systemTheme])

  useEffect(() => {
    applyResolvedTheme(resolvedTheme)
  }, [resolvedTheme])

  const setTheme = (t: Theme) => {
    setThemeState(t)
    persistTheme(t)
  }

  const toggleTheme = () => {
    // toggle between resolved light/dark; keep user out of 'system' when explicitly toggling
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')
  }

  const value: ThemeContextValue = {
    theme,
    resolvedTheme,
    setTheme,
    toggleTheme,
  }

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}

