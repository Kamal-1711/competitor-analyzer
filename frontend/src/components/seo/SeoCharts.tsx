import { useMemo } from 'react'
import {
    RadarChart as RechartsRadar,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
    Legend,
    ResponsiveContainer,
    Tooltip
} from 'recharts'

interface RadarDataset {
    label: string
    data: number[]
    is_you?: boolean
}

interface SeoRadarChartProps {
    labels: string[]
    datasets: RadarDataset[]
}

const COLORS = [
    '#8b5cf6', // Purple (you)
    '#3b82f6', // Blue
    '#06b6d4', // Cyan
    '#10b981', // Green
    '#f59e0b', // Orange
]

export function SeoRadarChart({ labels, datasets }: SeoRadarChartProps) {
    const chartData = useMemo(() => {
        return labels.map((label, i) => {
            const point: Record<string, string | number> = { category: label }
            datasets.forEach((dataset) => {
                point[dataset.label] = dataset.data[i] || 0
            })
            return point
        })
    }, [labels, datasets])

    return (
        <ResponsiveContainer width="100%" height={350}>
            <RechartsRadar data={chartData} margin={{ top: 20, right: 30, bottom: 20, left: 30 }}>
                <PolarGrid stroke="rgba(255,255,255,0.1)" />
                <PolarAngleAxis
                    dataKey="category"
                    tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
                />
                <PolarRadiusAxis
                    angle={30}
                    domain={[0, 100]}
                    tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }}
                />
                {datasets.map((dataset, i) => (
                    <Radar
                        key={dataset.label}
                        name={dataset.label}
                        dataKey={dataset.label}
                        stroke={dataset.is_you ? COLORS[0] : COLORS[(i + 1) % COLORS.length]}
                        fill={dataset.is_you ? COLORS[0] : COLORS[(i + 1) % COLORS.length]}
                        fillOpacity={dataset.is_you ? 0.3 : 0.1}
                        strokeWidth={dataset.is_you ? 2 : 1}
                    />
                ))}
                <Tooltip
                    contentStyle={{
                        backgroundColor: 'rgba(20, 20, 30, 0.95)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '8px',
                        color: '#fff'
                    }}
                />
                <Legend
                    wrapperStyle={{ color: 'rgba(255,255,255,0.6)' }}
                />
            </RechartsRadar>
        </ResponsiveContainer>
    )
}

// Comparison bar chart
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Cell,
    LabelList
} from 'recharts'

interface ComparisonBarData {
    name: string
    score: number
    is_you?: boolean
}

interface SeoComparisonBarProps {
    data: ComparisonBarData[]
    metric: string
}

export function SeoComparisonBar({ data, metric }: SeoComparisonBarProps) {
    return (
        <div className="glass-card p-4 rounded-xl">
            <h4 className="text-sm font-medium text-white/70 mb-3">{metric}</h4>
            <ResponsiveContainer width="100%" height={200}>
                <BarChart data={data} layout="vertical" margin={{ left: 80, right: 40 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" horizontal={false} />
                    <XAxis type="number" domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} />
                    <YAxis
                        type="category"
                        dataKey="name"
                        tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 12 }}
                        width={75}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: 'rgba(20, 20, 30, 0.95)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: '8px'
                        }}
                    />
                    <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                        {data.map((entry, index) => (
                            <Cell
                                key={`cell-${index}`}
                                fill={entry.is_you ? '#8b5cf6' : '#4b5563'}
                            />
                        ))}
                        <LabelList
                            dataKey="score"
                            position="right"
                            fill="rgba(255,255,255,0.7)"
                            fontSize={11}
                        />
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    )
}
