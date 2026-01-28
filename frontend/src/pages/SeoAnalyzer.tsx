import { useState, useEffect } from 'react'
import {
    Search,
    CheckCircle,
    XCircle,
    RefreshCw,
    FileText,
    Link2,
    Image,
    Code,
    TrendingUp,
    TrendingDown,
    AlertTriangle,
    Shield,
    Zap,
    Globe,
    BarChart3,
    Sparkles,
} from 'lucide-react'
import { competitorsApi, seoApi } from '../services/api'
import clsx from 'clsx'

interface Competitor {
    id: string
    name: string
    domain: string
    url: string
}

interface SeoAnalysis {
    overall_score: number
    title: string
    title_score: number
    meta_description: string
    meta_description_score: number
    h1_count: number
    h2_count: number
    h3_count: number
    headers_score: number
    word_count: number
    content_score: number
    total_images: number
    images_with_alt: number
    images_score: number
    internal_links: number
    external_links: number
    links_score: number
    has_ssl: boolean
    has_sitemap: boolean
    has_robots_txt: boolean
    has_canonical: boolean
    has_schema_markup: boolean
    technical_score: number
    analyzed_at?: string
}

export default function SeoAnalyzer() {
    const [competitors, setCompetitors] = useState<Competitor[]>([])
    const [selectedCompetitor, setSelectedCompetitor] = useState<string>('')
    const [analysis, setAnalysis] = useState<SeoAnalysis | null>(null)
    const [loading, setLoading] = useState(false)
    const [analyzing, setAnalyzing] = useState(false)

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
            fetchSeoData()
        }
    }, [selectedCompetitor])

    const fetchSeoData = async () => {
        setLoading(true)
        try {
            const analysisRes = await seoApi.get(selectedCompetitor)
            setAnalysis(analysisRes.data)
        } catch (error) {
            console.error('Failed to fetch SEO data:', error)
            setAnalysis(null)
        } finally {
            setLoading(false)
        }
    }

    const handleAnalyze = async () => {
        setAnalyzing(true)
        try {
            await seoApi.analyze(selectedCompetitor)
            await fetchSeoData()
        } catch (error) {
            console.error('Failed to analyze:', error)
        } finally {
            setAnalyzing(false)
        }
    }

    const getScoreColor = (score: number) => {
        if (score >= 80) return 'text-emerald-400'
        if (score >= 60) return 'text-amber-400'
        return 'text-rose-400'
    }

    const getScoreBg = (score: number) => {
        if (score >= 80) return 'from-emerald-500/20 to-emerald-500/5 border-emerald-500/30'
        if (score >= 60) return 'from-amber-500/20 to-amber-500/5 border-amber-500/30'
        return 'from-rose-500/20 to-rose-500/5 border-rose-500/30'
    }

    const getScoreRing = (score: number) => {
        if (score >= 80) return 'ring-emerald-500/50'
        if (score >= 60) return 'ring-amber-500/50'
        return 'ring-rose-500/50'
    }

    const getScoreLabel = (score: number) => {
        if (score >= 90) return 'Excellent'
        if (score >= 80) return 'Great'
        if (score >= 70) return 'Good'
        if (score >= 60) return 'Fair'
        if (score >= 50) return 'Needs Work'
        return 'Poor'
    }

    // Generate insights based on analysis
    const generateInsights = (analysis: SeoAnalysis) => {
        const insights: { type: 'success' | 'warning' | 'error'; message: string; priority: number }[] = []

        // Title insights
        if (analysis.title_score >= 80) {
            insights.push({ type: 'success', message: 'Title tag is well optimized', priority: 3 })
        } else if (analysis.title_score < 60) {
            insights.push({ type: 'error', message: 'Title tag needs improvement - ensure it\'s 50-60 characters', priority: 1 })
        }

        // Meta description
        if (analysis.meta_description_score < 60) {
            insights.push({ type: 'error', message: 'Meta description is missing or too short', priority: 1 })
        }

        // Technical
        if (!analysis.has_ssl) {
            insights.push({ type: 'error', message: 'SSL certificate not detected - critical for security', priority: 1 })
        }
        if (!analysis.has_sitemap) {
            insights.push({ type: 'warning', message: 'Sitemap.xml not found - important for crawling', priority: 2 })
        }
        if (!analysis.has_schema_markup) {
            insights.push({ type: 'warning', message: 'No schema markup detected - add structured data', priority: 2 })
        }
        if (analysis.has_ssl && analysis.has_sitemap && analysis.has_robots_txt) {
            insights.push({ type: 'success', message: 'Technical SEO fundamentals are solid', priority: 3 })
        }

        // Content
        if (analysis.word_count < 300) {
            insights.push({ type: 'warning', message: 'Content is thin - aim for 1000+ words', priority: 2 })
        } else if (analysis.word_count >= 1500) {
            insights.push({ type: 'success', message: 'Content length is excellent for SEO', priority: 3 })
        }

        // Headers
        if (analysis.h1_count === 0) {
            insights.push({ type: 'error', message: 'Missing H1 heading - every page needs one', priority: 1 })
        } else if (analysis.h1_count > 1) {
            insights.push({ type: 'warning', message: `Multiple H1 tags (${analysis.h1_count}) - use only one`, priority: 2 })
        }

        // Images
        if (analysis.total_images > 0 && analysis.images_with_alt < analysis.total_images) {
            const missing = analysis.total_images - analysis.images_with_alt
            insights.push({ type: 'warning', message: `${missing} images missing alt text`, priority: 2 })
        }

        // Sort by priority
        return insights.sort((a, b) => a.priority - b.priority)
    }

    const selectedComp = competitors.find(c => c.id === selectedCompetitor)

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-gradient-to-br from-violet-500/20 to-indigo-500/20 border border-violet-500/20">
                            <BarChart3 className="w-6 h-6 text-violet-400" />
                        </div>
                        SEO Analyzer
                    </h2>
                    <p className="text-white/50 mt-1">Deep analysis and optimization insights</p>
                </div>

                <div className="flex items-center gap-3">
                    <select
                        value={selectedCompetitor}
                        onChange={(e) => setSelectedCompetitor(e.target.value)}
                        className="input-glass min-w-[200px]"
                    >
                        {competitors.map((c) => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                    </select>

                    <button
                        onClick={handleAnalyze}
                        disabled={analyzing}
                        className="btn-primary"
                    >
                        {analyzing ? (
                            <RefreshCw className="w-5 h-5 animate-spin" />
                        ) : (
                            <Sparkles className="w-5 h-5" />
                        )}
                        {analyzing ? 'Analyzing...' : 'Analyze Now'}
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="flex items-center justify-center h-96">
                    <div className="text-center">
                        <RefreshCw className="w-12 h-12 text-violet-500 animate-spin mx-auto mb-4" />
                        <p className="text-white/50">Loading SEO data...</p>
                    </div>
                </div>
            ) : analysis ? (
                <>
                    {/* Hero Score Card */}
                    <div className="glass-card p-8 rounded-2xl relative overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-br from-violet-500/10 via-transparent to-indigo-500/10" />
                        <div className="relative flex flex-col lg:flex-row items-center justify-between gap-8">
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-4">
                                    <Globe className="w-5 h-5 text-violet-400" />
                                    <span className="text-white/70">{selectedComp?.url || selectedComp?.domain}</span>
                                </div>
                                <h3 className="text-2xl font-bold text-white mb-2">Overall SEO Health</h3>
                                <p className="text-white/50 mb-6">Comprehensive analysis across on-page, technical, and content factors</p>

                                {/* Quick Stats */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                                        <div className="text-xs text-white/50 uppercase tracking-wider mb-1">Content</div>
                                        <div className={clsx("text-xl font-bold", getScoreColor(analysis.content_score))}>{analysis.content_score}</div>
                                    </div>
                                    <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                                        <div className="text-xs text-white/50 uppercase tracking-wider mb-1">Technical</div>
                                        <div className={clsx("text-xl font-bold", getScoreColor(analysis.technical_score))}>{analysis.technical_score}</div>
                                    </div>
                                    <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                                        <div className="text-xs text-white/50 uppercase tracking-wider mb-1">On-Page</div>
                                        <div className={clsx("text-xl font-bold", getScoreColor(analysis.title_score))}>{analysis.title_score}</div>
                                    </div>
                                    <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                                        <div className="text-xs text-white/50 uppercase tracking-wider mb-1">Images</div>
                                        <div className={clsx("text-xl font-bold", getScoreColor(analysis.images_score))}>{analysis.images_score}</div>
                                    </div>
                                </div>
                            </div>

                            {/* Score Circle */}
                            <div className="relative">
                                <div className={clsx(
                                    "w-40 h-40 rounded-full flex flex-col items-center justify-center",
                                    "bg-gradient-to-br border-2 ring-4 ring-offset-4 ring-offset-dark-900",
                                    getScoreBg(analysis.overall_score),
                                    getScoreRing(analysis.overall_score)
                                )}>
                                    <div className={clsx("text-5xl font-bold", getScoreColor(analysis.overall_score))}>
                                        {analysis.overall_score}
                                    </div>
                                    <div className="text-white/50 text-sm">/ 100</div>
                                </div>
                                <div className={clsx(
                                    "absolute -bottom-2 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs font-bold",
                                    analysis.overall_score >= 80 ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" :
                                        analysis.overall_score >= 60 ? "bg-amber-500/20 text-amber-400 border border-amber-500/30" :
                                            "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                                )}>
                                    {getScoreLabel(analysis.overall_score)}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Insights Panel */}
                    <div className="glass-card p-6 rounded-2xl">
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <Zap className="w-5 h-5 text-amber-400" />
                            AI Insights & Recommendations
                        </h3>
                        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
                            {generateInsights(analysis).map((insight, i) => (
                                <div key={i} className={clsx(
                                    "p-4 rounded-xl border flex items-start gap-3",
                                    insight.type === 'success' && "bg-emerald-500/10 border-emerald-500/20",
                                    insight.type === 'warning' && "bg-amber-500/10 border-amber-500/20",
                                    insight.type === 'error' && "bg-rose-500/10 border-rose-500/20"
                                )}>
                                    {insight.type === 'success' && <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />}
                                    {insight.type === 'warning' && <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />}
                                    {insight.type === 'error' && <XCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />}
                                    <span className="text-sm text-white/80">{insight.message}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Score Cards Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                        {[
                            { label: 'Title', score: analysis.title_score, icon: FileText, detail: `${analysis.title?.length || 0} chars` },
                            { label: 'Meta', score: analysis.meta_description_score, icon: FileText, detail: `${analysis.meta_description?.length || 0} chars` },
                            { label: 'Headers', score: analysis.headers_score, icon: Code, detail: `${analysis.h1_count} H1, ${analysis.h2_count} H2` },
                            { label: 'Content', score: analysis.content_score, icon: FileText, detail: `${analysis.word_count.toLocaleString()} words` },
                            { label: 'Images', score: analysis.images_score, icon: Image, detail: `${analysis.images_with_alt}/${analysis.total_images} alt` },
                            { label: 'Links', score: analysis.links_score, icon: Link2, detail: `${analysis.internal_links} int, ${analysis.external_links} ext` },
                        ].map((item) => (
                            <div
                                key={item.label}
                                className={clsx(
                                    "glass-card-hover p-4 rounded-xl border bg-gradient-to-br",
                                    getScoreBg(item.score)
                                )}
                            >
                                <div className="flex items-center justify-between mb-3">
                                    <item.icon className={clsx("w-5 h-5", getScoreColor(item.score))} />
                                    <span className="text-xs text-white/40">{item.detail}</span>
                                </div>
                                <div className={clsx("text-3xl font-bold mb-1", getScoreColor(item.score))}>
                                    {item.score}
                                </div>
                                <div className="text-sm text-white/50">{item.label}</div>
                            </div>
                        ))}
                    </div>

                    {/* Details Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* On-Page SEO */}
                        <div className="glass-card p-6 rounded-2xl">
                            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                <FileText className="w-5 h-5 text-blue-400" />
                                On-Page SEO
                            </h3>

                            <div className="space-y-4">
                                <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                                    <div className="flex justify-between text-sm mb-2">
                                        <span className="text-white/70">Title Tag</span>
                                        <span className={getScoreColor(analysis.title_score)}>{analysis.title_score}/100</span>
                                    </div>
                                    <p className="text-sm text-white/80 bg-black/20 p-2 rounded-lg font-mono truncate">{analysis.title || 'No title'}</p>
                                </div>

                                <div className="p-4 bg-white/5 rounded-xl border border-white/5">
                                    <div className="flex justify-between text-sm mb-2">
                                        <span className="text-white/70">Meta Description</span>
                                        <span className={getScoreColor(analysis.meta_description_score)}>{analysis.meta_description_score}/100</span>
                                    </div>
                                    <p className="text-sm text-white/80 bg-black/20 p-2 rounded-lg line-clamp-2">{analysis.meta_description || 'No meta description'}</p>
                                </div>

                                <div className="grid grid-cols-3 gap-3">
                                    <div className="text-center p-3 bg-white/5 rounded-xl border border-white/5">
                                        <div className="text-2xl font-bold text-white">{analysis.h1_count}</div>
                                        <div className="text-xs text-white/50">H1 Tags</div>
                                    </div>
                                    <div className="text-center p-3 bg-white/5 rounded-xl border border-white/5">
                                        <div className="text-2xl font-bold text-white">{analysis.h2_count}</div>
                                        <div className="text-xs text-white/50">H2 Tags</div>
                                    </div>
                                    <div className="text-center p-3 bg-white/5 rounded-xl border border-white/5">
                                        <div className="text-2xl font-bold text-white">{analysis.word_count.toLocaleString()}</div>
                                        <div className="text-xs text-white/50">Words</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Technical SEO */}
                        <div className="glass-card p-6 rounded-2xl">
                            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                <Shield className="w-5 h-5 text-indigo-400" />
                                Technical SEO
                            </h3>

                            <div className="space-y-3">
                                {[
                                    { label: 'SSL Certificate', value: analysis.has_ssl, icon: Shield },
                                    { label: 'Sitemap.xml', value: analysis.has_sitemap, icon: FileText },
                                    { label: 'Robots.txt', value: analysis.has_robots_txt, icon: FileText },
                                    { label: 'Canonical Tag', value: analysis.has_canonical, icon: Link2 },
                                    { label: 'Schema Markup', value: analysis.has_schema_markup, icon: Code },
                                ].map((item) => (
                                    <div key={item.label} className={clsx(
                                        "flex items-center justify-between p-4 rounded-xl border transition-colors",
                                        item.value
                                            ? "bg-emerald-500/10 border-emerald-500/20"
                                            : "bg-rose-500/10 border-rose-500/20"
                                    )}>
                                        <div className="flex items-center gap-3">
                                            <item.icon className={clsx("w-4 h-4", item.value ? "text-emerald-400" : "text-rose-400")} />
                                            <span className="text-white/80">{item.label}</span>
                                        </div>
                                        {item.value ? (
                                            <CheckCircle className="w-5 h-5 text-emerald-400" />
                                        ) : (
                                            <XCircle className="w-5 h-5 text-rose-400" />
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Images */}
                        <div className="glass-card p-6 rounded-2xl">
                            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                <Image className="w-5 h-5 text-cyan-400" />
                                Image Optimization
                            </h3>

                            <div className="flex items-center justify-between mb-6">
                                <div>
                                    <div className="text-4xl font-bold text-white">{analysis.images_with_alt}</div>
                                    <div className="text-white/50">of {analysis.total_images} with alt text</div>
                                </div>
                                <div className={clsx(
                                    "w-20 h-20 rounded-full flex flex-col items-center justify-center border-4",
                                    getScoreBg(analysis.images_score),
                                    getScoreColor(analysis.images_score)
                                )}>
                                    <span className="text-2xl font-bold">{analysis.images_score}</span>
                                    <span className="text-xs opacity-70">%</span>
                                </div>
                            </div>

                            <div className="h-3 bg-white/10 rounded-full overflow-hidden">
                                <div
                                    className={clsx(
                                        "h-full rounded-full transition-all duration-500",
                                        analysis.images_score >= 80 ? "bg-gradient-to-r from-emerald-500 to-emerald-400" :
                                            analysis.images_score >= 60 ? "bg-gradient-to-r from-amber-500 to-amber-400" :
                                                "bg-gradient-to-r from-rose-500 to-rose-400"
                                    )}
                                    style={{ width: `${analysis.total_images > 0 ? (analysis.images_with_alt / analysis.total_images) * 100 : 100}%` }}
                                />
                            </div>
                        </div>

                        {/* Links */}
                        <div className="glass-card p-6 rounded-2xl">
                            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                                <Link2 className="w-5 h-5 text-purple-400" />
                                Link Profile
                            </h3>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-5 bg-gradient-to-br from-blue-500/20 to-blue-500/5 rounded-xl border border-blue-500/20 text-center">
                                    <div className="text-4xl font-bold text-blue-400">{analysis.internal_links}</div>
                                    <div className="text-sm text-white/50 mt-1">Internal Links</div>
                                </div>
                                <div className="p-5 bg-gradient-to-br from-purple-500/20 to-purple-500/5 rounded-xl border border-purple-500/20 text-center">
                                    <div className="text-4xl font-bold text-purple-400">{analysis.external_links}</div>
                                    <div className="text-sm text-white/50 mt-1">External Links</div>
                                </div>
                            </div>

                            <div className="mt-4 p-4 bg-white/5 rounded-xl border border-white/5">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-white/70">Link Balance</span>
                                    <span className={getScoreColor(analysis.links_score)}>{analysis.links_score}/100</span>
                                </div>
                                <div className="h-2 bg-white/10 rounded-full overflow-hidden flex">
                                    <div
                                        className="h-full bg-blue-500"
                                        style={{ width: `${analysis.internal_links + analysis.external_links > 0 ? (analysis.internal_links / (analysis.internal_links + analysis.external_links)) * 100 : 50}%` }}
                                    />
                                    <div
                                        className="h-full bg-purple-500"
                                        style={{ width: `${analysis.internal_links + analysis.external_links > 0 ? (analysis.external_links / (analysis.internal_links + analysis.external_links)) * 100 : 50}%` }}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            ) : (
                <div className="glass-card p-12 rounded-2xl text-center">
                    <div className="w-20 h-20 rounded-full bg-violet-500/10 border border-violet-500/20 flex items-center justify-center mx-auto mb-6">
                        <Search className="w-10 h-10 text-violet-400" />
                    </div>
                    <h3 className="text-2xl font-bold text-white mb-3">No Analysis Available</h3>
                    <p className="text-white/50 mb-8 max-w-md mx-auto">
                        Click "Analyze Now" to run a comprehensive SEO audit on the selected competitor's website
                    </p>
                    <button
                        onClick={handleAnalyze}
                        disabled={analyzing}
                        className="btn-primary"
                    >
                        {analyzing ? (
                            <RefreshCw className="w-5 h-5 animate-spin" />
                        ) : (
                            <Sparkles className="w-5 h-5" />
                        )}
                        {analyzing ? 'Analyzing...' : 'Run SEO Analysis'}
                    </button>
                </div>
            )}
        </div>
    )
}
