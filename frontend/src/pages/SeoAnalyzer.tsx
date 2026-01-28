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
} from 'lucide-react'
import { competitorsApi, seoApi } from '../services/api'
import clsx from 'clsx'

interface Competitor {
    id: string
    name: string
    domain: string
}

interface SeoAnalysis {
    overall_score: number
    title: string
    title_score: number
    meta_description: string
    meta_description_score: number
    h1_count: number
    h2_count: number
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
            const [analysisRes, auditRes] = await Promise.all([
                seoApi.get(selectedCompetitor),
                seoApi.getAudit(selectedCompetitor)
            ])
            setAnalysis(analysisRes.data)
            void auditRes.data
        } catch (error) {
            console.error('Failed to fetch SEO data:', error)
            // Show empty state - no mock data
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
        if (score >= 80) return 'text-accent-green'
        if (score >= 60) return 'text-accent-orange'
        return 'text-accent-red'
    }

    const getScoreBg = (score: number) => {
        if (score >= 80) return 'bg-accent-green/20 border-accent-green/30'
        if (score >= 60) return 'bg-accent-orange/20 border-accent-orange/30'
        return 'bg-accent-red/20 border-accent-red/30'
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white">SEO Analyzer</h2>
                    <p className="text-white/50">Analyze and compare SEO performance</p>
                </div>

                <div className="flex items-center gap-3">
                    <select
                        value={selectedCompetitor}
                        onChange={(e) => setSelectedCompetitor(e.target.value)}
                        className="input-glass"
                    >
                        {competitors.map((c) => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                    </select>

                    <button
                        onClick={handleAnalyze}
                        disabled={analyzing}
                        className="btn-primary flex items-center gap-2"
                    >
                        {analyzing ? (
                            <RefreshCw className="w-5 h-5 animate-spin" />
                        ) : (
                            <Search className="w-5 h-5" />
                        )}
                        Analyze
                    </button>
                </div>
            </div>

            {loading ? (
                <div className="flex items-center justify-center h-96">
                    <RefreshCw className="w-8 h-8 text-accent-purple animate-spin" />
                </div>
            ) : analysis ? (
                <>
                    {/* Overall Score */}
                    <div className="glass-card p-8 rounded-2xl">
                        <div className="flex items-center justify-between">
                            <div>
                                <h3 className="text-lg font-semibold text-white mb-2">Overall SEO Score</h3>
                                <p className="text-white/50">Based on on-page, technical, and content analysis</p>
                            </div>

                            <div className="text-center">
                                <div className={clsx(
                                    "text-6xl font-bold",
                                    getScoreColor(analysis.overall_score)
                                )}>
                                    {analysis.overall_score}
                                </div>
                                <div className="text-white/50">/ 100</div>
                            </div>
                        </div>
                    </div>

                    {/* Score Cards */}
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                        {[
                            { label: 'Title', score: analysis.title_score, icon: FileText },
                            { label: 'Meta', score: analysis.meta_description_score, icon: FileText },
                            { label: 'Headers', score: analysis.headers_score, icon: Code },
                            { label: 'Content', score: analysis.content_score, icon: FileText },
                            { label: 'Images', score: analysis.images_score, icon: Image },
                            { label: 'Links', score: analysis.links_score, icon: Link2 },
                        ].map((item) => (
                            <div
                                key={item.label}
                                className={clsx(
                                    "glass-card p-4 rounded-xl border",
                                    getScoreBg(item.score)
                                )}
                            >
                                <item.icon className={clsx("w-5 h-5 mb-2", getScoreColor(item.score))} />
                                <div className={clsx("text-2xl font-bold", getScoreColor(item.score))}>
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
                            <h3 className="text-lg font-semibold text-white mb-4">On-Page SEO</h3>

                            <div className="space-y-4">
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-white/70">Title Tag</span>
                                        <span className={getScoreColor(analysis.title_score)}>{analysis.title_score}/100</span>
                                    </div>
                                    <p className="text-xs text-white/50 truncate">{analysis.title}</p>
                                </div>

                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-white/70">Meta Description</span>
                                        <span className={getScoreColor(analysis.meta_description_score)}>{analysis.meta_description_score}/100</span>
                                    </div>
                                    <p className="text-xs text-white/50 truncate">{analysis.meta_description}</p>
                                </div>

                                <div className="grid grid-cols-3 gap-3 pt-2">
                                    <div className="text-center p-3 bg-white/5 rounded-lg">
                                        <div className="text-xl font-bold text-white">{analysis.h1_count}</div>
                                        <div className="text-xs text-white/50">H1 Tags</div>
                                    </div>
                                    <div className="text-center p-3 bg-white/5 rounded-lg">
                                        <div className="text-xl font-bold text-white">{analysis.h2_count}</div>
                                        <div className="text-xs text-white/50">H2 Tags</div>
                                    </div>
                                    <div className="text-center p-3 bg-white/5 rounded-lg">
                                        <div className="text-xl font-bold text-white">{analysis.word_count}</div>
                                        <div className="text-xs text-white/50">Words</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Technical SEO */}
                        <div className="glass-card p-6 rounded-2xl">
                            <h3 className="text-lg font-semibold text-white mb-4">Technical SEO</h3>

                            <div className="space-y-3">
                                {[
                                    { label: 'SSL Certificate', value: analysis.has_ssl },
                                    { label: 'Sitemap.xml', value: analysis.has_sitemap },
                                    { label: 'Robots.txt', value: analysis.has_robots_txt },
                                    { label: 'Canonical Tag', value: analysis.has_canonical },
                                    { label: 'Schema Markup', value: analysis.has_schema_markup },
                                ].map((item) => (
                                    <div key={item.label} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                                        <span className="text-white/70">{item.label}</span>
                                        {item.value ? (
                                            <CheckCircle className="w-5 h-5 text-accent-green" />
                                        ) : (
                                            <XCircle className="w-5 h-5 text-accent-red" />
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Images */}
                        <div className="glass-card p-6 rounded-2xl">
                            <h3 className="text-lg font-semibold text-white mb-4">Images</h3>

                            <div className="flex items-center justify-between mb-4">
                                <div>
                                    <div className="text-3xl font-bold text-white">{analysis.images_with_alt}</div>
                                    <div className="text-white/50">of {analysis.total_images} with alt text</div>
                                </div>
                                <div className={clsx(
                                    "w-16 h-16 rounded-full flex items-center justify-center text-xl font-bold border-4",
                                    getScoreBg(analysis.images_score),
                                    getScoreColor(analysis.images_score)
                                )}>
                                    {analysis.images_score}%
                                </div>
                            </div>

                            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-mesh rounded-full"
                                    style={{ width: `${(analysis.images_with_alt / analysis.total_images) * 100}%` }}
                                />
                            </div>
                        </div>

                        {/* Links */}
                        <div className="glass-card p-6 rounded-2xl">
                            <h3 className="text-lg font-semibold text-white mb-4">Links</h3>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-4 bg-white/5 rounded-xl text-center">
                                    <div className="text-3xl font-bold text-accent-blue">{analysis.internal_links}</div>
                                    <div className="text-sm text-white/50">Internal Links</div>
                                </div>
                                <div className="p-4 bg-white/5 rounded-xl text-center">
                                    <div className="text-3xl font-bold text-accent-purple">{analysis.external_links}</div>
                                    <div className="text-sm text-white/50">External Links</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            ) : (
                <div className="glass-card p-12 rounded-2xl text-center">
                    <Search className="w-16 h-16 text-white/20 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">No analysis available</h3>
                    <p className="text-white/50 mb-6">
                        Select a competitor and run an analysis to see SEO insights
                    </p>
                </div>
            )}
        </div>
    )
}
