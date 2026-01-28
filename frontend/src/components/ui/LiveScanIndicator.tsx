import { useLiveScan } from '../../hooks/useNotifications'
import { RefreshCw, Globe, CheckCircle, XCircle } from 'lucide-react'
import clsx from 'clsx'

interface LiveScanIndicatorProps {
    scanId?: string
    className?: string
}

export function LiveScanIndicator({ scanId, className }: LiveScanIndicatorProps) {
    const { currentScan, isConnected, isScanning } = useLiveScan(scanId)

    if (!currentScan) return null

    return (
        <div className={clsx('glass-card p-4 rounded-xl', className)}>
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    {isScanning ? (
                        <RefreshCw className="w-5 h-5 text-accent-purple animate-spin" />
                    ) : currentScan.status === 'completed' ? (
                        <CheckCircle className="w-5 h-5 text-accent-green" />
                    ) : (
                        <XCircle className="w-5 h-5 text-accent-red" />
                    )}
                    <span className="font-medium text-white">
                        {isScanning ? 'Scanning...' :
                            currentScan.status === 'completed' ? 'Completed' : 'Failed'}
                    </span>
                </div>
                <div className="flex items-center gap-1.5">
                    <div className={clsx(
                        'w-2 h-2 rounded-full',
                        isConnected ? 'bg-accent-green animate-pulse' : 'bg-accent-red'
                    )} />
                    <span className="text-xs text-white/50">
                        {isConnected ? 'Live' : 'Disconnected'}
                    </span>
                </div>
            </div>

            {isScanning && (
                <>
                    {/* Progress bar */}
                    <div className="h-2 bg-white/10 rounded-full overflow-hidden mb-2">
                        <div
                            className="h-full bg-gradient-mesh transition-all duration-500 rounded-full"
                            style={{ width: `${currentScan.progress}%` }}
                        />
                    </div>

                    <div className="flex justify-between items-center text-sm">
                        <span className="text-accent-purple font-medium">{currentScan.progress}%</span>
                        <div className="flex items-center gap-1 text-white/50 truncate max-w-[200px]">
                            <Globe className="w-3 h-3 flex-shrink-0" />
                            <span className="truncate">{currentScan.currentUrl}</span>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

// Compact version for sidebar/header
export function ScanStatusBadge() {
    const { currentScan, isScanning } = useLiveScan()

    if (!isScanning) return null

    return (
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent-purple/20 border border-accent-purple/30">
            <RefreshCw className="w-3 h-3 text-accent-purple animate-spin" />
            <span className="text-xs text-accent-purple font-medium">{currentScan?.progress}%</span>
        </div>
    )
}
