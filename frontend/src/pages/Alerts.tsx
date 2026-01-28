import { useState, useEffect } from 'react'
import { Bell, RefreshCw, Check, Trash2, AlertTriangle, FileText, DollarSign, Package } from 'lucide-react'
import { alertsApi } from '../services/api'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

interface AlertItem { id: string; alert_type: string; severity: string; title: string; message: string; is_read: boolean; created_at: string }
interface AlertStats { total: number; unread: number; critical: number; high: number; medium: number; low: number }

const alertIcons: Record<string, typeof Bell> = { price_change: DollarSign, content_update: FileText, new_product: Package, default: AlertTriangle }
const severityColors: Record<string, string> = { critical: 'bg-accent-red/20 border-accent-red/30 text-accent-red', high: 'bg-accent-orange/20 border-accent-orange/30 text-accent-orange', medium: 'bg-accent-blue/20 border-accent-blue/30 text-accent-blue', low: 'bg-white/10 border-white/20 text-white/50' }

export default function Alerts() {
    const [alerts, setAlerts] = useState<AlertItem[]>([])
    const [stats, setStats] = useState<AlertStats | null>(null)
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState<'all' | 'unread'>('all')

    const fetchData = () => {
        setLoading(true)
        Promise.all([alertsApi.list(), alertsApi.getStats()])
            .then(([alertsRes, statsRes]) => { setAlerts(alertsRes.data); setStats(statsRes.data) })
            .catch(() => {
                setAlerts([
                    { id: '1', alert_type: 'price_change', severity: 'high', title: 'Price Drop Detected', message: 'Pro Plan decreased by 15%', is_read: false, created_at: new Date().toISOString() },
                    { id: '2', alert_type: 'content_update', severity: 'medium', title: 'New Blog Post', message: 'CompA published AI article', is_read: false, created_at: new Date(Date.now() - 3600000).toISOString() },
                    { id: '3', alert_type: 'new_product', severity: 'critical', title: 'New Product Launch', message: 'CompB launched Enterprise Suite', is_read: true, created_at: new Date(Date.now() - 86400000).toISOString() },
                ])
                setStats({ total: 3, unread: 2, critical: 1, high: 1, medium: 1, low: 0 })
            }).finally(() => setLoading(false))
    }

    useEffect(() => { fetchData() }, [])

    const handleMarkRead = async (id: string) => {
        try { await alertsApi.markAsRead(id); fetchData() } catch (e) { console.error(e) }
    }

    const handleDismiss = async (id: string) => {
        try { await alertsApi.dismiss(id); fetchData() } catch (e) { console.error(e) }
    }

    const handleMarkAllRead = async () => {
        try { await alertsApi.markAllAsRead(); fetchData() } catch (e) { console.error(e) }
    }

    const filtered = filter === 'unread' ? alerts.filter(a => !a.is_read) : alerts

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div><h2 className="text-2xl font-bold text-white">Alerts</h2><p className="text-white/50">Stay updated on competitor changes</p></div>
                <button onClick={handleMarkAllRead} className="btn-secondary text-sm">Mark All Read</button>
            </div>

            <div className="grid grid-cols-5 gap-4">
                <div className="glass-card p-4 rounded-xl"><div className="text-2xl font-bold text-white">{stats?.total || 0}</div><div className="text-sm text-white/50">Total</div></div>
                <div className="glass-card p-4 rounded-xl"><div className="text-2xl font-bold text-accent-purple">{stats?.unread || 0}</div><div className="text-sm text-white/50">Unread</div></div>
                <div className="glass-card p-4 rounded-xl"><div className="text-2xl font-bold text-accent-red">{stats?.critical || 0}</div><div className="text-sm text-white/50">Critical</div></div>
                <div className="glass-card p-4 rounded-xl"><div className="text-2xl font-bold text-accent-orange">{stats?.high || 0}</div><div className="text-sm text-white/50">High</div></div>
                <div className="glass-card p-4 rounded-xl"><div className="text-2xl font-bold text-accent-blue">{stats?.medium || 0}</div><div className="text-sm text-white/50">Medium</div></div>
            </div>

            <div className="flex gap-2">
                {(['all', 'unread'] as const).map(f => (
                    <button key={f} onClick={() => setFilter(f)} className={clsx("px-4 py-2 rounded-lg text-sm", filter === f ? "bg-gradient-mesh text-white" : "bg-white/5 text-white/50")}>{f === 'all' ? 'All' : 'Unread'}</button>
                ))}
            </div>

            {loading ? <div className="flex justify-center h-64"><RefreshCw className="w-8 h-8 text-accent-purple animate-spin" /></div> : (
                <div className="space-y-3">
                    {filtered.length > 0 ? filtered.map(a => {
                        const Icon = alertIcons[a.alert_type] || alertIcons.default
                        return (
                            <div key={a.id} className={clsx("glass-card p-4 rounded-xl flex items-start gap-4", !a.is_read && "border-l-4 border-l-accent-purple")}>
                                <div className={clsx("w-10 h-10 rounded-lg flex items-center justify-center border", severityColors[a.severity] || severityColors.low)}><Icon className="w-5 h-5" /></div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2"><h4 className="font-medium text-white">{a.title}</h4><span className={clsx("badge", severityColors[a.severity])}>{a.severity}</span></div>
                                    <p className="text-sm text-white/50">{a.message}</p>
                                    <span className="text-xs text-white/30">{formatDistanceToNow(new Date(a.created_at), { addSuffix: true })}</span>
                                </div>
                                <div className="flex gap-2">
                                    {!a.is_read && <button onClick={() => handleMarkRead(a.id)} className="p-2 rounded-lg hover:bg-white/10 text-white/50 hover:text-accent-green"><Check className="w-4 h-4" /></button>}
                                    <button onClick={() => handleDismiss(a.id)} className="p-2 rounded-lg hover:bg-accent-red/20 text-white/50 hover:text-accent-red"><Trash2 className="w-4 h-4" /></button>
                                </div>
                            </div>
                        )
                    }) : <div className="glass-card p-12 rounded-2xl text-center"><Bell className="w-16 h-16 text-white/20 mx-auto mb-4" /><h3 className="text-xl font-semibold text-white">No alerts</h3></div>}
                </div>
            )}
        </div>
    )
}
