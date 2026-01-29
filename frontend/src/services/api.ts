import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
    baseURL: `${API_URL}/api`,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor
api.interceptors.request.use(
    (config) => {
        // Add auth token if available
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response interceptor
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Handle unauthorized
            localStorage.removeItem('token')
        }
        return Promise.reject(error)
    }
)

// API functions
export const dashboardApi = {
    getMetrics: () => api.get('/dashboard/metrics'),
    getActivity: (limit = 10) => api.get(`/dashboard/activity?limit=${limit}`),
    getHealthScore: () => api.get('/dashboard/health-score'),
    getScanProgress: () => api.get('/dashboard/scan-progress'),
}

export const competitorsApi = {
    list: (params?: { skip?: number; limit?: number; type?: string }) =>
        api.get('/competitors', { params }),
    get: (id: string) => api.get(`/competitors/${id}`),
    create: (data: { name: string; url: string; competitor_type?: string }) =>
        api.post('/competitors', data),
    update: (id: string, data: Partial<{ name: string; is_monitoring: boolean }>) =>
        api.put(`/competitors/${id}`, data),
    delete: (id: string) => api.delete(`/competitors/${id}`),
    triggerScan: (id: string) => api.post(`/competitors/${id}/scan`),
    getScans: (id: string) => api.get(`/competitors/${id}/scans`),
}

export const seoApi = {
    get: (competitorId: string) => api.get(`/seo/${competitorId}`),
    getHistory: (competitorId: string) => api.get(`/seo/${competitorId}/history`),
    getAudit: (competitorId: string) => api.get(`/seo/${competitorId}/audit`),
    compare: (ids: string[]) => api.get(`/seo/compare?competitor_ids=${ids.join(',')}`),
    analyze: (competitorId: string) => api.post(`/seo/${competitorId}/analyze`),
}

export const contentApi = {
    get: (competitorId: string) => api.get(`/content/${competitorId}`),
    getChanges: (competitorId: string) => api.get(`/content/${competitorId}/changes`),
    getDiff: (contentId: string) => api.get(`/content/diff/${contentId}`),
    getStats: (competitorId: string) => api.get(`/content/stats/${competitorId}`),
}

export const pricesApi = {
    get: (competitorId: string) => api.get(`/prices/${competitorId}`),
    scan: (competitorId: string) => api.post(`/prices/${competitorId}/scan`),
    getHistory: (competitorId: string, productName: string, days = 30) =>
        api.get(`/prices/${competitorId}/history?product_name=${productName}&days=${days}`),
    compare: (productName: string, ids?: string[]) =>
        api.get(`/prices/compare?product_name=${productName}${ids ? `&competitor_ids=${ids.join(',')}` : ''}`),
    getAlerts: () => api.get('/prices/alerts/recent'),
    getDeals: () => api.get('/prices/deals'),
}

export const productsApi = {
    get: (competitorId: string) => api.get(`/products/${competitorId}`),
    getNew: (days = 7) => api.get(`/products/new?days=${days}`),
    compareFeatures: (names: string[], ids?: string[]) =>
        api.get(`/products/compare/features?product_names=${names.join(',')}${ids ? `&competitor_ids=${ids.join(',')}` : ''}`),
    getCategories: () => api.get('/products/categories'),
}

export const gapsApi = {
    getSummary: () => api.get('/gaps/summary'),
    getFeatures: () => api.get('/gaps/features'),
    getContent: () => api.get('/gaps/content'),
    getKeywords: () => api.get('/gaps/keywords'),
    getPositioning: () => api.get('/gaps/positioning'),
}

export const alertsApi = {
    list: (params?: { is_read?: boolean; severity?: string; limit?: number }) =>
        api.get('/alerts', { params }),
    getStats: () => api.get('/alerts/stats'),
    getUnreadCount: () => api.get('/alerts/unread/count'),
    markAsRead: (id: string) => api.put(`/alerts/${id}/read`),
    markAllAsRead: () => api.put('/alerts/read-all'),
    dismiss: (id: string) => api.delete(`/alerts/${id}`),
    getRecent: (limit = 5) => api.get(`/alerts/recent?limit=${limit}`),
}

export const crawlApi = {
    list: (params?: { competitor_id?: string; status?: string }) =>
        api.get('/crawl', { params }),
    get: (scanId: string) => api.get(`/crawl/${scanId}`),
    create: (data: { competitor_id: string; scan_type?: 'full' | 'quick'; max_pages?: number }) =>
        api.post('/crawl', data),
    cancel: (scanId: string) => api.delete(`/crawl/${scanId}`),
    retry: (scanId: string) => api.post(`/crawl/${scanId}/retry`),
    getPages: (scanId: string, params?: { skip?: number; limit?: number }) =>
        api.get(`/crawl/${scanId}/pages`, { params }),
    getStats: () => api.get('/crawl/stats'),
    getRunning: () => api.get('/crawl/running'),
    quickScan: (url: string) => api.post('/crawl/quick', { url }),
}

// Enhanced SEO API
export const seoApiEnhanced = {
    ...seoApi,
    getReport: (competitorId: string) => api.get(`/seo/${competitorId}/report`),
    getTrends: (competitorId: string, days = 30) =>
        api.get(`/seo/${competitorId}/trends?days=${days}`),
    compareDetailed: (competitorIds: string[], yourCompetitorId?: string) =>
        api.post('/seo/compare/detailed', { competitor_ids: competitorIds, your_competitor_id: yourCompetitorId }),
    quickAnalyze: (url: string) => api.post(`/seo/analyze/quick?url=${encodeURIComponent(url)}`),
}

// Type definitions
export interface Competitor {
    id: string
    name: string
    url: string
    domain: string
    logo_url?: string
    favicon_url?: string
    competitor_type: 'direct' | 'indirect'
    health_score: number
    seo_score: number
    content_score: number
    is_monitoring: boolean
    last_scanned?: string
    created_at: string
}

export interface Scan {
    id: string
    competitor_id: string
    status: 'pending' | 'running' | 'completed' | 'failed'
    progress: number
    pages_crawled: number
    pages_discovered: number
    current_url?: string
    error_message?: string
    started_at?: string
    completed_at?: string
    created_at: string
}

export interface Alert {
    id: string
    competitor_id?: string
    alert_type: string
    severity: 'low' | 'medium' | 'high' | 'critical'
    title: string
    message: string
    related_url?: string
    is_read: boolean
    is_dismissed: boolean
    created_at: string
}

export interface SeoAnalysis {
    id: string
    competitor_id: string
    url: string
    overall_score: number
    title?: string
    title_score: number
    meta_description_score: number
    headers_score: number
    content_score: number
    technical_score: number
    images_score: number
    links_score: number
    analyzed_at: string
}
