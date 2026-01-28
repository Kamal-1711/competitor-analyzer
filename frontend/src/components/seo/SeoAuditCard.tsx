import { CheckCircle, XCircle, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import clsx from 'clsx'

interface AuditItem {
    name: string
    score: number
    status: 'good' | 'warning' | 'error'
    value: string
    recommendation?: string
}

interface AuditSection {
    title: string
    score: number
    status: 'good' | 'warning' | 'error'
    items: AuditItem[]
}

interface SeoAuditCardProps {
    sections: AuditSection[]
}

const statusIcons = {
    good: CheckCircle,
    warning: AlertCircle,
    error: XCircle
}

const statusColors = {
    good: 'text-accent-green bg-accent-green/10 border-accent-green/20',
    warning: 'text-accent-orange bg-accent-orange/10 border-accent-orange/20',
    error: 'text-accent-red bg-accent-red/10 border-accent-red/20'
}

export function SeoAuditCard({ sections }: SeoAuditCardProps) {
    const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())

    const toggleSection = (title: string) => {
        setExpandedSections(prev => {
            const next = new Set(prev)
            if (next.has(title)) {
                next.delete(title)
            } else {
                next.add(title)
            }
            return next
        })
    }

    return (
        <div className="space-y-3">
            {sections.map(section => {
                const Icon = statusIcons[section.status]
                const isExpanded = expandedSections.has(section.title)

                return (
                    <div key={section.title} className="glass-card rounded-xl overflow-hidden">
                        {/* Section header */}
                        <button
                            onClick={() => toggleSection(section.title)}
                            className="w-full p-4 flex items-center justify-between hover:bg-white/5 transition-colors"
                        >
                            <div className="flex items-center gap-3">
                                <div className={clsx('p-2 rounded-lg border', statusColors[section.status])}>
                                    <Icon className="w-5 h-5" />
                                </div>
                                <div className="text-left">
                                    <h3 className="font-medium text-white">{section.title}</h3>
                                    <p className="text-sm text-white/50">Score: {section.score}/100</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                <div className={clsx(
                                    'px-3 py-1 rounded-full text-sm font-medium',
                                    section.status === 'good' ? 'bg-accent-green/20 text-accent-green' :
                                        section.status === 'warning' ? 'bg-accent-orange/20 text-accent-orange' :
                                            'bg-accent-red/20 text-accent-red'
                                )}>
                                    {section.score}
                                </div>
                                {isExpanded ? (
                                    <ChevronUp className="w-5 h-5 text-white/50" />
                                ) : (
                                    <ChevronDown className="w-5 h-5 text-white/50" />
                                )}
                            </div>
                        </button>

                        {/* Section items */}
                        {isExpanded && (
                            <div className="border-t border-white/10 p-4 space-y-3">
                                {section.items.map((item, idx) => (
                                    <div key={idx} className="flex items-start justify-between p-3 bg-white/5 rounded-lg">
                                        <div className="flex items-start gap-3">
                                            {item.status === 'good' ? (
                                                <CheckCircle className="w-5 h-5 text-accent-green flex-shrink-0 mt-0.5" />
                                            ) : item.status === 'warning' ? (
                                                <AlertCircle className="w-5 h-5 text-accent-orange flex-shrink-0 mt-0.5" />
                                            ) : (
                                                <XCircle className="w-5 h-5 text-accent-red flex-shrink-0 mt-0.5" />
                                            )}
                                            <div>
                                                <p className="font-medium text-white">{item.name}</p>
                                                <p className="text-sm text-white/50">{item.value}</p>
                                                {item.recommendation && (
                                                    <p className="text-sm text-accent-blue mt-1">→ {item.recommendation}</p>
                                                )}
                                            </div>
                                        </div>
                                        <span className={clsx(
                                            'text-sm font-medium px-2 py-0.5 rounded',
                                            item.status === 'good' ? 'text-accent-green' :
                                                item.status === 'warning' ? 'text-accent-orange' :
                                                    'text-accent-red'
                                        )}>
                                            {item.score}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )
            })}
        </div>
    )
}

// Priority fixes card
interface PriorityFix {
    section: string
    item: string
    recommendation: string
    priority: 'high' | 'medium'
}

interface PriorityFixesProps {
    fixes: PriorityFix[]
}

export function PriorityFixes({ fixes }: PriorityFixesProps) {
    if (fixes.length === 0) {
        return (
            <div className="glass-card p-6 rounded-xl text-center">
                <CheckCircle className="w-12 h-12 text-accent-green mx-auto mb-3" />
                <h3 className="font-semibold text-white">All Good!</h3>
                <p className="text-white/50">No critical issues found</p>
            </div>
        )
    }

    return (
        <div className="glass-card rounded-xl overflow-hidden">
            <div className="p-4 border-b border-white/10">
                <h3 className="font-semibold text-white">Priority Fixes</h3>
                <p className="text-sm text-white/50">Address these issues first</p>
            </div>
            <div className="divide-y divide-white/10">
                {fixes.map((fix, idx) => (
                    <div key={idx} className="p-4 flex items-start gap-3">
                        <div className={clsx(
                            'w-2 h-2 rounded-full mt-2 flex-shrink-0',
                            fix.priority === 'high' ? 'bg-accent-red' : 'bg-accent-orange'
                        )} />
                        <div>
                            <div className="flex items-center gap-2">
                                <span className="font-medium text-white">{fix.item}</span>
                                <span className="text-xs text-white/40">{fix.section}</span>
                            </div>
                            <p className="text-sm text-accent-blue mt-1">{fix.recommendation}</p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
