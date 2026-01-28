import { useState, useEffect } from 'react'
import { Bell, Search, Menu, Plus, RefreshCw, ChevronDown } from 'lucide-react'
import { api } from '../../services/api'
import { Link } from 'react-router-dom'

export default function Header() {
    const [alertCount, setAlertCount] = useState(0)

    useEffect(() => {
        const fetchAlertCount = async () => {
            try {
                const response = await api.get('/alerts/unread/count')
                setAlertCount(response.data.count)
            } catch (error) {
                console.error('Failed to fetch alert count:', error)
            }
        }

        fetchAlertCount()
        const interval = setInterval(fetchAlertCount, 30000)

        return () => clearInterval(interval)
    }, [])

    return (
        <header className="sticky top-0 z-40 bg-transparent mb-6">
            <div className="flex h-16 items-center justify-between gap-6">
                {/* Mobile menu button */}
                <button className="lg:hidden p-2 rounded-xl hover:bg-white/10 text-white transition-colors">
                    <Menu className="h-6 w-6" />
                </button>

                {/* Project Selector (Dropdown) */}
                <div className="hidden md:flex items-center">
                    <button className="flex items-center gap-2 px-4 py-2 rounded-xl glass-card hover:bg-white/10 transition-all duration-300">
                        <span className="font-semibold text-white">My Competitive Analysis</span>
                        <ChevronDown className="w-4 h-4 text-gray-400" />
                    </button>
                </div>

                {/* Search */}
                <div className="flex-1 max-w-xl">
                    <div className="relative group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 group-focus-within:text-accent-blue transition-colors" />
                        <input
                            type="text"
                            placeholder="Search competitors, content..."
                            className="input-glass pl-11"
                        />
                    </div>
                </div>

                {/* Right Actions */}
                <div className="flex items-center gap-3">
                    {/* Run Scan Button */}
                    <button className="hidden md:flex items-center gap-2 btn-secondary hover:shadow-glow-blue border-transparent">
                        <RefreshCw className="w-4 h-4 text-accent-blue" />
                        <span className="text-white">Run Scan</span>
                    </button>

                    {/* Add Competitor Button */}
                    <Link
                        to="/competitors"
                        className="hidden md:flex items-center gap-2 btn-primary shadow-glow-purple"
                    >
                        <Plus className="w-4 h-4" />
                        Add Competitor
                    </Link>

                    <div className="w-px h-8 bg-white/10 mx-2 hidden md:block" />

                    {/* Notifications */}
                    <button className="relative p-2.5 rounded-xl hover:bg-white/10 text-gray-400 hover:text-white transition-all duration-300">
                        <Bell className="h-5 w-5" />
                        {alertCount > 0 && (
                            <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-accent-red shadow-glow-red" />
                        )}
                    </button>

                    {/* User Profile */}
                    <div className="flex items-center justify-center w-9 h-9 rounded-full bg-gradient-mesh p-[1px] cursor-pointer hover:shadow-glow-purple transition-shadow">
                        <div className="w-full h-full rounded-full bg-dark-800 flex items-center justify-center text-xs font-semibold text-white">
                            TE
                        </div>
                    </div>
                </div>
            </div>
        </header>
    )
}
