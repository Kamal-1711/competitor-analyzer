import { MoreVertical, ExternalLink } from 'lucide-react'
import clsx from 'clsx'
import { Link } from 'react-router-dom'

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

interface CompetitorCardProps {
    competitor: Competitor
}

export default function CompetitorCard({ competitor }: CompetitorCardProps) {
    const {
        id,
        name,
        competitor_type,
        health_score,
        seo_score,
        content_score,
        url
    } = competitor

    // Generate specific colors/gradients based on name/mock
    const getLogoStyle = (name: string) => {
        const n = name.toLowerCase()
        if (n.includes('edgar')) return 'bg-gradient-to-br from-emerald-400 to-cyan-500 shadow-emerald-500/20'
        if (n.includes('brix')) return 'bg-gradient-to-br from-amber-400 to-orange-500 shadow-orange-500/20'
        if (n.includes('flow')) return 'bg-gradient-to-br from-violet-400 to-purple-500 shadow-purple-500/20'
        return 'bg-gradient-to-br from-gray-700 to-gray-600'
    }

    const logoStyle = getLogoStyle(name)
    const initials = name.substring(0, 2).toUpperCase()

    // Helper for score color
    const getScoreColor = (score: number) => {
        if (score >= 80) return 'text-emerald-400'
        if (score >= 60) return 'text-amber-400'
        return 'text-rose-400'
    }

    return (
        <div className="glass-card-hover p-6 group relative flex flex-col h-full">
            <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <a href={url} target="_blank" rel="noopener noreferrer" className="p-2 text-gray-400 hover:text-white transition-colors">
                    <ExternalLink className="w-4 h-4" />
                </a>
            </div>

            <div className="flex justify-between items-start mb-6">
                <div className="flex items-start gap-4">
                    <div className={clsx("w-14 h-14 rounded-2xl flex items-center justify-center font-bold text-xl text-white shadow-lg ring-1 ring-white/20", logoStyle)}>
                        {initials}
                    </div>
                    <div>
                        <Link to={`/competitors/${id}`} className="block">
                            <h4 className="font-semibold text-white text-lg leading-tight group-hover:text-blue-400 transition-colors mb-1.5">{name}</h4>
                        </Link>
                        <span className={clsx(
                            "inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border",
                            competitor_type === 'direct'
                                ? 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20'
                                : 'bg-slate-500/10 text-slate-400 border-slate-500/20'
                        )}>
                            {competitor_type}
                        </span>
                    </div>
                </div>
            </div>

            <div className="mt-auto pt-4">
                <div className="grid grid-cols-3 gap-2 p-1.5 bg-black/20 rounded-2xl border border-white/5">
                    <div className="text-center p-2 rounded-xl hover:bg-white/5 transition-colors">
                        <div className={clsx("text-xl font-bold mb-0.5", getScoreColor(health_score))}>{health_score}</div>
                        <div className="text-[10px] uppercase font-semibold text-gray-500 tracking-wider">Health</div>
                    </div>
                    <div className="text-center p-2 rounded-xl hover:bg-white/5 transition-colors relative">
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-px h-8 bg-white/5" />
                        <div className={clsx("text-xl font-bold mb-0.5", getScoreColor(seo_score))}>{seo_score}</div>
                        <div className="text-[10px] uppercase font-semibold text-gray-500 tracking-wider">SEO</div>
                        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-px h-8 bg-white/5" />
                    </div>
                    <div className="text-center p-2 rounded-xl hover:bg-white/5 transition-colors">
                        <div className={clsx("text-xl font-bold mb-0.5", getScoreColor(content_score))}>{content_score}</div>
                        <div className="text-[10px] uppercase font-semibold text-gray-500 tracking-wider">Content</div>
                    </div>
                </div>
            </div>
        </div>
    )
}
