import { ReactNode } from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'
import clsx from 'clsx'

interface MetricCardProps {
    label: string
    value: number | string
    change?: number
    changeDirection?: 'up' | 'down'
    icon: ReactNode
    color?: 'gray' | 'blue' | 'green' | 'yellow' | 'red'
    alert?: boolean
}

const colorStyles = {
    gray: { bg: 'bg-white/5', text: 'text-gray-400', ring: 'ring-gray-500/20' },
    blue: { bg: 'bg-blue-500/10', text: 'text-blue-400', ring: 'ring-blue-500/20' },
    green: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', ring: 'ring-emerald-500/20' },
    yellow: { bg: 'bg-amber-500/10', text: 'text-amber-400', ring: 'ring-amber-500/20' },
    red: { bg: 'bg-rose-500/10', text: 'text-rose-400', ring: 'ring-rose-500/20' }
}

export default function MetricCard({
    label,
    value,
    change,
    changeDirection,
    icon,
    color = 'gray',
    alert
}: MetricCardProps) {
    const styles = colorStyles[color]

    return (
        <div className={clsx(
            "glass-card-hover p-6 group relative",
            alert && "ring-1 ring-rose-500/50 shadow-[0_0_20px_rgba(244,63,94,0.15)]"
        )}>
            <div className="glass-shine opacity-0 group-hover:opacity-100 transition-opacity duration-700" />

            <div className="flex justify-between items-start mb-4 relative z-10">
                <div className="flex-1">
                    <p className="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1.5">{label}</p>
                    <h3 className="text-3xl font-bold text-white tracking-tight">{value}</h3>
                </div>
                <div className={clsx(
                    "p-3.5 rounded-2xl transition-all duration-300 group-hover:scale-110",
                    styles.bg,
                    styles.text,
                    "ring-1 inset", styles.ring
                )}>
                    {icon}
                </div>
            </div>

            {change !== undefined && (
                <div className="flex items-center gap-2 relative z-10">
                    <div className={clsx(
                        "flex items-center text-xs font-bold px-2.5 py-1 rounded-full border",
                        changeDirection === 'up'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                    )}>
                        {changeDirection === 'up' ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                        {Math.abs(change)}%
                    </div>
                    <span className="text-xs text-gray-500 font-medium">vs yesterday</span>
                </div>
            )}

            {alert && (
                <span className="absolute top-3 right-3 flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
                </span>
            )}
        </div>
    )
}
