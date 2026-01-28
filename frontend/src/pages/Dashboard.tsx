import { useState, useEffect } from 'react'
import {
    Users,
    Activity,
    HeartPulse,
    AlertTriangle,
    Sparkles,
    RefreshCw
} from 'lucide-react'
import { dashboardApi, competitorsApi } from '../services/api'
import MetricCard from '../components/dashboard/MetricCard'
import ScanProgress from '../components/dashboard/ScanProgress'
import CompetitorCard from '../components/dashboard/CompetitorCard'
import HealthScore from '../components/dashboard/HealthScore'
import ActivityFeed from '../components/dashboard/ActivityFeed'

interface DashboardMetrics {
    total_competitors: { value: number; label: string }
    changes_24h: { value: number; change?: number; change_direction?: string }
    active_monitors: { value: number }
    critical_alerts: { value: number }
}

interface Competitor {
    id: string
    name: string
    url: string
    domain: string
    favicon_url: string
    competitor_type: 'direct' | 'indirect'
    health_score: number
    seo_score: number
    content_score: number
    is_monitoring: boolean
}

export default function Dashboard() {
    const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
    const [competitors, setCompetitors] = useState<Competitor[]>([])
    const [healthScore, setHealthScore] = useState({ overall_score: 0, strengths: 0, neutrals: 0, weaknesses: 0 })
    const [scanProgress, setScanProgress] = useState({ is_scanning: false, progress: 0, current_url: '' })
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [metricsRes, competitorsRes, healthRes, scanRes] = await Promise.all([
                    dashboardApi.getMetrics(),
                    competitorsApi.list({ limit: 3 }), // Limit to 3 for the overview row
                    dashboardApi.getHealthScore(),
                    dashboardApi.getScanProgress()
                ])

                setMetrics(metricsRes.data)
                setCompetitors(competitorsRes.data)
                setHealthScore(healthRes.data)
                setScanProgress(scanRes.data)
            } catch (error) {
                console.error('Failed to fetch dashboard data:', error)
                // Show zero values - no mock data
                setMetrics({
                    total_competitors: { value: 0, label: 'Total Competitors' },
                    changes_24h: { value: 0, change: 0, change_direction: 'neutral' },
                    active_monitors: { value: 0 },
                    critical_alerts: { value: 0 }
                })
                setHealthScore({ overall_score: 0, strengths: 0, neutrals: 0, weaknesses: 0 })
            } finally {
                setLoading(false)
            }
        }

        fetchData()
        const interval = setInterval(fetchData, 30000)
        return () => clearInterval(interval)
    }, [])

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full min-h-[500px]">
                <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
            </div>
        )
    }

    return (
        <div className="space-y-8">
            {/* Dashboard Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Dashboard</h1>
                    <p className="text-gray-400 mt-1">Monitor your competitive landscape at a glance</p>
                </div>
                <div className="flex items-center gap-4">
                    {scanProgress.is_scanning && (
                        <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl backdrop-blur-md">
                            <RefreshCw className="w-4 h-4 text-accent-blue animate-spin" />
                            <span className="text-sm font-medium text-gray-300">Scanning...</span>
                        </div>
                    )}
                    <button className="flex items-center gap-2 px-6 py-2.5 btn-primary shadow-glow-purple">
                        <Sparkles className="w-4 h-4" />
                        Generate Insights
                    </button>
                </div>
            </div>

            {/* Scan Progress Bar (Conditional) */}
            {scanProgress.is_scanning && (
                <ScanProgress
                    isScanning={scanProgress.is_scanning}
                    progress={scanProgress.progress}
                    currentUrl={scanProgress.current_url}
                />
            )}

            {/* Stats Overview Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <MetricCard
                    label="Total Competitors"
                    value={metrics?.total_competitors.value ?? 0}
                    icon={<Users className="w-5 h-5" />}
                    color="gray"
                />
                <MetricCard
                    label="Changes (24h)"
                    value={metrics?.changes_24h.value ?? 0}
                    icon={<Activity className="w-5 h-5" />}
                    color="blue"
                />
                <MetricCard
                    label="Active Monitors"
                    value={metrics?.active_monitors.value ?? 0}
                    icon={<HeartPulse className="w-5 h-5" />}
                    color="green"
                />
                <MetricCard
                    label="Critical Alerts"
                    value={metrics?.critical_alerts.value ?? 0}
                    icon={<AlertTriangle className="w-5 h-5" />}
                    color="yellow"
                />
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column (Activities + Competitors) */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Recent Activity */}
                    <div className="glass-card p-6">
                        <h3 className="text-lg font-semibold text-white mb-6">Recent Activity</h3>
                        <ActivityFeed limit={3} />
                    </div>

                    {/* Competitors Overview */}
                    <div className="glass-card p-6">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-semibold text-white">Competitors Overview</h3>
                            <a href="/competitors" className="text-sm font-medium text-accent-blue hover:text-blue-400 transition-colors">
                                View All
                            </a>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            {competitors.map((competitor) => (
                                <CompetitorCard key={competitor.id} competitor={competitor} />
                            ))}
                            {competitors.length < 3 && (
                                <div className="border border-dashed border-white/20 rounded-xl flex items-center justify-center p-6 text-gray-400 hover:border-white/40 hover:text-white transition-all cursor-pointer bg-white/5">
                                    <span className="text-sm">Add more competitors</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Column (Health Score) */}
                <div className="lg:col-span-1">
                    <HealthScore
                        score={healthScore.overall_score}
                        strengths={healthScore.strengths}
                        neutrals={healthScore.neutrals}
                        weaknesses={healthScore.weaknesses}
                    />
                </div>
            </div>
        </div>
    )
}
