export type Theme = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'webspy_theme'

export function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'dark'
  return window.matchMedia?.('(prefers-color-scheme: dark)')?.matches ? 'dark' : 'light'
}

export function resolveTheme(theme: Theme): 'light' | 'dark' {
  return theme === 'system' ? getSystemTheme() : theme
}

export function getInitialTheme(): Theme {
  if (typeof window === 'undefined') return 'dark'
  const stored = window.localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark' || stored === 'system') return stored
  return 'system'
}

export function persistTheme(theme: Theme) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(STORAGE_KEY, theme)
}

export function applyResolvedTheme(resolved: 'light' | 'dark') {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  root.dataset.theme = resolved
  // Helps built-in form controls match theme
  root.style.colorScheme = resolved
}

