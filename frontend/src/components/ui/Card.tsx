import { ReactNode } from 'react'
import clsx from 'clsx'

interface CardProps {
    children: ReactNode
    className?: string
    hover?: boolean
    padding?: 'none' | 'sm' | 'md' | 'lg'
}

export function Card({ children, className, hover = false, padding = 'md' }: CardProps) {
    const paddingClass = {
        none: '',
        sm: 'p-3',
        md: 'p-5',
        lg: 'p-6'
    }

    return (
        <div className={clsx(
            'glass-card rounded-xl',
            paddingClass[padding],
            hover && 'hover:border-white/20 transition-colors cursor-pointer',
            className
        )}>
            {children}
        </div>
    )
}

// Card with header
interface CardWithHeaderProps extends CardProps {
    title: string
    subtitle?: string
    action?: ReactNode
}

export function CardWithHeader({
    title,
    subtitle,
    action,
    children,
    className
}: CardWithHeaderProps) {
    return (
        <div className={clsx('glass-card rounded-xl overflow-hidden', className)}>
            <div className="px-5 py-4 border-b border-white/10 flex items-center justify-between">
                <div>
                    <h3 className="font-semibold text-white">{title}</h3>
                    {subtitle && <p className="text-sm text-white/50">{subtitle}</p>}
                </div>
                {action}
            </div>
            <div className="p-5">
                {children}
            </div>
        </div>
    )
}

// Empty state card
interface EmptyStateProps {
    icon?: ReactNode
    title: string
    description?: string
    action?: ReactNode
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
    return (
        <div className="glass-card rounded-xl p-8 text-center">
            {icon && (
                <div className="mb-4 text-white/30">{icon}</div>
            )}
            <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
            {description && (
                <p className="text-white/50 mb-4 max-w-md mx-auto">{description}</p>
            )}
            {action}
        </div>
    )
}

// Loading card skeleton
export function CardSkeleton({ lines = 3 }: { lines?: number }) {
    return (
        <div className="glass-card rounded-xl p-5 animate-pulse">
            <div className="h-4 bg-white/10 rounded w-1/3 mb-4" />
            {Array.from({ length: lines }).map((_, i) => (
                <div
                    key={i}
                    className="h-3 bg-white/5 rounded mb-2"
                    style={{ width: `${100 - i * 15}%` }}
                />
            ))}
        </div>
    )
}
