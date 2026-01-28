
interface HealthScoreProps {
    score: number
    strengths: number
    neutrals: number
    weaknesses: number
}

export default function HealthScore({ score, strengths, neutrals, weaknesses }: HealthScoreProps) {
    const circumference = 2 * Math.PI * 80
    const strokeDashoffset = circumference - (score / 100) * circumference

    const scoreColor = score >= 70 ? '#10b981' : score >= 40 ? '#f59e0b' : '#ef4444'
    const statusText = score >= 70 ? 'Good' : score >= 40 ? 'Fair' : 'Poor'

    return (
        <div className="glass-card p-6 h-full">
            <h3 className="text-lg font-semibold text-white mb-1">Competitive Health Score</h3>
            <p className="text-gray-400 text-sm mb-6">Overall competitive positioning</p>

            {/* Gauge Chart */}
            <div className="flex justify-center mb-8 relative">
                <div className="relative w-48 h-48">
                    <svg className="w-48 h-48 transform -rotate-90" viewBox="0 0 200 200">
                        {/* Background */}
                        <circle cx="100" cy="100" r="80"
                            fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="16"
                            className="gauge-bg"
                        />
                        {/* Progress */}
                        <circle cx="100" cy="100" r="80"
                            fill="none" stroke={scoreColor} strokeWidth="16"
                            strokeLinecap="round"
                            strokeDasharray={circumference}
                            strokeDashoffset={strokeDashoffset}
                            className="gauge-fill transition-all duration-1000 ease-out drop-shadow-lg"
                        />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className="text-5xl font-bold text-white tracking-tighter">{score}<span className="text-3xl text-gray-500">-</span></span>
                        <span className="text-xl font-medium mt-1" style={{ color: scoreColor }}>{statusText}</span>
                    </div>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-3">
                <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-3 text-center transition-transform hover:scale-105">
                    <div className="text-lg font-bold text-green-400 block mb-1">{strengths}</div>
                    <span className="text-xs font-medium text-green-300/70 block uppercase tracking-wider">Strengths</span>
                </div>
                <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-3 text-center transition-transform hover:scale-105">
                    <div className="text-lg font-bold text-yellow-400 block mb-1">{neutrals}</div>
                    <span className="text-xs font-medium text-yellow-300/70 block uppercase tracking-wider">Neutral</span>
                </div>
                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-center transition-transform hover:scale-105">
                    <div className="text-lg font-bold text-red-400 block mb-1">{weaknesses}</div>
                    <span className="text-xs font-medium text-red-300/70 block uppercase tracking-wider">Weaknesses</span>
                </div>
            </div>
        </div>
    )
}
