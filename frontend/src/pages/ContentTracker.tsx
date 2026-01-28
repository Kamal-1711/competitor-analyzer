import { useState, useEffect } from 'react'
import {
    FileText,
    RefreshCw,
    Filter,
} from 'lucide-react'
import { competitorsApi, contentApi } from '../services/api'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

interface Competitor {
    id: string
    name: string
}

interface ContentItem {
    id: string
    url: string
    title: string
    content_type: string
    word_count: number
    readability_score: number | null
    has_changed: boolean
    last_checked: string
}

const contentTypeColors: Record<string, string> = {
    blog: 'badge-purple',
    product: 'badge-success',
    landing: 'badge-info',
    pricing: 'badge-warning',
    documentation: 'badge-info',
    other: 'bg-white/10 text-white/70 border-white/20'
}

export default function ContentTracker() {
    const [competitors, setCompetitors] = useState<Competitor[]>([])
    const [selectedCompetitor, setSelectedCompetitor] = useState<string>('')
    const [content, setContent] = useState<ContentItem[]>([])
    const [loading, setLoading] = useState(false)
    const [filter, setFilter] = useState<'all' | 'changed'>('all')
    const [typeFilter, setTypeFilter] = useState<string>('all')

    useEffect(() => {
        const fetchCompetitors = async () => {
            try {
                const response = await competitorsApi.list()
                setCompetitors(response.data)
                if (response.data.length > 0) {
                    setSelectedCompetitor(response.data[0].id)
                }
            } catch (error) {
                console.error('Failed to fetch competitors:', error)
            }
        }

        fetchCompetitors()
    }, [])

    useEffect(() => {
        if (selectedCompetitor) {
            fetchContent()
        }
    }, [selectedCompetitor])

    const fetchContent = async () => {
        setLoading(true)
        try {
            const response = await contentApi.get(selectedCompetitor)
            setContent(response.data)
        } catch (error) {
            console.error('Failed to fetch content:', error)
            // Show empty state - no mock data
            setContent([])
        } finally {
            setLoading(false)
        }
    }

    const filteredContent = content.filter(item => {
        const matchesChange = filter === 'all' || (filter === 'changed' && item.has_changed)
        const matchesType = typeFilter === 'all' || item.content_type === typeFilter
        return matchesChange && matchesType
    })

    const contentTypes = [...new Set(content.map(c => c.content_type))]
    const changedCount = content.filter(c => c.has_changed).length

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white">Content Tracker</h2>
                    <p className="text-white/50">Monitor content changes and updates</p>
                </div>

                <select
                    value={selectedCompetitor}
                    onChange={(e) => setSelectedCompetitor(e.target.value)}
                    className="input-glass w-auto"
                >
                    {competitors.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                </select>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="glass-card p-4 rounded-xl">
                    <div className="text-2xl font-bold text-white">{content.length}</div>
                    <div className="text-sm text-white/50">Total Pages</div>
                </div>
                <div className="glass-card p-4 rounded-xl">
                    <div className="text-2xl font-bold text-accent-orange">{changedCount}</div>
                    <div className="text-sm text-white/50">Changed</div>
                </div>
                <div className="glass-card p-4 rounded-xl">
                    <div className="text-2xl font-bold text-accent-purple">
                        {content.reduce((sum, c) => sum + c.word_count, 0).toLocaleString()}
                    </div>
                    <div className="text-sm text-white/50">Total Words</div>
                </div>
                <div className="glass-card p-4 rounded-xl">
                    <div className="text-2xl font-bold text-accent-blue">
                        {Math.round(content.reduce((sum, c) => sum + (c.readability_score || 0), 0) / content.length) || 0}
                    </div>
                    <div className="text-sm text-white/50">Avg Readability</div>
                </div>
            </div>

            {/* Filters */}
            <div className="glass-card p-4 rounded-xl flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                    <Filter className="w-4 h-4 text-white/50" />
                    <span className="text-sm text-white/70">Filter:</span>
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={() => setFilter('all')}
                        className={clsx(
                            "px-3 py-1.5 rounded-lg text-sm transition-all",
                            filter === 'all'
                                ? "bg-gradient-mesh text-white"
                                : "bg-white/5 text-white/50 hover:text-white"
                        )}
                    >
                        All ({content.length})
                    </button>
                    <button
                        onClick={() => setFilter('changed')}
                        className={clsx(
                            "px-3 py-1.5 rounded-lg text-sm transition-all",
                            filter === 'changed'
                                ? "bg-gradient-mesh text-white"
                                : "bg-white/5 text-white/50 hover:text-white"
                        )}
                    >
                        Changed ({changedCount})
                    </button>
                </div>

                <div className="h-6 w-px bg-white/10" />

                <select
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                    className="input-glass py-1.5 px-3 text-sm w-auto"
                >
                    <option value="all">All Types</option>
                    {contentTypes.map(type => (
                        <option key={type} value={type}>{type}</option>
                    ))}
                </select>
            </div>

            {/* Content Table */}
            {loading ? (
                <div className="flex items-center justify-center h-64">
                    <RefreshCw className="w-8 h-8 text-accent-purple animate-spin" />
                </div>
            ) : filteredContent.length > 0 ? (
                <div className="glass-card rounded-2xl overflow-hidden">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-white/10">
                                <th className="text-left p-4 text-sm font-medium text-white/50">Page</th>
                                <th className="text-left p-4 text-sm font-medium text-white/50">Type</th>
                                <th className="text-center p-4 text-sm font-medium text-white/50">Words</th>
                                <th className="text-center p-4 text-sm font-medium text-white/50">Readability</th>
                                <th className="text-center p-4 text-sm font-medium text-white/50">Status</th>
                                <th className="text-right p-4 text-sm font-medium text-white/50">Last Checked</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredContent.map((item) => (
                                <tr key={item.id} className="border-b border-white/5 hover:bg-white/5 cursor-pointer">
                                    <td className="p-4">
                                        <div className="flex items-center gap-3">
                                            <FileText className="w-5 h-5 text-white/30" />
                                            <div>
                                                <div className="font-medium text-white">{item.title}</div>
                                                <div className="text-sm text-white/50 truncate max-w-xs">{item.url}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <span className={clsx("badge", contentTypeColors[item.content_type] || contentTypeColors.other)}>
                                            {item.content_type}
                                        </span>
                                    </td>
                                    <td className="p-4 text-center text-white">{item.word_count.toLocaleString()}</td>
                                    <td className="p-4 text-center">
                                        <span className={clsx(
                                            "font-medium",
                                            item.readability_score && item.readability_score >= 70
                                                ? "text-accent-green"
                                                : item.readability_score && item.readability_score >= 50
                                                    ? "text-accent-orange"
                                                    : "text-accent-red"
                                        )}>
                                            {item.readability_score || '-'}
                                        </span>
                                    </td>
                                    <td className="p-4 text-center">
                                        {item.has_changed ? (
                                            <span className="badge badge-warning">Changed</span>
                                        ) : (
                                            <span className="badge bg-white/5 text-white/50 border-white/10">No change</span>
                                        )}
                                    </td>
                                    <td className="p-4 text-right text-sm text-white/50">
                                        {formatDistanceToNow(new Date(item.last_checked), { addSuffix: true })}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="glass-card p-12 rounded-2xl text-center">
                    <FileText className="w-16 h-16 text-white/20 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">No content found</h3>
                    <p className="text-white/50">
                        Run a scan to discover competitor content
                    </p>
                </div>
            )}
        </div>
    )
}
