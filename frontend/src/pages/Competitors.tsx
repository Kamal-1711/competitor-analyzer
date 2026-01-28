import { useState, useEffect } from 'react'
import {
    Plus,
    Grid,
    List,
    Search,
    Play,
    Trash2,
    ExternalLink,
    RefreshCw,
    Globe
} from 'lucide-react'
import { competitorsApi } from '../services/api'
import clsx from 'clsx'
import { ThemeToggle } from '../components/ui/ThemeToggle'

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
    last_scanned: string | null
}

export default function Competitors() {
    const [competitors, setCompetitors] = useState<Competitor[]>([])
    const [loading, setLoading] = useState(true)
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
    const [showAddModal, setShowAddModal] = useState(false)
    const [filter, setFilter] = useState<'all' | 'direct' | 'indirect'>('all')
    const [searchQuery, setSearchQuery] = useState('')

    // Form state
    const [formData, setFormData] = useState({
        name: '',
        url: '',
        competitor_type: 'direct' as 'direct' | 'indirect'
    })
    const [submitting, setSubmitting] = useState(false)

    useEffect(() => {
        fetchCompetitors()
    }, [])

    const fetchCompetitors = async () => {
        try {
            const response = await competitorsApi.list({ limit: 50 })
            setCompetitors(response.data)
        } catch (error) {
            console.error('Failed to fetch competitors:', error)
        } finally {
            setLoading(false)
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setSubmitting(true)

        try {
            await competitorsApi.create(formData)
            setShowAddModal(false)
            setFormData({ name: '', url: '', competitor_type: 'direct' })
            fetchCompetitors()
        } catch (error) {
            console.error('Failed to add competitor:', error)
            alert('Failed to add competitor. Please check the URL and try again.')
        } finally {
            setSubmitting(false)
        }
    }

    const handleTriggerScan = async (id: string) => {
        try {
            await competitorsApi.triggerScan(id)
            fetchCompetitors()
        } catch (error) {
            console.error('Failed to trigger scan:', error)
        }
    }

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure you want to delete this competitor?')) return

        try {
            await competitorsApi.delete(id)
            fetchCompetitors()
        } catch (error) {
            console.error('Failed to delete competitor:', error)
        }
    }

    const filteredCompetitors = competitors.filter(c => {
        const matchesFilter = filter === 'all' || c.competitor_type === filter
        const matchesSearch = c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            c.domain.toLowerCase().includes(searchQuery.toLowerCase())
        return matchesFilter && matchesSearch
    })

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <RefreshCw className="w-8 h-8 text-accent-purple animate-spin" />
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white">Competitors</h2>
                    <p className="text-white/50">Monitor and track your competition</p>
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="btn-primary flex items-center gap-2"
                    >
                        <Plus className="w-5 h-5" />
                        Add Competitor
                    </button>
                    <ThemeToggle />
                </div>
            </div>

            {/* Filters */}
            <div className="glass-card p-4 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                    {/* Search */}
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/40" />
                        <input
                            type="text"
                            placeholder="Search competitors..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="input-glass pl-10 w-64"
                        />
                    </div>

                    {/* Type filter */}
                    <div className="flex items-center gap-1 p-1 bg-white/5 rounded-lg">
                        {(['all', 'direct', 'indirect'] as const).map((type) => (
                            <button
                                key={type}
                                onClick={() => setFilter(type)}
                                className={clsx(
                                    "px-3 py-1.5 rounded-md text-sm font-medium transition-all",
                                    filter === type
                                        ? "bg-gradient-mesh text-white"
                                        : "text-white/50 hover:text-white"
                                )}
                            >
                                {type.charAt(0).toUpperCase() + type.slice(1)}
                            </button>
                        ))}
                    </div>
                </div>

                {/* View toggle */}
                <div className="flex items-center gap-1 p-1 bg-white/5 rounded-lg">
                    <button
                        onClick={() => setViewMode('grid')}
                        className={clsx(
                            "p-2 rounded-md transition-all",
                            viewMode === 'grid'
                                ? "bg-white/10 text-white"
                                : "text-white/50 hover:text-white"
                        )}
                    >
                        <Grid className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => setViewMode('list')}
                        className={clsx(
                            "p-2 rounded-md transition-all",
                            viewMode === 'list'
                                ? "bg-white/10 text-white"
                                : "text-white/50 hover:text-white"
                        )}
                    >
                        <List className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Competitors Grid/List */}
            {filteredCompetitors.length > 0 ? (
                viewMode === 'grid' ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {filteredCompetitors.map((competitor) => (
                            <div key={competitor.id} className="glass-card-hover p-6 rounded-2xl">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center">
                                            {competitor.favicon_url ? (
                                                <img src={competitor.favicon_url} alt="" className="w-8 h-8" />
                                            ) : (
                                                <Globe className="w-6 h-6 text-white/50" />
                                            )}
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-white">{competitor.name}</h3>
                                            <p className="text-sm text-white/50">{competitor.domain}</p>
                                        </div>
                                    </div>
                                    <span className={clsx(
                                        "badge",
                                        competitor.competitor_type === 'direct'
                                            ? "badge-danger"
                                            : "badge-info"
                                    )}>
                                        {competitor.competitor_type}
                                    </span>
                                </div>

                                {/* Scores */}
                                <div className="grid grid-cols-3 gap-3 mb-4">
                                    <div className="text-center p-2 rounded-lg bg-white/5">
                                        <div className="text-lg font-bold text-white">{competitor.health_score}</div>
                                        <div className="text-xs text-white/50">Health</div>
                                    </div>
                                    <div className="text-center p-2 rounded-lg bg-white/5">
                                        <div className="text-lg font-bold text-accent-purple">{competitor.seo_score}</div>
                                        <div className="text-xs text-white/50">SEO</div>
                                    </div>
                                    <div className="text-center p-2 rounded-lg bg-white/5">
                                        <div className="text-lg font-bold text-accent-blue">{competitor.content_score}</div>
                                        <div className="text-xs text-white/50">Content</div>
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="flex items-center justify-between pt-4 border-t border-white/10">
                                    <button
                                        onClick={() => handleTriggerScan(competitor.id)}
                                        className="btn-secondary text-sm px-4 py-2 flex items-center gap-2"
                                    >
                                        <Play className="w-4 h-4" />
                                        Scan
                                    </button>

                                    <div className="flex items-center gap-2">
                                        <a
                                            href={competitor.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="p-2 rounded-lg hover:bg-white/10 transition-colors text-white/50 hover:text-white"
                                        >
                                            <ExternalLink className="w-4 h-4" />
                                        </a>
                                        <button
                                            onClick={() => handleDelete(competitor.id)}
                                            className="p-2 rounded-lg hover:bg-accent-red/20 transition-colors text-white/50 hover:text-accent-red"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="glass-card rounded-2xl overflow-hidden">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-white/10">
                                    <th className="text-left p-4 text-sm font-medium text-white/50">Competitor</th>
                                    <th className="text-left p-4 text-sm font-medium text-white/50">Type</th>
                                    <th className="text-center p-4 text-sm font-medium text-white/50">Health</th>
                                    <th className="text-center p-4 text-sm font-medium text-white/50">SEO</th>
                                    <th className="text-center p-4 text-sm font-medium text-white/50">Content</th>
                                    <th className="text-right p-4 text-sm font-medium text-white/50">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredCompetitors.map((competitor) => (
                                    <tr key={competitor.id} className="border-b border-white/5 hover:bg-white/5">
                                        <td className="p-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center">
                                                    {competitor.favicon_url ? (
                                                        <img src={competitor.favicon_url} alt="" className="w-6 h-6" />
                                                    ) : (
                                                        <Globe className="w-5 h-5 text-white/50" />
                                                    )}
                                                </div>
                                                <div>
                                                    <div className="font-medium text-white">{competitor.name}</div>
                                                    <div className="text-sm text-white/50">{competitor.domain}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <span className={clsx(
                                                "badge",
                                                competitor.competitor_type === 'direct' ? "badge-danger" : "badge-info"
                                            )}>
                                                {competitor.competitor_type}
                                            </span>
                                        </td>
                                        <td className="p-4 text-center font-medium text-white">{competitor.health_score}</td>
                                        <td className="p-4 text-center font-medium text-accent-purple">{competitor.seo_score}</td>
                                        <td className="p-4 text-center font-medium text-accent-blue">{competitor.content_score}</td>
                                        <td className="p-4">
                                            <div className="flex items-center justify-end gap-2">
                                                <button
                                                    onClick={() => handleTriggerScan(competitor.id)}
                                                    className="p-2 rounded-lg hover:bg-white/10 transition-colors text-white/50 hover:text-white"
                                                >
                                                    <Play className="w-4 h-4" />
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(competitor.id)}
                                                    className="p-2 rounded-lg hover:bg-accent-red/20 transition-colors text-white/50 hover:text-accent-red"
                                                >
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )
            ) : (
                <div className="glass-card p-12 rounded-2xl text-center">
                    <Globe className="w-16 h-16 text-white/20 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">No competitors found</h3>
                    <p className="text-white/50 mb-6">
                        {searchQuery || filter !== 'all'
                            ? 'Try adjusting your filters'
                            : 'Add your first competitor to start monitoring'}
                    </p>
                    {!searchQuery && filter === 'all' && (
                        <button
                            onClick={() => setShowAddModal(true)}
                            className="btn-primary inline-flex items-center gap-2"
                        >
                            <Plus className="w-5 h-5" />
                            Add Competitor
                        </button>
                    )}
                </div>
            )}

            {/* Add Modal */}
            {showAddModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <div
                        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                        onClick={() => setShowAddModal(false)}
                    />
                    <div className="relative glass-card p-8 rounded-2xl w-full max-w-md">
                        <h3 className="text-xl font-semibold text-white mb-6">Add Competitor</h3>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-white/70 mb-2">
                                    Company Name
                                </label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                                    placeholder="e.g., Acme Inc"
                                    className="input-glass"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-white/70 mb-2">
                                    Website URL
                                </label>
                                <input
                                    type="url"
                                    value={formData.url}
                                    onChange={(e) => setFormData(prev => ({ ...prev, url: e.target.value }))}
                                    placeholder="https://example.com"
                                    className="input-glass"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-white/70 mb-2">
                                    Competitor Type
                                </label>
                                <div className="flex gap-3">
                                    <button
                                        type="button"
                                        onClick={() => setFormData(prev => ({ ...prev, competitor_type: 'direct' }))}
                                        className={clsx(
                                            "flex-1 py-3 rounded-xl border transition-all",
                                            formData.competitor_type === 'direct'
                                                ? "bg-accent-red/20 border-accent-red text-accent-red"
                                                : "bg-white/5 border-white/10 text-white/50 hover:border-white/30"
                                        )}
                                    >
                                        Direct
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setFormData(prev => ({ ...prev, competitor_type: 'indirect' }))}
                                        className={clsx(
                                            "flex-1 py-3 rounded-xl border transition-all",
                                            formData.competitor_type === 'indirect'
                                                ? "bg-accent-blue/20 border-accent-blue text-accent-blue"
                                                : "bg-white/5 border-white/10 text-white/50 hover:border-white/30"
                                        )}
                                    >
                                        Indirect
                                    </button>
                                </div>
                            </div>

                            <div className="flex gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={() => setShowAddModal(false)}
                                    className="btn-secondary flex-1"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={submitting}
                                    className="btn-primary flex-1 flex items-center justify-center gap-2"
                                >
                                    {submitting && <RefreshCw className="w-4 h-4 animate-spin" />}
                                    Add Competitor
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}
