import { NavLink } from 'react-router-dom'
import {
    LayoutDashboard,
    Users,
    Search,
    FileText,
    DollarSign,
    Package,
    Target,
    Bell,
    FileBarChart,
    Settings,
    ChevronLeft
} from 'lucide-react'

const navigation = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Competitors', href: '/competitors', icon: Users },
    { name: 'Price Monitor', href: '/prices', icon: DollarSign },
    { name: 'Content Tracker', href: '/content', icon: FileText },
    { name: 'SEO Analyzer', href: '/seo', icon: Search },
    { name: 'Product Watcher', href: '/products', icon: Package },
    { name: 'Gap Finder', href: '/gaps', icon: Target },
    { name: 'Alerts', href: '/alerts', icon: Bell, badge: true },
    { name: 'Reports', href: '/reports', icon: FileBarChart },
]

export default function Sidebar() {
    return (
        <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col glass-card rounded-l-none border-y-0 border-l-0 border-r border-glass-border">
            <div className="flex grow flex-col gap-y-5 overflow-y-auto px-6 pb-4">
                {/* Logo */}
                <div className="flex h-16 shrink-0 items-center justify-between mt-2">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-mesh flex items-center justify-center shadow-glow-purple">
                            <span className="text-white font-bold text-lg">W</span>
                        </div>
                        <span className="text-xl font-bold text-white tracking-tight">Web Spy</span>
                    </div>
                    <button className="text-gray-400 hover:text-white transition-colors">
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex flex-1 flex-col">
                    <ul role="list" className="flex flex-1 flex-col gap-y-1">
                        {navigation.map((item) => (
                            <li key={item.name}>
                                <NavLink
                                    to={item.href}
                                    className={({ isActive }) =>
                                        `group flex items-center gap-x-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-300 ${isActive
                                            ? 'bg-white/10 text-white shadow-lg shadow-purple-500/10 border border-white/10'
                                            : 'text-gray-400 hover:bg-white/5 hover:text-white'
                                        }`
                                    }
                                >
                                    {({ isActive }) => (
                                        <>
                                            <item.icon
                                                className={`h-5 w-5 shrink-0 transition-colors ${isActive ? 'text-accent-purple' : 'text-gray-500 group-hover:text-white'}`}
                                            />
                                            {item.name}
                                            {item.badge && (
                                                <span className="ml-auto w-2 h-2 rounded-full bg-accent-red shadow-glow-red" />
                                            )}
                                        </>
                                    )}
                                </NavLink>
                            </li>
                        ))}
                    </ul>
                </nav>

                {/* Footer */}
                <div className="mt-auto">
                    <NavLink
                        to="/settings"
                        className={({ isActive }) =>
                            `group flex items-center gap-x-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-300 ${isActive
                                ? 'bg-white/10 text-white shadow-lg'
                                : 'text-gray-400 hover:bg-white/5 hover:text-white'
                            }`
                        }
                    >
                        <Settings className="h-5 w-5 shrink-0" />
                        Settings
                    </NavLink>
                </div>
            </div>
        </div>
    )
}
