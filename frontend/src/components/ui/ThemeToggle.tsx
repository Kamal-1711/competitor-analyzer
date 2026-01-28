import { Moon, Sun } from 'lucide-react'
import { IconButton } from './Button'
import { useTheme } from '../../theme/ThemeProvider'

export function ThemeToggle() {
  const { resolvedTheme, toggleTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'

  return (
    <IconButton
      type="button"
      variant="secondary"
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Light mode' : 'Dark mode'}
      onClick={toggleTheme}
      icon={
        isDark ? (
          <Sun className="w-4 h-4" />
        ) : (
          <Moon className="w-4 h-4" />
        )
      }
      className="hidden md:inline-flex"
    />
  )
}

