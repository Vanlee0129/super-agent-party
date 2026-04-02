# -*- coding: utf-8 -*-
"""Twitch live streaming platform implementation."""

import asyncio
import socket
import ssl
import time
from typing import Any, Callable, Dict, List, Optional

from py.live.platforms.base import BasePlatform, ConnectionStatus
from py.live.events import create_event, LiveEventType


class TwitchChatClient:
    """Twitch IRC chat client for receiving messages."""

    def __init__(self, access_token: str, channel: str, on_message: Callable):
        self.access_token = access_token.replace("oauth:", "")
        self.channel = channel.lower().lstrip("#")
        self.on_message = on_message
        self._sock: Optional[socket.socket] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the Twitch chat client."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._listen_loop())

    async def stop(self):
        """Stop the Twitch chat client."""
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._close_socket()

    async def _listen_loop(self):
        """Main listening loop with reconnection logic."""
        reconnect_delay = 5
        while self._running:
            try:
                await self._connect_and_read()
                reconnect_delay = 5
            except Exception as exc:
                if not self._running:
                    break
                self._dispatch_error(f"Connection error: {exc}")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, 60)

    async def _connect_and_read(self):
        """Connect to Twitch IRC and read messages."""
        ctx = ssl.create_default_context()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        self._sock = ctx.wrap_socket(sock, server_hostname="irc.chat.twitch.tv")
        self._sock.connect(("irc.chat.twitch.tv", 6697))
        self._sock.settimeout(None)

        # Authenticate
        self._send(f"CAP REQ :twitch.tv/tags twitch.tv/commands")
        self._send(f"PASS oauth:{self.access_token}")
        self._send(f"NICK justinfan12345")
        self._send(f"JOIN #{self.channel}")

        buffer = ""
        while self._running:
            data = await asyncio.get_event_loop().sock_recv(self._sock, 4096)
            if not data:
                raise ConnectionAbortedError("Server closed connection")
            buffer += data.decode("utf-8", errors="ignore")
            while "\r\n" in buffer:
                line, buffer = buffer.split("\r\n", 1)
                if line:
                    self._handle_line(line)

    def _handle_line(self, line: str):
        """Handle an incoming IRC line."""
        if line.startswith("PING"):
            self._send("PONG " + line[4:])
            return
        if "PRIVMSG" not in line:
            return

        # Parse tags
        tags = {}
        if line.startswith("@"):
            tag_str, _, line = line[1:].partition(" ")
            for kv in tag_str.split(";"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    tags[k] = v

        # Get username
        user = (
            tags.get("display-name") or
            tags.get("user-id") or
            line.split("!", 1)[0]
        ).strip()

        # Get channel
        try:
            _, _, rest = line.partition("PRIVMSG #")
            channel = rest.split(" ", 1)[0].lower().lstrip("#")
        except Exception:
            return

        # Get message
        try:
            msg = line.split(" :", maxsplit=1)[1]
        except Exception:
            return

        # Dispatch
        data = {
            "id": str(hash((channel, user, msg, time.time()))),
            "user": user,
            "content": f"{user}: {msg}",
            "type": "message",
            "raw": {
                "channel": channel,
                "user": user,
                "message": msg,
                "tags": tags,
            }
        }

        event = create_event(
            LiveEventType.MESSAGE,
            "twitch",
            channel,
            data
        )

        self.on_message(event)

    def _send(self, msg: str):
        """Send a message to Twitch IRC."""
        if self._sock:
            self._sock.send(f"{msg}\r\n".encode())

    def _close_socket(self):
        """Close the socket."""
        if self._sock:
            try:
                self._sock.close()
            except:
                pass
            self._sock = None

    def _dispatch_error(self, error: str):
        """Dispatch an error event."""
        event = create_event(
            LiveEventType.ERROR,
            "twitch",
            self.channel,
            {"error": error}
        )
        self.on_message(event)


class TwitchPlatform(BasePlatform):
    """Twitch live streaming platform."""

    def __init__(self, channel_id: str, access_token: str = "", **kwargs):
        super().__init__(channel_id)
        self.access_token = access_token

        self._client: Optional[TwitchChatClient] = None

    @property
    def platform_name(self) -> str:
        return "twitch"

    async def connect(self, **kwargs) -> bool:
        """Connect to Twitch stream."""
        try:
            async with self._lock:
                if self._status == ConnectionStatus.CONNECTED:
                    return True

                self._status = ConnectionStatus.CONNECTING
                self._error = None

            if not self.access_token:
                self._error = "Twitch access token is required"
                self._status = ConnectionStatus.ERROR
                return False

            async def on_message(event):
                self.add_message(event.model_dump())
                await self._notify_listeners(event)

            self._client = TwitchChatClient(
                access_token=self.access_token,
                channel=self.channel_id,
                on_message=on_message
            )

            await self._client.start()

            self._status = ConnectionStatus.CONNECTED
            self._started_at = self._started_at or time.time()
            self._room_name = self.channel_id
            return True

        except Exception as e:
            self._error = str(e)
            self._status = ConnectionStatus.ERROR
            return False

    async def disconnect(self) -> bool:
        """Disconnect from Twitch stream."""
        try:
            async with self._lock:
                if self._status == ConnectionStatus.DISCONNECTED:
                    return True

                if self._client:
                    await self._client.stop()
                    self._client = None

                self._status = ConnectionStatus.DISCONNECTED
                self._started_at = None
                return True

        except Exception as e:
            self._error = str(e)
            return False

    async def is_connected(self) -> bool:
        """Check if connected to Twitch stream."""
        return self._status == ConnectionStatus.CONNECTED

    async def _notify_listeners(self, event):
        """Notify WebSocket listeners of an event."""
        from py.live.router import live_router
        await live_router.broadcast_event(event)
