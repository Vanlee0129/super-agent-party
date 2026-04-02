# -*- coding: utf-8 -*-
"""Bilibili live streaming platform implementation."""

import asyncio
import http.cookies
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
import aiohttp

import py.blivedm as blivedm
import py.blivedm.models.web as web_models
import py.blivedm.models.open_live as open_models

from py.live.platforms.base import BasePlatform, ConnectionStatus


class BilibiliWebSocketHandler(blivedm.BaseHandler):
    """WebSocket handler for Bilibili web streams."""

    def __init__(self, platform: "BilibiliPlatform"):
        self.platform = platform
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        return self._loop

    def _on_heartbeat(self, client: blivedm.BLiveClient, message: web_models.HeartbeatMessage):
        """Handle heartbeat."""
        loop = self._get_loop()
        if loop.is_running():
            loop.create_task(self._broadcast_heartbeat())

    async def _broadcast_heartbeat(self):
        """Broadcast heartbeat to listeners."""
        from py.live.events import create_event, LiveEventType
        event = create_event(
            LiveEventType.HEARTBEAT,
            "bilibili",
            self.platform.channel_id,
            {"viewer_count": self.platform.viewer_count}
        )
        await self.platform._notify_listeners(event)

    def _on_danmaku(self, client: blivedm.BLiveClient, message: web_models.DanmakuMessage):
        """Handle danmaku (bullet comments) message."""
        msg_text = f'{message.uname}: {message.msg}'
        data = {
            "id": str(uuid.uuid4()),
            "user": message.uname,
            "content": msg_text,
            "type": "message",
            "raw": {
                "uname": message.uname,
                "msg": message.msg,
                "dm_type": message.dm_type,
            }
        }
        self._dispatch_message(data)

    def _on_gift(self, client: blivedm.BLiveClient, message: web_models.GiftMessage):
        """Handle gift message."""
        msg_text = f'{message.uname} sent {message.gift_name}x{message.num}'
        data = {
            "id": str(uuid.uuid4()),
            "user": message.uname,
            "content": msg_text,
            "type": "gift",
            "raw": {
                "uname": message.uname,
                "gift_name": message.gift_name,
                "num": message.num,
                "coin_type": message.coin_type,
                "total_coin": message.total_coin,
            }
        }
        self._dispatch_message(data)

    def _on_buy_guard(self, client: blivedm.BLiveClient, message: web_models.GuardBuyMessage):
        """Handle guard purchase message."""
        msg_text = f'{message.username} purchased guard (level {message.guard_level})'
        data = {
            "id": str(uuid.uuid4()),
            "user": message.username,
            "content": msg_text,
            "type": "member",
            "raw": {
                "username": message.username,
                "guard_level": message.guard_level,
            }
        }
        self._dispatch_message(data)

    def _on_super_chat(self, client: blivedm.BLiveClient, message: web_models.SuperChatMessage):
        """Handle super chat message."""
        msg_text = f'{message.uname} sent super chat: {message.message}'
        data = {
            "id": str(uuid.uuid4()),
            "user": message.uname,
            "content": msg_text,
            "type": "superchat",
            "raw": {
                "uname": message.uname,
                "message": message.message,
                "price": message.price,
            }
        }
        self._dispatch_message(data)

    def _on_interact_word(self, client: blivedm.BLiveClient, message: web_models.InteractWordMessage):
        """Handle interaction word (enter room, follow, etc.)."""
        if message.msg_type == 1:  # Enter room
            msg_text = f'{message.username} entered the room'
            data = {
                "id": str(uuid.uuid4()),
                "user": message.username,
                "content": msg_text,
                "type": "member",
                "raw": {
                    "username": message.username,
                    "msg_type": message.msg_type,
                }
            }
            self._dispatch_message(data)
        elif message.msg_type == 2:  # Follow
            msg_text = f'{message.username} followed'
            data = {
                "id": str(uuid.uuid4()),
                "user": message.username,
                "content": msg_text,
                "type": "member",
                "raw": {
                    "username": message.username,
                    "msg_type": message.msg_type,
                }
            }
            self._dispatch_message(data)

    def _dispatch_message(self, data: Dict[str, Any]):
        """Dispatch a message to listeners."""
        from py.live.events import create_event, LiveEventType
        
        event_type_map = {
            "message": LiveEventType.MESSAGE,
            "gift": LiveEventType.GIFT,
            "superchat": LiveEventType.SUPERCHAT,
            "member": LiveEventType.MEMBER,
        }
        event_type = event_type_map.get(data["type"], LiveEventType.MESSAGE)
        
        event = create_event(
            event_type,
            "bilibili",
            self.platform.channel_id,
            data
        )
        
        self.platform.add_message(event.model_dump())
        
        loop = self._get_loop()
        if loop.is_running():
            loop.create_task(self.platform._notify_listeners(event))


class OpenLiveWebSocketHandler(blivedm.BaseHandler):
    """WebSocket handler for Bilibili open platform streams."""

    def __init__(self, platform: "BilibiliPlatform"):
        self.platform = platform
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
        return self._loop

    def _on_heartbeat(self, client: blivedm.OpenLiveClient, message: open_models.HeartbeatMessage):
        """Handle heartbeat."""
        loop = self._get_loop()
        if loop.is_running():
            loop.create_task(self.platform._notify_listeners({
                "event": "live.heartbeat",
                "platform": "bilibili",
                "channel_id": self.platform.channel_id,
                "data": {}
            }))

    def _on_open_live_danmaku(self, client: blivedm.OpenLiveClient, message: open_models.DanmakuMessage):
        """Handle danmaku message."""
        data = {
            "id": str(uuid.uuid4()),
            "user": message.uname,
            "content": f'{message.uname}: {message.msg}',
            "type": "message",
        }
        self._dispatch_message(data)

    def _on_open_live_gift(self, client: blivedm.OpenLiveClient, message: open_models.GiftMessage):
        """Handle gift message."""
        data = {
            "id": str(uuid.uuid4()),
            "user": message.uname,
            "content": f'{message.uname} sent {message.gift_name}x{message.gift_num}',
            "type": "gift",
        }
        self._dispatch_message(data)

    def _on_open_live_buy_guard(self, client: blivedm.OpenLiveClient, message: open_models.GuardBuyMessage):
        """Handle guard purchase."""
        data = {
            "id": str(uuid.uuid4()),
            "user": message.user_info.uname if message.user_info else "unknown",
            "content": f'{message.user_info.uname if message.user_info else "User"} purchased guard (level {message.guard_level})',
            "type": "member",
        }
        self._dispatch_message(data)

    def _on_open_live_super_chat(self, client: blivedm.OpenLiveClient, message: open_models.SuperChatMessage):
        """Handle super chat."""
        data = {
            "id": str(uuid.uuid4()),
            "user": message.uname,
            "content": f'{message.uname} sent super chat: {message.message}',
            "type": "superchat",
        }
        self._dispatch_message(data)

    def _on_open_live_like(self, client: blivedm.OpenLiveClient, message: open_models.LikeMessage):
        """Handle like."""
        data = {
            "id": str(uuid.uuid4()),
            "user": message.uname,
            "content": f'{message.uname} liked',
            "type": "member",
        }
        self._dispatch_message(data)

    def _on_open_live_enter_room(self, client: blivedm.OpenLiveClient, message: open_models.RoomEnterMessage):
        """Handle room enter."""
        data = {
            "id": str(uuid.uuid4()),
            "user": message.uname,
            "content": f'{message.uname} entered the room',
            "type": "member",
        }
        self._dispatch_message(data)

    def _dispatch_message(self, data: Dict[str, Any]):
        """Dispatch a message to listeners."""
        from py.live.events import create_event, LiveEventType
        
        event_type_map = {
            "message": LiveEventType.MESSAGE,
            "gift": LiveEventType.GIFT,
            "superchat": LiveEventType.SUPERCHAT,
            "member": LiveEventType.MEMBER,
        }
        event_type = event_type_map.get(data["type"], LiveEventType.MESSAGE)
        
        event = create_event(
            event_type,
            "bilibili",
            self.platform.channel_id,
            data
        )
        
        self.platform.add_message(event.model_dump())
        
        loop = self._get_loop()
        if loop.is_running():
            loop.create_task(self.platform._notify_listeners(event))


class BilibiliPlatform(BasePlatform):
    """Bilibili live streaming platform."""

    def __init__(self, channel_id: str, live_type: str = "web", **kwargs):
        super().__init__(channel_id)
        self.live_type = live_type
        self.sessdata = kwargs.get("sessdata", "")
        self.access_key_id = kwargs.get("access_key_id", "")
        self.access_key_secret = kwargs.get("access_key_secret", "")
        self.app_id = kwargs.get("app_id", "")
        self.room_owner_auth_code = kwargs.get("room_owner_auth_code", "")
        
        self._client: Optional[blivedm.BLiveClient] = None
        self._open_client: Optional[blivedm.OpenLiveClient] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._handler: Optional[BilibiliWebSocketHandler] = None
        self._open_handler: Optional[OpenLiveWebSocketHandler] = None
        self._stop_event: Optional[asyncio.Event] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def platform_name(self) -> str:
        return "bilibili"

    async def connect(self, **kwargs) -> bool:
        """Connect to Bilibili live stream."""
        try:
            async with self._lock:
                if self._status == ConnectionStatus.CONNECTED:
                    return True

                self._status = ConnectionStatus.CONNECTING
                self._error = None

            if self.live_type == "web":
                return await self._connect_web()
            elif self.live_type == "open_live":
                return await self._connect_open_live()
            else:
                raise ValueError(f"Unsupported Bilibili live type: {self.live_type}")

        except Exception as e:
            self._error = str(e)
            self._status = ConnectionStatus.ERROR
            return False

    async def _connect_web(self) -> bool:
        """Connect using web interface."""
        room_id = int(self.channel_id)
        
        # Initialize session
        cookies = http.cookies.SimpleCookie()
        if self.sessdata:
            cookies["SESSDATA"] = self.sessdata
            cookies["SESSDATA"]["domain"] = "bilibili.com"

        self._session = aiohttp.ClientSession()
        if self.sessdata:
            self._session.cookie_jar.update_cookies(cookies)

        # Create client and handler
        self._client = blivedm.BLiveClient(room_id, session=self._session)
        self._handler = BilibiliWebSocketHandler(self)
        self._client.set_handler(self._handler)

        # Start client in background
        self._client.start()
        
        self._status = ConnectionStatus.CONNECTED
        self._started_at = self._started_at or time.time()
        self._room_name = str(room_id)
        
        return True

    async def _connect_open_live(self) -> bool:
        """Connect using open platform."""
        if not all([self.access_key_id, self.access_key_secret, self.app_id, self.room_owner_auth_code]):
            raise ValueError("Open platform configuration is incomplete")

        self._open_client = blivedm.OpenLiveClient(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            app_id=int(self.app_id),
            room_owner_auth_code=self.room_owner_auth_code,
        )
        self._open_handler = OpenLiveWebSocketHandler(self)
        self._open_client.set_handler(self._open_handler)

        self._open_client.start()
        
        self._status = ConnectionStatus.CONNECTED
        self._started_at = self._started_at or time.time()
        
        return True

    async def disconnect(self) -> bool:
        """Disconnect from Bilibili stream."""
        try:
            async with self._lock:
                if self._status == ConnectionStatus.DISCONNECTED:
                    return True

                self._status = ConnectionStatus.DISCONNECTED

                if self._client:
                    await self._client.stop_and_close()
                    self._client = None

                if self._open_client:
                    await self._open_client.stop_and_close()
                    self._open_client = None

                if self._session:
                    await self._session.close()
                    self._session = None

                self._started_at = None
                return True

        except Exception as e:
            self._error = str(e)
            return False

    async def is_connected(self) -> bool:
        """Check if connected to Bilibili stream."""
        return self._status == ConnectionStatus.CONNECTED

    async def _notify_listeners(self, event):
        """Notify WebSocket listeners of an event."""
        from py.live.router import live_router
        await live_router.broadcast_event(event)
