import { useState, useEffect } from 'react'
import { DollarSign, RefreshCw, TrendingUp, Tag, Percent } from 'lucide-react'
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
        setLoading(true)
        pricesApi.get(selectedCompetitor).then(res => {
            setPrices(res.data)
            if (res.data.length) setSelectedProduct(res.data[0].product_name)
        }).catch((error) => {
            console.error('Failed to fetch prices:', error)
            // Show empty state - no mock data
            setPrices([])
            setChartData([])
        }).finally(() => setLoading(false))
    }, [selectedCompetitor])

    const onSaleCount = prices.filter(p => p.is_on_sale).length
    const avgPrice = prices.length ? prices.reduce((s, p) => s + p.price, 0) / prices.length : 0

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div><h2 className="text-2xl font-bold text-white">Price Monitor</h2><p className="text-white/50">Track pricing changes</p></div>
                <select value={selectedCompetitor} onChange={e => setSelectedCompetitor(e.target.value)} className="input-glass w-auto">
                    {competitors.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
            </div>

            <div className="grid grid-cols-4 gap-4">
                <div className="glass-card p-4 rounded-xl"><DollarSign className="w-8 h-8 text-accent-green mb-2" /><div className="text-2xl font-bold text-white">{prices.length}</div><div className="text-sm text-white/50">Products</div></div>
                <div className="glass-card p-4 rounded-xl"><Tag className="w-8 h-8 text-accent-orange mb-2" /><div className="text-2xl font-bold text-accent-orange">{onSaleCount}</div><div className="text-sm text-white/50">On Sale</div></div>
                <div className="glass-card p-4 rounded-xl"><TrendingUp className="w-8 h-8 text-accent-purple mb-2" /><div className="text-2xl font-bold text-white">${avgPrice.toFixed(0)}</div><div className="text-sm text-white/50">Avg Price</div></div>
                <div className="glass-card p-4 rounded-xl"><Percent className="w-8 h-8 text-accent-cyan mb-2" /><div className="text-2xl font-bold text-accent-cyan">{Math.round((onSaleCount / (prices.length || 1)) * 100)}%</div><div className="text-sm text-white/50">Discount Rate</div></div>
            </div>

            {loading ? <div className="flex justify-center h-64"><RefreshCw className="w-8 h-8 text-accent-purple animate-spin" /></div> : (
                <div className="grid lg:grid-cols-2 gap-6">
                    <div className="glass-card p-6 rounded-2xl">
                        <h3 className="text-lg font-semibold text-white mb-4">Price History</h3>
                        <ResponsiveContainer width="100%" height={250}>
                            <LineChart data={chartData}><CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" /><XAxis dataKey="date" stroke="rgba(255,255,255,0.5)" /><YAxis stroke="rgba(255,255,255,0.5)" /><Tooltip contentStyle={{ backgroundColor: '#1a1a24', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} /><Line type="monotone" dataKey="price" stroke="#8b5cf6" strokeWidth={2} /></LineChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="glass-card p-6 rounded-2xl">
                        <h3 className="text-lg font-semibold text-white mb-4">Current Prices</h3>
                        <div className="space-y-3">
                            {prices.map(p => (
                                <div key={p.id} onClick={() => setSelectedProduct(p.product_name)} className={clsx("p-4 rounded-xl border cursor-pointer", selectedProduct === p.product_name ? "bg-accent-purple/10 border-accent-purple/30" : "bg-white/5 border-white/10 hover:border-white/20")}>
                                    <div className="flex justify-between items-center">
                                        <div><h4 className="font-medium text-white">{p.product_name}</h4><span className="text-xl font-bold text-accent-green">${p.price}</span>{p.original_price && <span className="text-sm text-white/40 line-through ml-2">${p.original_price}</span>}</div>
                                        {p.is_on_sale && <span className="badge badge-warning">{p.discount_percent}% OFF</span>}
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
