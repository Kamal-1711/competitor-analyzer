import { useState, useEffect } from 'react'
import { DollarSign, RefreshCw, TrendingUp, Tag, Percent, Search, AlertCircle, Sparkles } from 'lucide-react'
import { competitorsApi, pricesApi } from '../services/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import clsx from 'clsx'

interface Competitor { id: string; name: string }
interface PriceItem { id: string; product_name: string; price: number; original_price: number | null; currency: string; is_on_sale: boolean; discount_percent: number | null }

export default function PriceMonitor() {
    const [competitors, setCompetitors] = useState<Competitor[]>([])
    const [selectedCompetitor, setSelectedCompetitor] = useState('')
    const [prices, setPrices] = useState<PriceItem[]>([])
    const [loading, setLoading] = useState(false)
    const [scanning, setScanning] = useState(false)
    const [scanMessage, setScanMessage] = useState<string | null>(null)
    const [chartData, setChartData] = useState<{ date: string; price: number }[]>([])
    const [selectedProduct, setSelectedProduct] = useState('')

    useEffect(() => {
        competitorsApi.list().then(res => {
            setCompetitors(res.data)
            if (res.data.length) setSelectedCompetitor(res.data[0].id)
        }).catch(() => { })
    }, [])

    useEffect(() => {
        if (!selectedCompetitor) return
        fetchPrices()
    }, [selectedCompetitor])

    const fetchPrices = async () => {
        setLoading(true)
        setScanMessage(null)
        pricesApi.get(selectedCompetitor).then(res => {
            setPrices(res.data)
            if (res.data.length) {
                setSelectedProduct(res.data[0].product_name)
                // Fetch history for first product
                pricesApi.getHistory(selectedCompetitor, res.data[0].product_name).then(histRes => {
                    setChartData(histRes.data.history.map((h: { date: string; price: number }) => ({
                        date: new Date(h.date).toLocaleDateString(),
                        price: h.price
                    })))
                }).catch(() => setChartData([]))
            } else {
                setChartData([])
            }
        }).catch((error) => {
            console.error('Failed to fetch prices:', error)
            setPrices([])
            setChartData([])
        }).finally(() => setLoading(false))
    }

    const handleScan = async () => {
        setScanning(true)
        setScanMessage(null)
        try {
            const res = await pricesApi.scan(selectedCompetitor)
            setScanMessage(res.data.message)
            // Refresh prices after scan
            await fetchPrices()
        } catch (error) {
            console.error('Scan failed:', error)
            setScanMessage('Scan failed. Please try again.')
        } finally {
            setScanning(false)
        }
    }

    const handleProductSelect = async (productName: string) => {
        setSelectedProduct(productName)
        try {
            const histRes = await pricesApi.getHistory(selectedCompetitor, productName)
            setChartData(histRes.data.history.map((h: { date: string; price: number }) => ({
                date: new Date(h.date).toLocaleDateString(),
                price: h.price
            })))
        } catch {
            setChartData([])
        }
    }

    const onSaleCount = prices.filter(p => p.is_on_sale).length
    const avgPrice = prices.length ? prices.reduce((s, p) => s + p.price, 0) / prices.length : 0

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-gradient-to-br from-emerald-500/20 to-green-500/20 border border-emerald-500/20">
                            <DollarSign className="w-6 h-6 text-emerald-400" />
                        </div>
                        Price Monitor
                    </h2>
                    <p className="text-white/50 mt-1">Track pricing changes and deals</p>
                </div>
                <div className="flex items-center gap-3">
                    <select value={selectedCompetitor} onChange={e => setSelectedCompetitor(e.target.value)} className="input-glass w-auto">
                        {competitors.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                    </select>
                    <button
                        onClick={handleScan}
                        disabled={scanning || !selectedCompetitor}
                        className="btn-primary"
                    >
                        {scanning ? (
                            <RefreshCw className="w-5 h-5 animate-spin" />
                        ) : (
                            <Search className="w-5 h-5" />
                        )}
                        {scanning ? 'Scanning...' : 'Scan Prices'}
                    </button>
                </div>
            </div>

            {scanMessage && (
                <div className={clsx(
                    "p-4 rounded-xl border flex items-center gap-3",
                    scanMessage.includes('No pricing') || scanMessage.includes('failed')
                        ? "bg-amber-500/10 border-amber-500/20 text-amber-400"
                        : "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                )}>
                    <AlertCircle className="w-5 h-5 shrink-0" />
                    <span>{scanMessage}</span>
                </div>
            )}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="glass-card p-4 rounded-xl">
                    <DollarSign className="w-8 h-8 text-accent-green mb-2" />
                    <div className="text-2xl font-bold text-white">{prices.length}</div>
                    <div className="text-sm text-white/50">Products Tracked</div>
                </div>
                <div className="glass-card p-4 rounded-xl">
                    <Tag className="w-8 h-8 text-accent-orange mb-2" />
                    <div className="text-2xl font-bold text-accent-orange">{onSaleCount}</div>
                    <div className="text-sm text-white/50">On Sale</div>
                </div>
                <div className="glass-card p-4 rounded-xl">
                    <TrendingUp className="w-8 h-8 text-accent-purple mb-2" />
                    <div className="text-2xl font-bold text-white">${avgPrice.toFixed(0)}</div>
                    <div className="text-sm text-white/50">Avg Price</div>
                </div>
                <div className="glass-card p-4 rounded-xl">
                    <Percent className="w-8 h-8 text-accent-cyan mb-2" />
                    <div className="text-2xl font-bold text-accent-cyan">{Math.round((onSaleCount / (prices.length || 1)) * 100)}%</div>
                    <div className="text-sm text-white/50">Discount Rate</div>
                </div>
            </div>

            {loading ? (
                <div className="flex justify-center h-64">
                    <RefreshCw className="w-8 h-8 text-accent-purple animate-spin" />
                </div>
            ) : prices.length === 0 ? (
                <div className="glass-card p-12 rounded-2xl text-center">
                    <div className="w-20 h-20 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-6">
                        <DollarSign className="w-10 h-10 text-emerald-400" />
                    </div>
                    <h3 className="text-2xl font-bold text-white mb-3">No Prices Found</h3>
                    <p className="text-white/50 mb-8 max-w-md mx-auto">
                        Click "Scan Prices" to search for pricing information on the competitor's website.
                        Works best with e-commerce sites that display product prices publicly.
                    </p>
                    <button
                        onClick={handleScan}
                        disabled={scanning}
                        className="btn-primary"
                    >
                        {scanning ? (
                            <RefreshCw className="w-5 h-5 animate-spin" />
                        ) : (
                            <Sparkles className="w-5 h-5" />
                        )}
                        {scanning ? 'Scanning...' : 'Scan for Prices'}
                    </button>
                </div>
            ) : (
                <div className="grid lg:grid-cols-2 gap-6">
                    <div className="glass-card p-6 rounded-2xl">
                        <h3 className="text-lg font-semibold text-white mb-4">Price History</h3>
                        {chartData.length > 0 ? (
                            <ResponsiveContainer width="100%" height={250}>
                                <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                                    <XAxis dataKey="date" stroke="rgba(255,255,255,0.5)" fontSize={12} />
                                    <YAxis stroke="rgba(255,255,255,0.5)" fontSize={12} />
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: '#1a1a24',
                                            border: '1px solid rgba(255,255,255,0.1)',
                                            borderRadius: '8px'
                                        }}
                                    />
                                    <Line type="monotone" dataKey="price" stroke="#8b5cf6" strokeWidth={2} dot={{ fill: '#8b5cf6' }} />
                                </LineChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-[250px] flex items-center justify-center text-white/40">
                                <p>Select a product to view price history</p>
                            </div>
                        )}
                    </div>
                    <div className="glass-card p-6 rounded-2xl">
                        <h3 className="text-lg font-semibold text-white mb-4">Current Prices</h3>
                        <div className="space-y-3 max-h-[300px] overflow-y-auto">
                            {prices.map(p => (
                                <div
                                    key={p.id}
                                    onClick={() => handleProductSelect(p.product_name)}
                                    className={clsx(
                                        "p-4 rounded-xl border cursor-pointer transition-all",
                                        selectedProduct === p.product_name
                                            ? "bg-accent-purple/10 border-accent-purple/30"
                                            : "bg-white/5 border-white/10 hover:border-white/20"
                                    )}
                                >
                                    <div className="flex justify-between items-center">
                                        <div>
                                            <h4 className="font-medium text-white line-clamp-1">{p.product_name}</h4>
                                            <div className="flex items-baseline gap-2 mt-1">
                                                <span className="text-xl font-bold text-accent-green">
                                                    {p.currency === 'USD' ? '$' : p.currency}{p.price}
                                                </span>
                                                {p.original_price && (
                                                    <span className="text-sm text-white/40 line-through">
                                                        ${p.original_price}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        {p.is_on_sale && p.discount_percent && (
                                            <span className="px-2 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                                                {p.discount_percent}% OFF
                                            </span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
