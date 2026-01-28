import { LucideIcon } from 'lucide-react'
import clsx from 'clsx'

interface StatCardProps {
    title: string
    value: string | number
    change?: number
    changeLabel?: string
    icon?: LucideIcon
    iconColor?: string
    trend?: 'up' | 'down' | 'neutral'
    className?: string
}

export function StatCard({
    title,
    value,
    change,
    changeLabel = 'vs last period',
    icon: Icon,
    iconColor = 'text-accent-purple',
    className
}: StatCardProps) {
    const showChange = change !== undefined

    return (
        <div className={clsx('glass-card p-5 rounded-xl', className)}>
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm text-white/50 mb-1">{title}</p>
                    <p className="text-2xl font-bold text-white">{value}</p>

                    {showChange && (
                        <div className="flex items-center gap-1.5 mt-2">
                            <span className={clsx(
                                'text-sm font-medium',
                                change > 0 ? 'text-accent-green' :
                                    change < 0 ? 'text-accent-red' :
                                        'text-white/50'
                            )}>
                                {change > 0 ? '+' : ''}{change}%
                            </span>
                            <span className="text-xs text-white/40">{changeLabel}</span>
                        </div>
                    )}
                </div>

                {Icon && (
                    <div className={clsx('p-3 rounded-xl bg-white/5', iconColor)}>
                        <Icon className="w-6 h-6" />
                    </div>
                )}
            </div>
        </div>
    )
}

// Mini stat for inline usage
interface MiniStatProps {
    label: string
    value: string | number
    subValue?: string
}

export function MiniStat({ label, value, subValue }: MiniStatProps) {
    return (
        <div className="flex items-center justify-between py-2">
            <span className="text-sm text-white/60">{label}</span>
            <div className="text-right">
                <span className="font-semibold text-white">{value}</span>
                {subValue && (
                    <span className="text-xs text-white/40 ml-1">{subValue}</span>
                )}
            </div>
        </div>
    )
}

// Stat group for grid layouts
interface StatGroupProps {
    stats: Array<{
        label: string
        value: string | number
        change?: number
    }>
}

export function StatGroup({ stats }: StatGroupProps) {
    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stats.map((stat, idx) => (
                <div key={idx} className="glass-card p-4 rounded-xl text-center">
                    <p className="text-2xl font-bold text-white">{stat.value}</p>
                    <p className="text-sm text-white/50">{stat.label}</p>
                    {stat.change !== undefined && (
                        <span className={clsx(
                            'text-xs font-medium',
                            stat.change >= 0 ? 'text-accent-green' : 'text-accent-red'
                        )}>
                            {stat.change >= 0 ? '↑' : '↓'} {Math.abs(stat.change)}%
                        </span>
                    )}
                </div>
            ))}
        </div>
    )
}
