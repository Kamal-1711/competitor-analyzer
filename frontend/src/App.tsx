import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Competitors from './pages/Competitors'
import SeoAnalyzer from './pages/SeoAnalyzer'
import ContentTracker from './pages/ContentTracker'
import PriceMonitor from './pages/PriceMonitor'
import ProductWatcher from './pages/ProductWatcher'
import GapFinder from './pages/GapFinder'
import Alerts from './pages/Alerts'

function App() {
    return (
        <Routes>
            <Route path="/" element={<Layout />}>
                <Route index element={<Dashboard />} />
                <Route path="competitors" element={<Competitors />} />
                <Route path="seo" element={<SeoAnalyzer />} />
                <Route path="content" element={<ContentTracker />} />
                <Route path="prices" element={<PriceMonitor />} />
                <Route path="products" element={<ProductWatcher />} />
                <Route path="gaps" element={<GapFinder />} />
                <Route path="alerts" element={<Alerts />} />
            </Route>
        </Routes>
    )
}

export default App
