# -*- coding: utf-8 -*-
"""YouTube live streaming platform implementation."""

import asyncio
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from googleapiclient.discovery import build

from py.live.platforms.base import BasePlatform, ConnectionStatus
from py.live.events import create_event, LiveEventType


class YouTubePlatform(BasePlatform):
    """YouTube live streaming platform using YouTube Data API v3."""

    def __init__(self, channel_id: str, api_key: str, poll_interval: int = 5, **kwargs):
        super().__init__(channel_id)
        self.api_key = api_key
        self.poll_interval = poll_interval

        self._yt = build("youtube", "v3", developerKey=api_key)
        self._chat_id: Optional[str] = None
        self._page_token: Optional[str] = None
        self._stop_evt = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def platform_name(self) -> str:
        return "youtube"

    async def connect(self, **kwargs) -> bool:
        """Connect to YouTube live stream."""
        try:
            async with self._lock:
                if self._status == ConnectionStatus.CONNECTED:
                    return True

                self._status = ConnectionStatus.CONNECTING
                self._error = None

            # Get live chat ID
            self._chat_id = self._get_live_chat_id()
            if not self._chat_id:
                self._error = "Stream is not live or has no chat"
                self._status = ConnectionStatus.ERROR
                return False

            # Start polling thread
            self._stop_evt.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

            self._status = ConnectionStatus.CONNECTED
            self._started_at = self._started_at or time.time()
            self._room_name = self.channel_id
            return True

        except Exception as e:
            self._error = str(e)
            self._status = ConnectionStatus.ERROR
            return False

    def _get_live_chat_id(self) -> Optional[str]:
        """Get the live chat ID for the video."""
        try:
            rsp = self._yt.videos().list(
                id=self.channel_id,
                part="liveStreamingDetails"
            ).execute()
            if not rsp["items"]:
                return None
            details = rsp["items"][0].get("liveStreamingDetails", {})
            return details.get("activeLiveChatId")
        except Exception as e:
            self._error = f"Failed to get live chat ID: {e}"
            return None

    def _run(self):
        """Polling loop running in background thread."""
        while not self._stop_evt.is_set():
            try:
                self._poll_once()
            except Exception as e:
                self._error = f"Poll error: {e}"
            time.sleep(self.poll_interval)

    def _poll_once(self):
        """Poll for new messages once."""
        if not self._chat_id:
            return

        try:
            rsp = self._yt.liveChatMessages().list(
                liveChatId=self._chat_id,
                part="snippet,authorDetails",
                pageToken=self._page_token,
                maxResults=2000
            ).execute()

            for item in rsp["items"]:
                author = item["authorDetails"]["displayName"]
                text = item["snippet"]["displayMessage"]
                msg_id = item["id"]

                data = {
                    "id": msg_id,
                    "user": author,
                    "content": f"{author}: {text}",
                    "type": "message",
                    "raw": {
                        "author": author,
                        "message": text,
                        "msg_id": msg_id,
                    }
                }

                event = create_event(
                    LiveEventType.MESSAGE,
                    "youtube",
                    self.channel_id,
                    data
                )

                self.add_message(event.model_dump())
                self._dispatch_event(event)

            self._page_token = rsp.get("nextPageToken")

        except Exception as e:
            self._error = f"Failed to poll messages: {e}"

    def _dispatch_event(self, event):
        """Dispatch event to listeners."""
        try:
            loop = self._loop or asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._notify_listeners(event),
                    loop
                )
        except Exception:
            pass

    async def _notify_listeners(self, event):
        """Notify WebSocket listeners of an event."""
        from py.live.router import live_router
        await live_router.broadcast_event(event)

    async def disconnect(self) -> bool:
        """Disconnect from YouTube stream."""
        try:
            async with self._lock:
                if self._status == ConnectionStatus.DISCONNECTED:
                    return True

                self._stop_evt.set()

                if self._thread and self._thread.is_alive():
                    self._thread.join(timeout=self.poll_interval + 1)

                self._status = ConnectionStatus.DISCONNECTED
                self._started_at = None
                self._chat_id = None
                self._page_token = None
                return True

        except Exception as e:
            self._error = str(e)
            return False

    async def is_connected(self) -> bool:
        """Check if connected to YouTube stream."""
        return self._status == ConnectionStatus.CONNECTED
