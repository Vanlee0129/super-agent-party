# -*- coding: utf-8 -*-
"""Base platform interface for live streaming connections."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel
import asyncio
import threading
import time


class ConnectionStatus(str, Enum):
    """Connection status enum."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class StreamConnection(BaseModel):
    """Stream connection model."""
    platform: str
    channel_id: str
    status: ConnectionStatus
    room_name: Optional[str] = None
    viewer_count: int = 0
    started_at: Optional[float] = None
    error: Optional[str] = None


class BasePlatform(ABC):
    """Abstract base class for live streaming platforms."""

    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        self._status = ConnectionStatus.DISCONNECTED
        self._room_name: Optional[str] = None
        self._viewer_count = 0
        self._started_at: Optional[float] = None
        self._error: Optional[str] = None
        self._lock = asyncio.Lock()
        self._message_history: List[Dict[str, Any]] = []
        self._max_history = 1000

    @property
    def status(self) -> ConnectionStatus:
        return self._status

    @property
    def room_name(self) -> Optional[str]:
        return self._room_name

    @property
    def viewer_count(self) -> int:
        return self._viewer_count

    @property
    def started_at(self) -> Optional[float]:
        return self._started_at

    @property
    def error(self) -> Optional[str]:
        return self._error

    def get_connection_info(self) -> StreamConnection:
        """Get current connection information."""
        return StreamConnection(
            platform=self.platform_name,
            channel_id=self.channel_id,
            status=self._status,
            room_name=self._room_name,
            viewer_count=self._viewer_count,
            started_at=self._started_at,
            error=self._error
        )

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform name."""
        pass

    @abstractmethod
    async def connect(self, **kwargs) -> bool:
        """Connect to the live stream."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the live stream."""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if connected to the stream."""
        pass

    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to history."""
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)

    def get_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent messages from history."""
        return self._message_history[-limit:]

    def clear_messages(self) -> None:
        """Clear message history."""
        self._message_history.clear()
