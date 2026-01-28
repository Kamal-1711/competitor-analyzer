import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { useEffect, useState } from 'react'
import clsx from 'clsx'

interface Toast {
    id: string
    type: 'success' | 'error' | 'warning' | 'info'
    title: string
    message?: string
}

interface ToastContainerProps {
    toasts: Toast[]
    onRemove: (id: string) => void
}

const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info
}

const colors = {
    success: 'bg-accent-green/20 border-accent-green/30 text-accent-green',
    error: 'bg-accent-red/20 border-accent-red/30 text-accent-red',
    warning: 'bg-accent-orange/20 border-accent-orange/30 text-accent-orange',
    info: 'bg-accent-blue/20 border-accent-blue/30 text-accent-blue'
}

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
    return (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
            {toasts.map(toast => (
                <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
            ))}
        </div>
    )
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
    const [isVisible, setIsVisible] = useState(false)
    const Icon = icons[toast.type]

    useEffect(() => {
        // Animate in
        requestAnimationFrame(() => setIsVisible(true))
    }, [])

    const handleClose = () => {
        setIsVisible(false)
        setTimeout(() => onRemove(toast.id), 200)
    }

    return (
        <div
            className={clsx(
                'glass-card p-4 rounded-xl border transition-all duration-200 transform',
                colors[toast.type],
                isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'
            )}
        >
            <div className="flex items-start gap-3">
                <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-white">{toast.title}</h4>
                    {toast.message && (
                        <p className="text-sm text-white/70 mt-1">{toast.message}</p>
                    )}
                </div>
                <button
                    onClick={handleClose}
                    className="p-1 hover:bg-white/10 rounded-lg transition-colors"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>
        </div>
    )
}
