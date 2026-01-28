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
                activities.map((activity) => {
                    const style = activityStyles[activity.type] || activityStyles.default
                    const Icon = style.icon

                    return (
                        <div key={activity.id} className="flex gap-4 p-4 hover:bg-white/5 rounded-xl transition-colors cursor-pointer group border border-transparent hover:border-white/5">
                            <div className={clsx("w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border border-white/5 shadow-inner", style.bg, style.text)}>
                                <Icon className="w-5 h-5" />
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex justify-between items-start">
                                    <h4 className="text-sm font-semibold text-gray-200 truncate group-hover:text-white transition-colors">
                                        {activity.title}
                                    </h4>
                                    <span className="text-xs text-gray-500 whitespace-nowrap ml-2">
                                        {formatDistanceToNow(new Date(activity.timestamp), { addSuffix: true })}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-400 truncate mt-0.5">{activity.description}</p>
                                <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                                    <span className="w-1 h-1 rounded-full bg-gray-600" />
                                    {activity.competitor_name}
                                </p>
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
