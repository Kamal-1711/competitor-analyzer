import { useState, useEffect } from 'react'
import { Target, RefreshCw, FileText, Search, Zap } from 'lucide-react'
import { gapsApi } from '../services/api'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ZAxis } from 'recharts'
import clsx from 'clsx'

interface GapSummary { feature_gaps: number; content_gaps: number; keyword_opportunities: number; overall_opportunity_score: number }
interface FeatureGap { feature_name: string; your_status: string | null; competitors: Record<string, string> }
interface KeywordOpp { keyword: string; competitors_ranking: string[]; opportunity_score: number }

export default function GapFinder() {
    const [summary, setSummary] = useState<GapSummary | null>(null)
    const [features, setFeatures] = useState<FeatureGap[]>([])
    const [keywords, setKeywords] = useState<KeywordOpp[]>([])
    const [positioning, setPositioning] = useState<{ name: string; x: number; y: number; size: number }[]>([])
    const [loading, setLoading] = useState(true)
    const [tab, setTab] = useState<'features' | 'content' | 'keywords'>('features')

    useEffect(() => {
        Promise.all([gapsApi.getSummary(), gapsApi.getFeatures(), gapsApi.getKeywords(), gapsApi.getPositioning()])
            .then(([sumRes, featRes, kwRes, posRes]) => {
                setSummary(sumRes.data)
                setFeatures(featRes.data)
                setKeywords(kwRes.data)
                setPositioning(posRes.data.data || [])
            }).catch((err) => {
                console.error('Failed to fetch gap data:', err)
                // Leave state empty — UI will show empty state
            }).finally(() => setLoading(false))
    }, [])

    if (loading) return <div className="flex justify-center h-96"><RefreshCw className="w-8 h-8 text-accent-purple animate-spin" /></div>

    if (!summary) return (
        <div className="glass-card p-12 rounded-2xl text-center">
            <Target className="w-16 h-16 text-white/20 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No gap analysis yet</h3>
            <p className="text-white/50">Add and scan competitors to generate gap insights</p>
        </div>
    )

    return (
        <div className="space-y-6">
            <div><h2 className="text-2xl font-bold text-white">Gap Finder</h2><p className="text-white/50">Identify opportunities and gaps</p></div>

            <div className="grid grid-cols-4 gap-4">
                <div className="glass-card p-4 rounded-xl"><Target className="w-8 h-8 text-accent-purple mb-2" /><div className="text-2xl font-bold text-white">{summary?.feature_gaps}</div><div className="text-sm text-white/50">Feature Gaps</div></div>
                <div className="glass-card p-4 rounded-xl"><FileText className="w-8 h-8 text-accent-blue mb-2" /><div className="text-2xl font-bold text-accent-blue">{summary?.content_gaps}</div><div className="text-sm text-white/50">Content Gaps</div></div>
                <div className="glass-card p-4 rounded-xl"><Search className="w-8 h-8 text-accent-cyan mb-2" /><div className="text-2xl font-bold text-accent-cyan">{summary?.keyword_opportunities}</div><div className="text-sm text-white/50">Keyword Opps</div></div>
                <div className="glass-card p-4 rounded-xl"><Zap className="w-8 h-8 text-accent-green mb-2" /><div className="text-2xl font-bold text-accent-green">{summary?.overall_opportunity_score}</div><div className="text-sm text-white/50">Opportunity Score</div></div>
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
                <div className="glass-card p-6 rounded-2xl">
                    <h3 className="text-lg font-semibold text-white mb-4">Market Positioning</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <ScatterChart><CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" /><XAxis dataKey="x" name="SEO" stroke="rgba(255,255,255,0.5)" /><YAxis dataKey="y" name="Content" stroke="rgba(255,255,255,0.5)" /><ZAxis dataKey="size" range={[100, 500]} /><Tooltip contentStyle={{ backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} /><Scatter name="Competitors" data={positioning} fill="#8b5cf6" /></ScatterChart>
                    </ResponsiveContainer>
                </div>

                <div className="glass-card p-6 rounded-2xl">
                    <div className="flex gap-2 mb-4">
                        {(['features', 'keywords'] as const).map(t => (
                            <button key={t} onClick={() => setTab(t)} className={clsx("px-4 py-2 rounded-lg text-sm", tab === t ? "bg-gradient-mesh text-white" : "bg-white/5 text-white/50")}>{t === 'features' ? 'Feature Gaps' : 'Keywords'}</button>
                        ))}
                    </div>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                        {tab === 'features' ? features.map((f, i) => (
                            <div key={i} className="p-3 bg-white/5 rounded-lg flex justify-between items-center">
                                <span className="text-white">{f.feature_name}</span>
                                <span className={clsx("badge", f.your_status === 'Missing' ? "badge-danger" : "badge-success")}>{f.your_status}</span>
                            </div>
                        )) : keywords.map((k, i) => (
                            <div key={i} className="p-3 bg-white/5 rounded-lg flex justify-between items-center">
                                <span className="text-white">{k.keyword}</span>
                                <span className="badge badge-purple">{k.opportunity_score}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
