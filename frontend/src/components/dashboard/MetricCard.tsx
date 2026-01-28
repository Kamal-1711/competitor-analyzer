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
    gray: { bg: 'bg-white/10', text: 'text-gray-300' },
    blue: { bg: 'bg-blue-500/10', text: 'text-blue-400' },
    green: { bg: 'bg-green-500/10', text: 'text-green-400' },
    yellow: { bg: 'bg-yellow-500/10', text: 'text-yellow-400' },
    red: { bg: 'bg-red-500/10', text: 'text-red-400' }
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
            "glass-card-hover p-6 relative overflow-hidden group",
            alert && "ring-1 ring-red-500/50 shadow-glow-red"
        )}>
            <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                    <p className="text-gray-400 text-sm font-medium mb-1">{label}</p>
                    <h3 className="text-3xl font-bold text-white tracking-tight">{value}</h3>
                </div>
                <div className={clsx(
                    "p-3 rounded-xl transition-transform duration-300 group-hover:scale-110",
                    styles.bg,
                    styles.text
                )}>
                    {icon}
                </div>
            </div>

            {change !== undefined && (
                <div className="flex items-center gap-2">
                    <div className={clsx(
                        "flex items-center text-xs font-bold px-2.5 py-1 rounded-lg",
                        changeDirection === 'up' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                    )}>
                        {changeDirection === 'up' ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                        {Math.abs(change)}%
                    </div>
                    <span className="text-xs text-gray-500">vs yesterday</span>
                </div>
            )}

            {alert && (
                <div className="absolute top-3 right-3 w-2 h-2 rounded-full bg-red-500 animate-pulse shadow-glow-red" />
            )}
        </div>
    )
}
