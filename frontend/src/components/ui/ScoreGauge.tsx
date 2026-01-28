import { useMemo } from 'react'
import clsx from 'clsx'

interface ScoreGaugeProps {
    score: number
    size?: 'sm' | 'md' | 'lg'
    label?: string
    showLabel?: boolean
}

export function ScoreGauge({ score, size = 'md', label, showLabel = true }: ScoreGaugeProps) {
    const dimensions = useMemo(() => {
        switch (size) {
            case 'sm': return { width: 80, stroke: 6, fontSize: 'text-lg' }
            case 'lg': return { width: 160, stroke: 10, fontSize: 'text-4xl' }
            default: return { width: 120, stroke: 8, fontSize: 'text-2xl' }
        }
    }, [size])

    const radius = (dimensions.width - dimensions.stroke) / 2
    const circumference = 2 * Math.PI * radius
    const progress = ((100 - score) / 100) * circumference

    const color = useMemo(() => {
        if (score >= 80) return { stroke: '#10b981', text: 'text-accent-green', bg: 'bg-accent-green/20' }
        if (score >= 60) return { stroke: '#f59e0b', text: 'text-accent-orange', bg: 'bg-accent-orange/20' }
        if (score >= 40) return { stroke: '#eab308', text: 'text-yellow-500', bg: 'bg-yellow-500/20' }
        return { stroke: '#ef4444', text: 'text-accent-red', bg: 'bg-accent-red/20' }
    }, [score])

    return (
        <div className="flex flex-col items-center">
            <div className="relative" style={{ width: dimensions.width, height: dimensions.width }}>
                <svg className="transform -rotate-90" width={dimensions.width} height={dimensions.width}>
                    {/* Background circle */}
                    <circle
                        cx={dimensions.width / 2}
                        cy={dimensions.width / 2}
                        r={radius}
                        fill="transparent"
                        stroke="rgba(255,255,255,0.1)"
                        strokeWidth={dimensions.stroke}
                    />
                    {/* Progress circle */}
                    <circle
                        cx={dimensions.width / 2}
                        cy={dimensions.width / 2}
                        r={radius}
                        fill="transparent"
                        stroke={color.stroke}
                        strokeWidth={dimensions.stroke}
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={progress}
                        className="transition-all duration-1000 ease-out"
                    />
                </svg>
                {/* Score text */}
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className={clsx('font-bold', dimensions.fontSize, color.text)}>
                        {score}
                    </span>
                </div>
            </div>
            {showLabel && label && (
                <span className="mt-2 text-sm text-white/60">{label}</span>
            )}
        </div>
    )
}

// Horizontal score bar
interface ScoreBarProps {
    score: number
    label: string
    showValue?: boolean
}

export function ScoreBar({ score, label, showValue = true }: ScoreBarProps) {
    const color = useMemo(() => {
        if (score >= 80) return 'bg-accent-green'
        if (score >= 60) return 'bg-accent-orange'
        if (score >= 40) return 'bg-yellow-500'
        return 'bg-accent-red'
    }, [score])

    return (
        <div className="space-y-1.5">
            <div className="flex justify-between items-center">
                <span className="text-sm text-white/70">{label}</span>
                {showValue && (
                    <span className="text-sm font-medium text-white">{score}/100</span>
                )}
            </div>
            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                <div
                    className={clsx('h-full rounded-full transition-all duration-500', color)}
                    style={{ width: `${score}%` }}
                />
            </div>
        </div>
    )
}

// Comparison score indicator
interface CompareScoreProps {
    yourScore: number
    avgScore: number
    label: string
}

export function CompareScore({ yourScore, avgScore, label }: CompareScoreProps) {
    const diff = yourScore - avgScore
    const isPositive = diff >= 0

    return (
        <div className="glass-card p-4 rounded-xl">
            <div className="flex justify-between items-start mb-2">
                <span className="text-sm text-white/50">{label}</span>
                <span className={clsx(
                    'text-xs px-2 py-0.5 rounded-full',
                    isPositive ? 'bg-accent-green/20 text-accent-green' : 'bg-accent-red/20 text-accent-red'
                )}>
                    {isPositive ? '+' : ''}{diff}
                </span>
            </div>
            <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-white">{yourScore}</span>
                <span className="text-sm text-white/40">vs avg {avgScore}</span>
            </div>
        </div>
    )
}
