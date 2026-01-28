import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'

export default function Layout() {
    const [sidebarOpen, setSidebarOpen] = useState(true)

    return (
        <div className="min-h-screen bg-transparent">
            {/* Mobile backdrop */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 z-40 bg-dark-900/60 backdrop-blur-sm lg:hidden transition-opacity duration-300"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar with state controls */}
            <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />

            <div className={`transition-all duration-300 min-h-screen ${sidebarOpen ? 'lg:pl-64' : 'pl-0'}`}>
                <Header setSidebarOpen={setSidebarOpen} sidebarOpen={sidebarOpen} />
                <main className="p-6">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}
