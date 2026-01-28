import { useState, useEffect } from 'react'
import { Package, RefreshCw, Star, Eye, ShoppingCart } from 'lucide-react'
import { competitorsApi, productsApi } from '../services/api'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

interface Competitor { id: string; name: string }
interface ProductItem { id: string; name: string; url: string; category: string | null; image_url: string | null; is_available: boolean; is_new: boolean; first_seen: string }

export default function ProductWatcher() {
    const [competitors, setCompetitors] = useState<Competitor[]>([])
    const [selectedCompetitor, setSelectedCompetitor] = useState('')
    const [products, setProducts] = useState<ProductItem[]>([])
    const [loading, setLoading] = useState(false)
    const [filter, setFilter] = useState<'all' | 'new' | 'unavailable'>('all')

    useEffect(() => {
        competitorsApi.list().then(res => {
            setCompetitors(res.data)
            if (res.data.length) setSelectedCompetitor(res.data[0].id)
        }).catch(() => { })
    }, [])

    useEffect(() => {
        if (!selectedCompetitor) return
        setLoading(true)
        productsApi.get(selectedCompetitor).then(res => setProducts(res.data)).catch(() => {
            setProducts([
                { id: '1', name: 'Enterprise Suite', url: '/products/enterprise', category: 'Software', image_url: null, is_available: true, is_new: true, first_seen: new Date().toISOString() },
                { id: '2', name: 'Pro Analytics', url: '/products/analytics', category: 'Software', image_url: null, is_available: true, is_new: false, first_seen: new Date(Date.now() - 86400000 * 30).toISOString() },
                { id: '3', name: 'Basic Plan', url: '/products/basic', category: 'Plans', image_url: null, is_available: false, is_new: false, first_seen: new Date(Date.now() - 86400000 * 60).toISOString() },
            ])
        }).finally(() => setLoading(false))
    }, [selectedCompetitor])

    const filteredProducts = products.filter(p => {
        if (filter === 'new') return p.is_new
        if (filter === 'unavailable') return !p.is_available
        return true
    })

    const newCount = products.filter(p => p.is_new).length
    const unavailableCount = products.filter(p => !p.is_available).length

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center gap-4">
                <div><h2 className="text-2xl font-bold text-white">Product Watcher</h2><p className="text-white/50">Monitor competitor products</p></div>
                <select value={selectedCompetitor} onChange={e => setSelectedCompetitor(e.target.value)} className="input-glass w-auto">
                    {competitors.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
            </div>

            <div className="grid grid-cols-4 gap-4">
                <div className="glass-card p-4 rounded-xl"><Package className="w-8 h-8 text-accent-purple mb-2" /><div className="text-2xl font-bold text-white">{products.length}</div><div className="text-sm text-white/50">Total Products</div></div>
                <div className="glass-card p-4 rounded-xl"><Star className="w-8 h-8 text-accent-green mb-2" /><div className="text-2xl font-bold text-accent-green">{newCount}</div><div className="text-sm text-white/50">New Products</div></div>
                <div className="glass-card p-4 rounded-xl"><Eye className="w-8 h-8 text-accent-blue mb-2" /><div className="text-2xl font-bold text-accent-blue">{products.filter(p => p.is_available).length}</div><div className="text-sm text-white/50">Available</div></div>
                <div className="glass-card p-4 rounded-xl"><ShoppingCart className="w-8 h-8 text-accent-red mb-2" /><div className="text-2xl font-bold text-accent-red">{unavailableCount}</div><div className="text-sm text-white/50">Unavailable</div></div>
            </div>

            <div className="flex gap-2">
                {(['all', 'new', 'unavailable'] as const).map(f => (
                    <button key={f} onClick={() => setFilter(f)} className={clsx("px-4 py-2 rounded-lg text-sm transition-all", filter === f ? "bg-gradient-mesh text-white" : "bg-white/5 text-white/50 hover:text-white")}>
                        {f === 'all' ? `All (${products.length})` : f === 'new' ? `New (${newCount})` : `Unavailable (${unavailableCount})`}
                    </button>
                ))}
            </div>

            {loading ? <div className="flex justify-center h-64"><RefreshCw className="w-8 h-8 text-accent-purple animate-spin" /></div> : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredProducts.map(p => (
                        <div key={p.id} className="glass-card-hover p-4 rounded-2xl">
                            <div className="h-32 bg-white/5 rounded-xl mb-4 flex items-center justify-center">
                                {p.image_url ? <img src={p.image_url} alt={p.name} className="h-full object-contain" /> : <Package className="w-12 h-12 text-white/20" />}
                            </div>
                            <div className="flex items-start justify-between mb-2">
                                <h3 className="font-semibold text-white">{p.name}</h3>
                                <div className="flex gap-1">
                                    {p.is_new && <span className="badge badge-success">New</span>}
                                    {!p.is_available && <span className="badge badge-danger">Unavailable</span>}
                                </div>
                            </div>
                            {p.category && <span className="badge bg-white/10 text-white/50 border-white/10 mb-2">{p.category}</span>}
                            <p className="text-xs text-white/40">First seen {formatDistanceToNow(new Date(p.first_seen), { addSuffix: true })}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
