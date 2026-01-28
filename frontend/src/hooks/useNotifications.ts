import { useEffect, useState, useCallback } from 'react'
import { useScanProgress, useAlerts } from './useWebSocket'
import { alertsApi } from '../services/api'

// Hook for managing toast notifications
export interface Toast {
    id: string
    type: 'success' | 'error' | 'warning' | 'info'
    title: string
    message?: string
    duration?: number
}

export function useToast() {
    const [toasts, setToasts] = useState<Toast[]>([])

    const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
        const id = Math.random().toString(36).substr(2, 9)
        const newToast = { ...toast, id }

        setToasts(prev => [...prev, newToast])

        // Auto-remove after duration
        const duration = toast.duration || 5000
        if (duration > 0) {
            setTimeout(() => {
                removeToast(id)
            }, duration)
        }

        return id
    }, [])

    const removeToast = useCallback((id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id))
    }, [])

    return { toasts, addToast, removeToast }
}

// Hook for real-time notifications with toast integration
export function useNotifications() {
    const { newAlert, isConnected } = useAlerts()
    const { toasts, addToast, removeToast } = useToast()
    const [unreadCount, setUnreadCount] = useState(0)

    // Fetch initial unread count
    useEffect(() => {
        alertsApi.getStats()
            .then(res => setUnreadCount(res.data.unread))
            .catch(() => { })
    }, [])

    // Listen for new alerts
    useEffect(() => {
        if (newAlert) {
            // Show toast notification
            addToast({
                type: newAlert.severity === 'critical' ? 'error' :
                    newAlert.severity === 'high' ? 'warning' : 'info',
                title: newAlert.title,
                message: newAlert.message,
                duration: 8000
            })

            // Increment unread count
            setUnreadCount(prev => prev + 1)
        }
    }, [newAlert, addToast])

    const markAllRead = useCallback(async () => {
        try {
            await alertsApi.markAllAsRead()
            setUnreadCount(0)
        } catch (e) {
            console.error('Failed to mark all as read', e)
        }
    }, [])

    return {
        toasts,
        removeToast,
        unreadCount,
        markAllRead,
        isConnected
    }
}

// Hook for live scan monitoring
export function useLiveScan(scanId?: string) {
    const { scanProgress, isConnected } = useScanProgress()
    const [currentScan, setCurrentScan] = useState<{
        id: string
        progress: number
        currentUrl: string
        status: string
    } | null>(null)

    useEffect(() => {
        if (scanProgress && (!scanId || scanProgress.scan_id === scanId)) {
            setCurrentScan({
                id: scanProgress.scan_id,
                progress: scanProgress.progress,
                currentUrl: scanProgress.current_url,
                status: scanProgress.status
            })
        }
    }, [scanProgress, scanId])

    return {
        currentScan,
        isConnected,
        isScanning: currentScan?.status === 'running'
    }
}

// Hook for auto-refreshing data
export function useAutoRefresh<T>(
    fetchFn: () => Promise<T>,
    intervalMs: number = 30000,
    enabled: boolean = true
) {
    const [data, setData] = useState<T | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)

    const refresh = useCallback(async () => {
        try {
            setLoading(true)
            const result = await fetchFn()
            setData(result)
            setError(null)
        } catch (e) {
            setError(e as Error)
        } finally {
            setLoading(false)
        }
    }, [fetchFn])

    useEffect(() => {
        refresh()

        if (enabled && intervalMs > 0) {
            const interval = setInterval(refresh, intervalMs)
            return () => clearInterval(interval)
        }
    }, [refresh, intervalMs, enabled])

    return { data, loading, error, refresh }
}

// Hook for debounced search
export function useDebounce<T>(value: T, delay: number = 300): T {
    const [debouncedValue, setDebouncedValue] = useState(value)

    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedValue(value)
        }, delay)

        return () => clearTimeout(timer)
    }, [value, delay])

    return debouncedValue
}

// Hook for local storage state
export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
    const [storedValue, setStoredValue] = useState<T>(() => {
        try {
            const item = window.localStorage.getItem(key)
            return item ? JSON.parse(item) : initialValue
        } catch (e) {
            return initialValue
        }
    })

    const setValue = useCallback((value: T) => {
        try {
            setStoredValue(value)
            window.localStorage.setItem(key, JSON.stringify(value))
        } catch (e) {
            console.error('Failed to save to localStorage', e)
        }
    }, [key])

    return [storedValue, setValue]
}
