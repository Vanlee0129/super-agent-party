# -*- coding: utf-8 -*-
"""Live streaming router - manages connections across all platforms."""

import asyncio
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from fastapi import WebSocket

from py.live.platforms.base import BasePlatform, ConnectionStatus, StreamConnection
from py.live.platforms.bilibili import BilibiliPlatform
from py.live.platforms.youtube import YouTubePlatform
from py.live.platforms.twitch import TwitchPlatform
from py.live.events import LiveEvent, LiveMessage, create_event, LiveEventType


class ConnectionManager:
    """Manages WebSocket connections for live streaming events."""

    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._connections[client_id] = websocket

    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection."""
        if client_id in self._connections:
            del self._connections[client_id]

    async def send(self, client_id: str, message: Dict[str, Any]) -> None:
        """Send a message to a specific client."""
        if client_id in self._connections:
            await self._connections[client_id].send_json(message)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        async with self._lock:
            disconnected = []
            for client_id, websocket in self._connections.items():
                try:
                    await websocket.send_json(message)
                except Exception:
                    disconnected.append(client_id)
            
            for client_id in disconnected:
                del self._connections[client_id]


class LiveRouter:
    """Main router for managing live streaming connections across platforms."""

    def __init__(self):
        self._connections: Dict[str, Dict[str, BasePlatform]] = {}  # platform -> channel_id -> platform
        self._ws_manager = ConnectionManager()
        self._lock = asyncio.Lock()

    def _get_key(self, platform: str, channel_id: str) -> str:
        """Get a unique key for a platform/channel combination."""
        return f"{platform}:{channel_id}"

    async def connect_stream(
        self,
        platform: str,
        channel_id: str,
        **kwargs
    ) -> StreamConnection:
        """Connect to a live stream."""
        key = self._get_key(platform, channel_id)

        async with self._lock:
            # Check if already connected
            if platform in self._connections:
                existing = self._connections[platform].get(channel_id)
                if existing and await existing.is_connected():
                    return existing.get_connection_info()

            # Create new platform connection
            if platform == "bilibili":
                conn = BilibiliPlatform(channel_id, **kwargs)
            elif platform == "youtube":
                conn = YouTubePlatform(channel_id, **kwargs)
            elif platform == "twitch":
                conn = TwitchPlatform(channel_id, **kwargs)
            else:
                raise ValueError(f"Unsupported platform: {platform}")

            if platform not in self._connections:
                self._connections[platform] = {}

            self._connections[platform][channel_id] = conn

        # Connect (outside the lock to avoid deadlock)
        success = await conn.connect(**kwargs)
        if not success:
            raise RuntimeError(f"Failed to connect to {platform} stream {channel_id}: {conn.error}")

        # Send connect event
        await self.broadcast_event(create_event(
            LiveEventType.CONNECT,
            platform,
            channel_id,
            {"status": "connected"}
        ))

        return conn.get_connection_info()

    async def disconnect_stream(self, platform: str, channel_id: str) -> bool:
        """Disconnect from a live stream."""
        key = self._get_key(platform, channel_id)

        async with self._lock:
            if platform not in self._connections:
                return True

            conn = self._connections[platform].get(channel_id)
            if not conn:
                return True

            await conn.disconnect()
            del self._connections[platform][channel_id]

        # Send disconnect event
        await self.broadcast_event(create_event(
            LiveEventType.DISCONNECT,
            platform,
            channel_id,
            {"status": "disconnected"}
        ))

        return True

    async def get_status(self, platform: str, channel_id: str) -> Optional[StreamConnection]:
        """Get connection status for a stream."""
        async with self._lock:
            if platform not in self._connections:
                return None
            conn = self._connections[platform].get(channel_id)
            if not conn:
                return None
            return conn.get_connection_info()

    async def list_connections(self) -> List[StreamConnection]:
        """List all active stream connections."""
        result = []
        async with self._lock:
            for platform, channels in self._connections.items():
                for channel_id, conn in channels.items():
                    if conn.status == ConnectionStatus.CONNECTED:
                        result.append(conn.get_connection_info())
        return result

    async def get_messages(
        self,
        platform: str,
        channel_id: str,
        limit: int = 100
    ) -> List[LiveMessage]:
        """Get recent messages from a stream."""
        async with self._lock:
            if platform not in self._connections:
                return []
            conn = self._connections[platform].get(channel_id)
            if not conn:
                return []
            messages = conn.get_messages(limit)
            return [LiveMessage.from_event(LiveEvent(**msg)) for msg in messages]

    async def broadcast_event(self, event: LiveEvent) -> None:
        """Broadcast an event to all WebSocket listeners."""
        await self._ws_manager.broadcast(event.model_dump())

    async def handle_websocket(self, websocket: WebSocket, platform: str, channel_id: str) -> None:
        """Handle a WebSocket connection for a specific stream."""
        client_id = str(uuid.uuid4())
        await self._ws_manager.connect(client_id, websocket)

        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
                # Handle other client messages if needed
        except Exception:
            pass
        finally:
            self._ws_manager.disconnect(client_id)


# Global singleton instance
live_router = LiveRouter()
