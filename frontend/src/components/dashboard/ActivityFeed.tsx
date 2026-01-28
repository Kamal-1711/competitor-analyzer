import { useState, useEffect } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { FileText, DollarSign, Package, AlertCircle, RefreshCw } from 'lucide-react'
import { dashboardApi } from '../../services/api'
import clsx from 'clsx'

interface Activity {
    id: string
    type: string
    title: string
    description: string
    competitor_name: string
    timestamp: string
}

const activityStyles: Record<string, { icon: any, bg: string, text: string }> = {
    content_update: { icon: FileText, bg: 'bg-blue-500/10', text: 'text-blue-400' },
    price_change: { icon: DollarSign, bg: 'bg-green-500/10', text: 'text-green-400' },
    new_product: { icon: Package, bg: 'bg-purple-500/10', text: 'text-purple-400' },
    default: { icon: AlertCircle, bg: 'bg-gray-500/10', text: 'text-gray-400' }
}

export default function ActivityFeed({ limit }: { limit?: number }) {
    const [activities, setActivities] = useState<Activity[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchActivities = async () => {
            try {
                const response = await dashboardApi.getActivity(limit || 10)
                setActivities(response.data)
            } catch (error) {
                console.error('Failed to fetch activities:', error)
                // Show empty state - no mock data
                setActivities([])
            } finally {
                setLoading(false)
            }
        }

        fetchActivities()
    }, [limit])

    if (loading) {
        return (
            <div className="flex items-center justify-center h-48">
                <RefreshCw className="w-6 h-6 text-accent-blue animate-spin" />
            </div>
        )
    }

    return (
        <div className="space-y-2">
            {activities.length > 0 ? (
                activities.map((activity, index) => {
                    const style = activityStyles[activity.type] || activityStyles.default
                    const Icon = style.icon

                    return (
                        <div key={activity.id} className="group relative">
                            {/* Connecting Line (except last item) */}
                            {index !== activities.length - 1 && (
                                <div className="absolute left-[26px] top-12 bottom-[-16px] w-px bg-white/5 z-0" />
                            )}

                            <div className="flex gap-4 p-4 rounded-2xl transition-all duration-300 hover:bg-white/5 border border-transparent hover:border-white/5 cursor-pointer relative z-10">
                                <div className={clsx(
                                    "w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border shadow-lg transition-transform group-hover:scale-105",
                                    style.bg,
                                    style.text,
                                    "border-white/10"
                                )}>
                                    <Icon className="w-5 h-5 drop-shadow-md" />
                                </div>
                                <div className="flex-1 min-w-0 pt-1">
                                    <div className="flex justify-between items-start mb-1">
                                        <h4 className="text-sm font-semibold text-gray-200 truncate group-hover:text-white group-hover:text-glow transition-all">
                                            {activity.title}
                                        </h4>
                                        <span className="text-[10px] font-medium text-gray-500 uppercase tracking-wider bg-white/5 px-2 py-0.5 rounded-full whitespace-nowrap ml-2">
                                            {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-400 leading-relaxed mb-2">{activity.description}</p>
                                    <div className="flex items-center gap-2">
                                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)]" />
                                        <p className="text-xs font-semibold text-gray-400 group-hover:text-indigo-400 transition-colors">
                                            {activity.competitor_name}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )
                })
            ) : (
                <div className="text-center py-8">
                    <p className="text-gray-500 text-sm">No recent activity</p>
                </div>
            )}
        </div>
    )
}
