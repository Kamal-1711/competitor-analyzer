import { RefreshCw } from 'lucide-react'

interface ScanProgressProps {
    isScanning: boolean
    progress: number
    currentUrl?: string
    pagesTotal?: number
    pagesCrawled?: number
}

export default function ScanProgress({
    isScanning,
    progress,
    currentUrl
}: ScanProgressProps) {
    if (!isScanning) {
        return null
    }

    return (
        <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-500/10 rounded-lg">
                        <RefreshCw className="w-5 h-5 text-accent-blue animate-spin" />
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <span className="text-white font-medium">Scanning competitors...</span>
                            <span className="font-bold text-accent-blue">{Math.round(progress)}%</span>
                        </div>
                        {currentUrl && (
                            <div className="text-xs text-gray-400 mt-0.5 truncate max-w-md hidden md:block">
                                {currentUrl}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                <div
                    className="h-full bg-gradient-to-r from-accent-blue to-accent-purple rounded-full transition-all duration-300 ease-out shadow-glow-blue"
                    style={{ width: `${progress}%` }}
                />
            </div>
        </div>
    )
}
