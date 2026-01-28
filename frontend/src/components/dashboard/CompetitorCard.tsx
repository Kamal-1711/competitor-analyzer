import { MoreVertical } from 'lucide-react'
import clsx from 'clsx'

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
        name,
        competitor_type,
        health_score,
        seo_score,
        content_score
    } = competitor

    // Generate specific colors based on name/mock just for visual parity with screenshot
    const getLogoStyle = (name: string) => {
        const n = name.toLowerCase()
        if (n.includes('edgar')) return 'bg-gradient-success text-white'
        if (n.includes('brix')) return 'bg-gradient-warm text-white'
        if (n.includes('flow')) return 'bg-gradient-cool text-white'
        return 'bg-white/10 text-gray-300'
    }

    const logoStyle = getLogoStyle(name)
    const initials = name.substring(0, 2).toUpperCase()

    return (
        <div className="glass-card-hover p-6 group">
            <div className="flex justify-between items-start mb-6">
                <div className="flex items-start gap-4">
                    <div className={clsx("w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg shadow-lg", logoStyle)}>
                        {initials}
                    </div>
                    <div>
                        <h4 className="font-semibold text-white text-lg leading-tight group-hover:text-accent-blue transition-colors">{name}</h4>
                        <span className="inline-block px-2.5 py-1 mt-2 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-medium">
                            {competitor_type}
                        </span>
                    </div>
                </div>
                <button className="text-gray-500 hover:text-white transition-colors p-1">
                    <MoreVertical className="w-5 h-5" />
                </button>
            </div>

            <div className="flex justify-between items-center text-center px-2 py-4 bg-white/5 rounded-xl border border-white/5">
                <div>
                    <div className="text-2xl font-bold text-white">{health_score}</div>
                    <div className="text-xs text-gray-400 font-medium mt-1">Health</div>
                </div>
                <div className="w-px h-8 bg-white/10" />
                <div>
                    <div className="text-2xl font-bold text-white">{seo_score}</div>
                    <div className="text-xs text-gray-400 font-medium mt-1">SEO</div>
                </div>
                <div className="w-px h-8 bg-white/10" />
                <div>
                    <div className="text-2xl font-bold text-white">{content_score}</div>
                    <div className="text-xs text-gray-400 font-medium mt-1">Content</div>
                </div>
            </div>
        </div>
    )
}
