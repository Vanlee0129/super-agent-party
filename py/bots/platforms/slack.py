"""Slack Bot Platform Plugin.

Refactored from slack_bot_manager.py
"""

import asyncio
import logging
import re
import threading
import time
from typing import Dict, Any, List, Optional

import aiohttp
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from openai import AsyncOpenAI
from pydantic import BaseModel

from py.bots.platforms.base import BotPlatformPlugin
from py.plugins.base import PluginMetadata

logger = logging.getLogger(__name__)


class SlackBotConfig(BaseModel):
    """Slack bot configuration."""
    bot_token: str
    app_token: str
    llm_model: str = "super-model"
    memory_limit: int = 30
    separators: List[str] = ["。", "\n", "？", "！"]
    reasoning_visible: bool = True
    quick_restart: bool = True
    enable_tts: bool = False
    wakeWord: str = ""
    behaviorSettings: Optional[Dict[str, Any]] = None
    behaviorTargetChatIds: List[str] = []


class SlackBotPlugin(BotPlatformPlugin):
    """Slack bot platform implementation."""

    platform_name = "slack"

    def __init__(self) -> None:
        super().__init__()
        self.bot_thread: Optional[threading.Thread] = None
        self.socket_client: Optional[SocketModeClient] = None
        self._is_running = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._ready_complete = threading.Event()
        self.bot_user_id: Optional[str] = None
        self.memory: Dict[str, List[dict]] = {}
        self.async_tools: Dict[str, List[str]] = {}
        self.file_links: Dict[str, List[str]] = {}

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="bot.platform.slack",
            name="Slack Bot Platform",
            version="1.0.0",
            description="Slack bot platform plugin for team messaging",
        )

    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the Slack bot with configuration."""
        self._config = SlackBotConfig(**config)
        self.memory = {}
        self.async_tools = {}
        self.file_links = {}

        from py.behavior_engine import global_behavior_engine
        global_behavior_engine.register_handler("slack", self.execute_behavior_event)
        logger.info(f"Slack bot initialized with config")

    async def _start(self) -> None:
        """Start the Slack bot."""
        if self._is_running:
            return

        self._ready_complete.clear()

        self.bot_thread = threading.Thread(
            target=self._run_bot_thread,
            args=(self._config,),
            daemon=True,
            name="SlackBotThread"
        )
        self.bot_thread.start()

        if not self._ready_complete.wait(timeout=30):
            await self._stop()
            raise RuntimeError("Slack bot startup timeout")

        self._is_running = True
        logger.info("Slack bot started")

    async def _stop(self) -> None:
        """Stop the Slack bot."""
        self._is_running = False
        if self.socket_client:
            asyncio.run_coroutine_threadsafe(
                self.socket_client.close(), self.loop
            )
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        logger.info("Slack bot stopped")

    async def _reload(self, config: Dict[str, Any]) -> None:
        """Reload the bot with new configuration."""
        await self._stop()
        self._config = SlackBotConfig(**config)

    async def get_status(self) -> Dict[str, Any]:
        """Get current bot status."""
        return {
            "is_running": self._is_running,
            "thread_alive": self.bot_thread.is_alive() if self.bot_thread else False,
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        return {
            "platform": "slack",
            "is_running": self._is_running,
            "uptime": 0,
            "message_count": sum(len(m) for m in self.memory.values()),
            "channel_count": len(self.memory),
        }

    def _run_bot_thread(self, config: SlackBotConfig) -> None:
        """Run bot in a separate thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def main_startup():
            try:
                from py.get_setting import load_settings
                from py.behavior_engine import global_behavior_engine, BehaviorSettings

                settings = await load_settings()
                behavior_data = settings.get("behaviorSettings", {})

                target_ids = config.behaviorTargetChatIds
                if not target_ids:
                    slack_conf = settings.get("slackBotConfig", {})
                    target_ids = slack_conf.get("behaviorTargetChatIds", [])

                if behavior_data:
                    logger.info(f"Slack: syncing behavior config... targets: {len(target_ids)}")
                    target_map = {"slack": target_ids}
                    global_behavior_engine.update_config(behavior_data, target_map)
                    config.behaviorSettings = BehaviorSettings(**behavior_data)
                    config.behaviorTargetChatIds = target_ids

                if not global_behavior_engine.is_running:
                    asyncio.create_task(global_behavior_engine.start())
                    logger.info("Behavior engine started in Slack thread")

                await self._async_start(config)

            except Exception as e:
                logger.exception(f"Slack startup exception: {e}")
                self._is_running = False
                self._ready_complete.set()

        try:
            self.loop.run_until_complete(main_startup())
        except Exception as e:
            logger.error(f"Slack thread loop exception: {e}")
        finally:
            self._is_running = False
            if not self._ready_complete.is_set():
                self._ready_complete.set()
            try:
                self.loop.close()
            except:
                pass

    async def _async_start(self, config: SlackBotConfig) -> None:
        """Async start implementation."""
        web_client = AsyncWebClient(token=config.bot_token)

        auth = await web_client.auth_test()
        self.bot_user_id = auth["user_id"]

        self.socket_client = SocketModeClient(
            app_token=config.app_token, web_client=web_client
        )

        async def process_listener(client, req: SocketModeRequest):
            if req.type == "events_api":
                await client.send_socket_mode_response(
                    SocketModeResponse(envelope_id=req.envelope_id)
                )
                event = req.payload.get("event", {})
                if event.get("user") == self.bot_user_id or event.get("bot_id") or "subtype" in event:
                    return
                if event.get("type") in ["message", "app_mention"]:
                    asyncio.ensure_future(self._handle_message(event, web_client))

        self.socket_client.socket_mode_request_listeners.append(process_listener)
        await self.socket_client.connect()
        self._is_running = True
        self._ready_complete.set()

        while self._is_running:
            await asyncio.sleep(1)

    async def _handle_message(self, event: dict, web_client: AsyncWebClient) -> None:
        """Handle incoming message."""
        cid = event["channel"]
        text = event.get("text", "").strip()

        if cid not in self.memory:
            self.memory[cid], self.async_tools[cid], self.file_links[cid] = [], [], []

        from py.behavior_engine import global_behavior_engine
        global_behavior_engine.report_activity("slack", cid)

        if text.lower() == "/id":
            info_msg = (
                f"Slack Session Information\n\n"
                f"Current Channel ID:\n`{cid}`\n\n"
                f"Please copy the ID above and paste into the target list."
            )
            await web_client.chat_postMessage(channel=cid, text=info_msg)
            return

        if self._config.wakeWord and self._config.wakeWord not in text:
            return

        if self._config.quick_restart and text in ["/重启", "/restart"]:
            self.memory[cid].clear()
            await web_client.chat_postMessage(channel=cid, text="对话记录已重置。")
            return

        self.memory[cid].append({"role": "user", "content": text})

        state = {"text_buffer": "", "image_buffer": "", "image_cache": []}

        initial_resp = await web_client.chat_postMessage(channel=cid, text="...")
        reply_ts = initial_resp["ts"]

        settings = await load_settings()
        from py.get_setting import get_port
        client_ai = AsyncOpenAI(
            api_key="super-secret-key",
            base_url=f"http://127.0.0.1:{get_port()}/v1"
        )

        try:
            stream = await client_ai.chat.completions.create(
                model=self._config.llm_model,
                messages=self.memory[cid],
                stream=True,
                extra_body={
                    "asyncToolsID": self.async_tools[cid],
                    "fileLinks": self.file_links[cid],
                    "is_app_bot": True,
                },
            )

            full_response = []
            last_update_time = time.time()

            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta_raw = chunk.choices[0].delta

                tool_link = getattr(delta_raw, "tool_link", None)
                if tool_link and settings.get("tools", {}).get("toolMemorandum", {}).get("enabled"):
                    if tool_link not in self.file_links[cid]:
                        self.file_links[cid].append(tool_link)

                async_tool_id = getattr(delta_raw, "async_tool_id", None)
                if async_tool_id:
                    if async_tool_id not in self.async_tools[cid]:
                        self.async_tools[cid].append(async_tool_id)
                    else:
                        self.async_tools[cid].remove(async_tool_id)

                content = delta_raw.content or ""
                reasoning = getattr(delta_raw, "reasoning_content", None) or ""
                if reasoning and self._config.reasoning_visible:
                    content = reasoning

                full_response.append(content)
                state["text_buffer"] += content
                state["image_buffer"] += content

                now = time.time()
                if (now - last_update_time > 1.2) or any(sep in content for sep in self._config.separators):
                    seg = self._clean_text(state["text_buffer"])
                    if seg and seg.strip():
                        await web_client.chat_update(channel=cid, ts=reply_ts, text=seg + " ▌")
                        last_update_time = now

            full_content = "".join(full_response)
            final_text = self._clean_text(full_content)
            await web_client.chat_update(channel=cid, ts=reply_ts, text=final_text or "回复完成。")

            self._extract_images(state)
            for img_url in state["image_cache"]:
                await self._send_image(cid, img_url, web_client)

            if self._config.enable_tts:
                await self._send_voice(cid, full_content, web_client)

            self.memory[cid].append({"role": "assistant", "content": full_content})
            if self._config.memory_limit > 0:
                while len(self.memory[cid]) > self._config.memory_limit * 2:
                    self.memory[cid].pop(0)

        except Exception as e:
            logger.error(f"Slack bot error: {e}")
            await web_client.chat_update(channel=cid, ts=reply_ts, text=f"处理消息失败: {e}")

    def _extract_images(self, state: Dict[str, Any]) -> None:
        """Extract image URLs from text."""
        pattern = r'!\[.*?\]\((https?://[^\s)]+)'
        for m in re.finditer(pattern, state["image_buffer"]):
            state["image_cache"].append(m.group(1))

    def _clean_text(self, text: str) -> str:
        """Clean text by removing HTML and image markdown."""
        text = re.sub(r'<.*?>', '', text)
        return re.sub(r"!\[.*?\]\(.*?\)", "", text).strip()

    async def _send_image(self, cid: str, url: str, web_client: AsyncWebClient) -> None:
        """Send image to channel."""
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url) as r:
                    if r.status == 200:
                        data = await r.read()
                        await web_client.files_upload_v2(
                            channel=cid, file=data, filename="image.png"
                        )
        except Exception as e:
            logger.error(f"Image send failed: {e}")

    async def _send_voice(self, cid: str, text: str, web_client: AsyncWebClient) -> None:
        """Send voice message to channel."""
        try:
            from py.get_setting import get_port, load_settings

            settings = await load_settings()
            tts_settings = settings.get("ttsSettings", {})

            clean_text = re.sub(r'[*_~`#]|!\[.*?\]\(.*?\)', '', text)
            if not clean_text.strip():
                return

            payload = {
                "text": clean_text[:300],
                "voice": "default",
                "ttsSettings": tts_settings,
                "index": 0,
                "mobile_optimized": False,
                "format": "mp3",
            }

            async with aiohttp.ClientSession() as s:
                async with s.post(f"http://127.0.0.1:{get_port()}/tts", json=payload) as r:
                    if r.status == 200:
                        audio = await r.read()
                        await web_client.files_upload_v2(
                            channel=cid,
                            file=audio,
                            filename="voice.mp3",
                            title="语音回复",
                            initial_comment="语音合成已完成",
                        )
        except Exception as e:
            logger.error(f"Voice send failed: {e}")

    async def execute_behavior_event(self, chat_id: str, behavior_item: Any) -> None:
        """Execute behavior event triggered by behavior engine."""
        if not self.socket_client or not self.socket_client.web_client:
            return

        logger.info(f"[SlackBot] Behavior trigger! Target: {chat_id}")

        prompt_content = await self._resolve_behavior_prompt(behavior_item)
        if not prompt_content:
            return

        cid = chat_id
        if cid not in self.memory:
            self.memory[cid] = []

        messages = self.memory[cid].copy()
        system_instruction = f"[system]: {prompt_content}"
        messages.append({"role": "user", "content": system_instruction})
        self.memory[cid].append({"role": "user", "content": system_instruction})

        try:
            from py.get_setting import get_port
            client_ai = AsyncOpenAI(
                api_key="super-secret-key",
                base_url=f"http://127.0.0.1:{get_port()}/v1"
            )

            response = await client_ai.chat.completions.create(
                model=self._config.llm_model,
                messages=messages,
                stream=False,
                extra_body={
                    "is_app_bot": True,
                    "behavior_trigger": True,
                },
            )

            reply_content = response.choices[0].message.content
            if reply_content:
                await self.socket_client.web_client.chat_postMessage(
                    channel=cid, text=reply_content
                )
                self.memory[cid].append({"role": "assistant", "content": reply_content})

                if self._config.enable_tts:
                    await self._send_voice(cid, reply_content, self.socket_client.web_client)

        except Exception as e:
            logger.error(f"[SlackBot] Behavior execution failed: {e}")

    async def _resolve_behavior_prompt(self, behavior: Any) -> Optional[str]:
        """Resolve behavior configuration to prompt."""
        import random
        action = behavior.action

        if action.type == "prompt":
            return action.prompt
        elif action.type == "random":
            if not action.random or not action.random.events:
                return None
            events = action.random.events
            if action.random.type == "random":
                return random.choice(events)
            elif action.random.type == "order":
                idx = action.random.orderIndex
                if idx >= len(events):
                    idx = 0
                selected = events[idx]
                action.random.orderIndex = idx + 1
                return selected
        return None

    async def send_message(self, chat_id: str, message: str) -> bool:
        """Send a message to a channel."""
        try:
            if self.socket_client and self.socket_client.web_client:
                await self.socket_client.web_client.chat_postMessage(
                    channel=chat_id, text=message
                )
                return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
        return False

    # Sync compatibility methods for BotManagerAdapter
    @property
    def is_running(self) -> bool:
        """Return True if bot is running."""
        return self._is_running

    def start_bot(self, config) -> None:
        """Start the bot (sync wrapper for BotManagerAdapter)."""
        if self._is_running:
            return
        config_dict = config.__dict__ if hasattr(config, '__dict__') else dict(config)
        asyncio.run(self._initialize(config_dict))
        asyncio.run(self._start())

    def stop_bot(self) -> None:
        """Stop the bot (sync wrapper for BotManagerAdapter)."""
        if not self._is_running and not self.bot_thread:
            return
        asyncio.run(self._stop())

    def get_status(self) -> dict:
        """Get bot status (sync wrapper for BotManagerAdapter)."""
        return {
            "is_running": self._is_running,
            "thread_alive": self.bot_thread.is_alive() if self.bot_thread else False,
            "startup_error": self._startup_error,
        }
