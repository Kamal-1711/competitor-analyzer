import { useEffect, useRef, useState, useCallback } from 'react'

type MessageHandler = (data: any) => void

interface WebSocketMessage {
    type: string
    data: any
}

export function useWebSocket(channel: string = 'default') {
    const ws = useRef<WebSocket | null>(null)
    const [isConnected, setIsConnected] = useState(false)
    const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
    const handlers = useRef<Map<string, Set<MessageHandler>>>(new Map())
    const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)

    const connect = useCallback(() => {
        if (ws.current?.readyState === WebSocket.OPEN) return

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/${channel}`

        ws.current = new WebSocket(wsUrl)

        ws.current.onopen = () => {
            setIsConnected(true)
            console.log(`WebSocket connected to ${channel}`)

            // Clear any pending reconnect
            if (reconnectTimeout.current) {
                clearTimeout(reconnectTimeout.current)
                reconnectTimeout.current = null
            }
        }

        ws.current.onclose = () => {
            setIsConnected(false)
            console.log(`WebSocket disconnected from ${channel}`)

            // Attempt to reconnect after 5 seconds
            reconnectTimeout.current = setTimeout(() => {
                connect()
            }, 5000)
        }

        ws.current.onerror = (error) => {
            console.error('WebSocket error:', error)
        }

        ws.current.onmessage = (event) => {
            try {
                const message: WebSocketMessage = JSON.parse(event.data)
                setLastMessage(message)

                // Call registered handlers for this message type
                const typeHandlers = handlers.current.get(message.type)
                if (typeHandlers) {
                    typeHandlers.forEach(handler => handler(message.data))
                }

                // Call handlers for 'all' messages
                const allHandlers = handlers.current.get('*')
                if (allHandlers) {
                    allHandlers.forEach(handler => handler(message))
                }
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error)
            }
        }
    }, [channel])

    const disconnect = useCallback(() => {
        if (reconnectTimeout.current) {
            clearTimeout(reconnectTimeout.current)
        }
        if (ws.current) {
            ws.current.close()
        }
    }, [])

    const sendMessage = useCallback((data: any) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(data))
        }
    }, [])

    const subscribe = useCallback((messageType: string, handler: MessageHandler) => {
        if (!handlers.current.has(messageType)) {
            handlers.current.set(messageType, new Set())
        }
        handlers.current.get(messageType)!.add(handler)

        // Return unsubscribe function
        return () => {
            handlers.current.get(messageType)?.delete(handler)
        }
    }, [])

    useEffect(() => {
        connect()
        return () => disconnect()
    }, [connect, disconnect])

    return {
        isConnected,
        lastMessage,
        sendMessage,
        subscribe,
        connect,
        disconnect
    }
}

// Hook for scan progress updates
export function useScanProgress() {
    const { isConnected, subscribe } = useWebSocket('scans')
    const [scanProgress, setScanProgress] = useState<{
        scan_id: string
        progress: number
        current_url: string
        status: string
    } | null>(null)

    useEffect(() => {
        const unsubscribe = subscribe('scan_progress', (data) => {
            setScanProgress(data)
        })
        return unsubscribe
    }, [subscribe])

    return { scanProgress, isConnected }
}

// Hook for real-time alerts
export function useAlerts() {
    const { isConnected, subscribe } = useWebSocket('alerts')
    const [newAlert, setNewAlert] = useState<{
        alert_type: string
        title: string
        message: string
        severity: string
    } | null>(null)

    useEffect(() => {
        const unsubscribe = subscribe('new_alert', (data) => {
            setNewAlert(data)
        })
        return unsubscribe
    }, [subscribe])

    return { newAlert, isConnected }
}

// Hook for competitor updates
export function useCompetitorUpdates() {
    const { isConnected, subscribe } = useWebSocket('competitors')
    const [update, setUpdate] = useState<{
        competitor_id: string
        update_type: string
        [key: string]: any
    } | null>(null)

    useEffect(() => {
        const unsubscribe = subscribe('competitor_update', (data) => {
            setUpdate(data)
        })
        return unsubscribe
    }, [subscribe])

    return { update, isConnected }
}
