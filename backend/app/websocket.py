from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json
from uuid import UUID
from loguru import logger


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, channel: str = "default"):
        """Accept a WebSocket connection and add it to a channel."""
        await websocket.accept()
        
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        
        self.active_connections[channel].add(websocket)
        logger.info(f"WebSocket connected to channel: {channel}")
    
    def disconnect(self, websocket: WebSocket, channel: str = "default"):
        """Remove a WebSocket connection from a channel."""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            
            if not self.active_connections[channel]:
                del self.active_connections[channel]
        
        logger.info(f"WebSocket disconnected from channel: {channel}")
    
    async def broadcast(self, message: dict, channel: str = "default"):
        """Broadcast a message to all connections in a channel."""
        if channel not in self.active_connections:
            return
        
        disconnected = set()
        
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections[channel].discard(conn)
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
    
    async def broadcast_scan_progress(
        self,
        scan_id: UUID,
        progress: int,
        current_url: str,
        status: str = "running"
    ):
        """Broadcast scan progress update."""
        await self.broadcast({
            "type": "scan_progress",
            "data": {
                "scan_id": str(scan_id),
                "progress": progress,
                "current_url": current_url,
                "status": status
            }
        }, channel="scans")
    
    async def broadcast_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        severity: str = "medium"
    ):
        """Broadcast a new alert."""
        await self.broadcast({
            "type": "new_alert",
            "data": {
                "alert_type": alert_type,
                "title": title,
                "message": message,
                "severity": severity
            }
        }, channel="alerts")
    
    async def broadcast_competitor_update(
        self,
        competitor_id: UUID,
        update_type: str,
        data: dict
    ):
        """Broadcast competitor update."""
        await self.broadcast({
            "type": "competitor_update",
            "data": {
                "competitor_id": str(competitor_id),
                "update_type": update_type,
                **data
            }
        }, channel="competitors")


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, channel: str = "default"):
    """WebSocket endpoint handler."""
    await manager.connect(websocket, channel)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal(websocket, {"type": "pong"})
                elif message.get("type") == "subscribe":
                    # Subscribe to additional channel
                    new_channel = message.get("channel")
                    if new_channel:
                        await manager.connect(websocket, new_channel)
                
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
