# -*- coding: utf-8 -*-
"""Live streaming event types and handling."""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel
import time
import uuid


class LiveEventType(str, Enum):
    """Live streaming event types."""
    MESSAGE = "live.message"
    GIFT = "live.gift"
    SUPERCHAT = "live.superchat"
    MEMBER = "live.member"
    CONNECT = "live.connect"
    DISCONNECT = "live.disconnect"
    ERROR = "live.error"
    HEARTBEAT = "live.heartbeat"


LIVE_EVENTS = {
    "live.message": "Chat message from stream",
    "live.gift": "Gift donation event",
    "live.superchat": "Super chat event",
    "live.member": "New member event",
    "live.connect": "Connected to stream",
    "live.disconnect": "Disconnected from stream",
    "live.error": "Connection error",
    "live.heartbeat": "Heartbeat/keepalive",
}


class LiveEvent(BaseModel):
    """Live streaming event model."""
    event: str
    platform: str
    channel_id: str
    data: Dict[str, Any]
    timestamp: float = time.time()
    id: str = str(uuid.uuid4())

    class Config:
        json_encoders = {
            float: lambda v: v
        }


class LiveMessage(BaseModel):
    """Live chat message model."""
    id: str
    platform: str
    channel_id: str
    user: str
    content: str
    timestamp: float
    type: str  # "message", "gift", "superchat", "member"

    @classmethod
    def from_event(cls, event: "LiveEvent") -> "LiveMessage":
        """Create a LiveMessage from a LiveEvent."""
        return cls(
            id=event.id,
            platform=event.platform,
            channel_id=event.channel_id,
            user=event.data.get("user", "unknown"),
            content=event.data.get("content", ""),
            timestamp=event.timestamp,
            type=event.event.replace("live.", "")
        )


def create_event(
    event_type: LiveEventType,
    platform: str,
    channel_id: str,
    data: Dict[str, Any]
) -> LiveEvent:
    """Create a new live event."""
    return LiveEvent(
        event=event_type.value,
        platform=platform,
        channel_id=channel_id,
        data=data,
        timestamp=time.time(),
        id=str(uuid.uuid4())
    )
