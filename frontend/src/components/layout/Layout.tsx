import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'

export default function Layout() {
    return (
        <div className="min-h-screen bg-transparent">
            <Sidebar />
            <div className="lg:pl-64 min-h-screen transition-all duration-300">
                <Header />
                <main className="p-6">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}
