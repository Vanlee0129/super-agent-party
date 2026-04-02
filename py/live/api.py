# -*- coding: utf-8 -*-
"""FastAPI routes for live streaming API."""

from enum import Enum
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from py.live.router import live_router
from py.live.events import LiveMessage


class Platform(str, Enum):
    """Supported streaming platforms."""
    BILIBILI = "bilibili"
    YOUTUBE = "youtube"
    TWITCH = "twitch"


class ConnectionStatus(str, Enum):
    """Connection status for streams."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class StreamConnection(BaseModel):
    """Model representing a stream connection."""
    platform: Platform
    channel_id: str
    status: ConnectionStatus
    room_name: Optional[str] = None
    viewer_count: int = 0
    started_at: Optional[float] = None
    error: Optional[str] = None


class ConnectRequest(BaseModel):
    """Request model for connecting to a stream."""
    platform: Platform
    channel_id: str
    # Bilibili options
    bilibili_type: Optional[str] = "web"
    sessdata: Optional[str] = ""
    access_key_id: Optional[str] = ""
    access_key_secret: Optional[str] = ""
    app_id: Optional[str] = ""
    room_owner_auth_code: Optional[str] = ""
    # YouTube options
    api_key: Optional[str] = ""
    poll_interval: Optional[int] = 5
    # Twitch options
    access_token: Optional[str] = ""


class DisconnectRequest(BaseModel):
    """Request model for disconnecting from a stream."""
    platform: Platform
    channel_id: str


class ApiResponse(BaseModel):
    """Generic API response."""
    success: bool
    message: str


router = APIRouter(prefix="/api/v1/live", tags=["live"])


@router.get("/connections", response_model=List[StreamConnection])
async def list_connections() -> List[StreamConnection]:
    """List all active stream connections."""
    return await live_router.list_connections()


@router.post("/connect", response_model=StreamConnection)
async def connect_stream(request: ConnectRequest) -> StreamConnection:
    """Connect to a live stream.
    
    Connect to a live streaming platform and start receiving events.
    """
    try:
        kwargs: Dict[str, Any] = {}
        
        if request.platform == Platform.BILIBILI:
            kwargs["live_type"] = request.bilibili_type or "web"
            kwargs["sessdata"] = request.sessdata or ""
            kwargs["access_key_id"] = request.access_key_id or ""
            kwargs["access_key_secret"] = request.access_key_secret or ""
            kwargs["app_id"] = request.app_id or ""
            kwargs["room_owner_auth_code"] = request.room_owner_auth_code or ""
        
        elif request.platform == Platform.YOUTUBE:
            kwargs["api_key"] = request.api_key or ""
            kwargs["poll_interval"] = request.poll_interval or 5
        
        elif request.platform == Platform.TWITCH:
            kwargs["access_token"] = request.access_token or ""
        
        return await live_router.connect_stream(
            platform=request.platform.value,
            channel_id=request.channel_id,
            **kwargs
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/disconnect", response_model=ApiResponse)
async def disconnect_stream(request: DisconnectRequest):
    """Disconnect from a live stream."""
    try:
        await live_router.disconnect_stream(
            platform=request.platform.value,
            channel_id=request.channel_id
        )
        return ApiResponse(success=True, message="Disconnected successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{platform}/{channel_id}", response_model=StreamConnection)
async def get_status(platform: Platform, channel_id: str) -> StreamConnection:
    """Get connection status for a specific stream."""
    status = await live_router.get_status(platform.value, channel_id)
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"No connection found for {platform.value} channel {channel_id}"
        )
    return StreamConnection(
        platform=Platform(status.platform),
        channel_id=status.channel_id,
        status=ConnectionStatus(status.status.value),
        room_name=status.room_name,
        viewer_count=status.viewer_count,
        started_at=status.started_at,
        error=status.error
    )


@router.get("/messages/{platform}/{channel_id}", response_model=List[LiveMessage])
async def get_messages(
    platform: Platform,
    channel_id: str,
    limit: int = 100
) -> List[LiveMessage]:
    """Get recent messages from a stream."""
    return await live_router.get_messages(platform.value, channel_id, limit)


@router.websocket("/ws/{platform}/{channel_id}")
async def live_websocket(websocket: WebSocket, platform: str, channel_id: str):
    """WebSocket endpoint for real-time live stream events.
    
    Connect to receive live events from a specific stream.
    Send "ping" to keep the connection alive (responds with "pong").
    """
    await live_router.handle_websocket(websocket, platform, channel_id)
