"""Discord Bot Platform Plugin.

Refactored from discord_bot_manager.py
"""

import asyncio
import base64
import io
import logging
import random
import re
import threading
from typing import Dict, Any, List, Optional

import aiohttp
import discord
from discord.ext import commands
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from py.bots.platforms.base import BotPlatformPlugin
from py.plugins.base import PluginMetadata

logger = logging.getLogger(__name__)


class DiscordBotConfig(BaseModel):
    """Discord bot configuration."""
    token: str
    llm_model: str = "super-model"
    memory_limit: int = 10
    separators: List[str] = ["。", "\n", "？", "！"]
    reasoning_visible: bool = False
    quick_restart: bool = True
    enable_tts: bool = True
    wakeWord: str = ""
    behaviorSettings: Optional[Dict[str, Any]] = None
    behaviorTargetChatIds: List[str] = Field(default_factory=list)


class DiscordBotPlugin(BotPlatformPlugin):
    """Discord bot platform implementation."""

    platform_name = "discord"

    def __init__(self) -> None:
        super().__init__()
        self.bot_thread: Optional[threading.Thread] = None
        self.bot_client: Optional["DiscordClient"] = None
        self._is_running = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._shutdown_event = threading.Event()
        self._ready_complete = threading.Event()
        self._startup_error: Optional[str] = None
        self._stop_requested = False

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="bot.platform.discord",
            name="Discord Bot Platform",
            version="1.0.0",
            description="Discord bot platform plugin for server messaging",
        )

    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the Discord bot with configuration."""
        self._config = DiscordBotConfig(**config)
        logger.info("Discord bot initialized")

    async def _start(self) -> None:
        """Start the Discord bot."""
        if self._is_running:
            return

        self._shutdown_event.clear()
        self._ready_complete.clear()
        self._startup_error = None
        self._stop_requested = False

        self.bot_thread = threading.Thread(
            target=self._run_bot_thread,
            args=(self._config,),
            daemon=True,
            name="DiscordBotThread"
        )
        self.bot_thread.start()

        if not self._ready_complete.wait(timeout=30):
            await self._stop()
            raise RuntimeError("Discord bot ready timeout")

        if self._startup_error:
            await self._stop()
            raise RuntimeError(f"Discord bot startup failed: {self._startup_error}")

        self._is_running = True
        logger.info("Discord bot started")

    async def _stop(self) -> None:
        """Stop the Discord bot."""
        if not self._is_running and not self.bot_thread:
            return

        self._stop_requested = True
        self._shutdown_event.set()
        self._is_running = False

        if self.bot_client:
            asyncio.run_coroutine_threadsafe(self.bot_client.close(), self.loop)

        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=5)

        self._cleanup()
        logger.info("Discord bot stopped")

    async def _reload(self, config: Dict[str, Any]) -> None:
        """Reload the bot with new configuration."""
        await self._stop()
        self._config = DiscordBotConfig(**config)
        if self.bot_client:
            self.bot_client.config.llm_model = self._config.llm_model
            self.bot_client.config.enable_tts = self._config.enable_tts
            self.bot_client.config.wakeWord = self._config.wakeWord

    def _cleanup(self) -> None:
        """Cleanup resources."""
        self._is_running = False
        if self.loop and not self.loop.is_closed():
            try:
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    task.cancel()
                self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                self.loop.close()
            except Exception:
                pass
        logger.info("Discord bot resources cleaned up")

    async def get_status(self) -> Dict[str, Any]:
        """Get current bot status."""
        return {
            "is_running": self._is_running,
            "thread_alive": self.bot_thread.is_alive() if self.bot_thread else False,
            "ready_completed": self._ready_complete.is_set(),
            "startup_error": self._startup_error,
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        message_count = 0
        if self.bot_client:
            message_count = sum(len(m) for m in self.bot_client.memory.values())
        return {
            "platform": "discord",
            "is_running": self._is_running,
            "uptime": 0,
            "message_count": message_count,
        }

    def _run_bot_thread(self, config: DiscordBotConfig) -> None:
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
                    discord_conf = settings.get("discordBotConfig", {})
                    target_ids = discord_conf.get("behaviorTargetChatIds", [])

                if behavior_data:
                    logger.info(f"Discord: syncing behavior config... targets: {len(target_ids)}")
                    target_map = {"discord": target_ids}
                    global_behavior_engine.update_config(behavior_data, target_map)
                    config.behaviorSettings = BehaviorSettings(**behavior_data)
                    config.behaviorTargetChatIds = target_ids

                self.bot_client = DiscordClient(config, manager=self)

                if not global_behavior_engine.is_running:
                    asyncio.create_task(global_behavior_engine.start())
                    logger.info("Behavior engine started in Discord thread")

                await self.bot_client.start(config.token)

            except Exception as e:
                self._startup_error = str(e)
                logger.exception("Discord bot startup error")

        try:
            self.loop.run_until_complete(main_startup())
        except Exception as e:
            if not self._stop_requested:
                self._startup_error = str(e)
                logger.exception("Discord bot thread exception")
        finally:
            self._cleanup()

    async def send_message(self, chat_id: str, message: str) -> bool:
        """Send a message to a channel."""
        try:
            if self.bot_client:
                channel = self.bot_client.get_channel(int(chat_id))
                if channel:
                    await channel.send(message)
                    return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
        return False


class DiscordClient(discord.Client):
    """Discord client implementation."""

    def __init__(self, config: DiscordBotConfig, manager: DiscordBotPlugin):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.config = config
        self.manager = manager
        self.memory: Dict[int, List[dict]] = {}
        self.async_tools: Dict[int, List[str]] = {}
        self.file_links: Dict[int, List[str]] = {}
        self._shutdown_requested = False

        from py.behavior_engine import global_behavior_engine
        global_behavior_engine.register_handler("discord", self.execute_behavior_event)

    async def on_ready(self) -> None:
        self.manager._is_running = True
        self.manager._ready_complete.set()
        logger.info(f"Discord bot online: {self.user}")

    async def on_message(self, msg: discord.Message) -> None:
        if self._shutdown_requested or msg.author == self.user:
            return
        try:
            await self._handle_message(msg)
        except Exception as e:
            logger.exception("Discord message handling failed")
            await msg.channel.send(f"处理消息失败: {e}")

    async def _handle_message(self, msg: discord.Message) -> None:
        """Handle incoming message."""
        cid = msg.channel.id
        if cid not in self.memory:
            self.memory[cid] = []
            self.async_tools[cid] = []
            self.file_links[cid] = []

        from py.behavior_engine import global_behavior_engine
        global_behavior_engine.report_activity("discord", str(cid))

        if msg.content:
            content_strip = msg.content.strip()

            if content_strip.lower() == "/id":
                info_msg = (
                    f"Discord Session Information\n\n"
                    f"Current Channel ID:\n`{cid}`\n\n"
                    f"Copy the ID above to the target list."
                )
                await msg.reply(info_msg)
                return

            if self.config.quick_restart:
                if content_strip in {"/重启", "/restart"}:
                    self.memory[cid].clear()
                    await msg.reply("对话记录已重置。")
                    return

        user_content = []
        user_text = ""
        has_media = False

        if msg.content:
            user_text = msg.content

        for att in msg.attachments:
            if att.content_type and att.content_type.startswith("image"):
                b64data = base64.b64encode(await att.read()).decode()
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{att.content_type};base64,{b64data}"}
                })
                has_media = True

        for att in msg.attachments:
            if att.content_type and att.content_type.startswith("audio"):
                audio_bytes = await att.read()
                asr_text = await self._transcribe_audio(audio_bytes, att.filename)
                if asr_text:
                    user_text += f"\n[语音转写] {asr_text}"
                else:
                    user_text += "\n[语音转写失败]"

        if self.config.wakeWord:
            if self.config.wakeWord not in user_text:
                return

        if has_media and user_text:
            user_content.append({"type": "text", "text": user_text})
        if not has_media and not user_text:
            return

        self.memory[cid].append({"role": "user", "content": user_content or user_text})

        from py.get_setting import get_port, load_settings
        settings = await load_settings()
        client = AsyncOpenAI(api_key="super-secret-key", base_url=f"http://127.0.0.1:{get_port()}/v1")

        async_tools = self.async_tools.get(cid, [])
        file_links = self.file_links.get(cid, [])

        try:
            stream = await client.chat.completions.create(
                model=self.config.llm_model,
                messages=self.memory[cid],
                stream=True,
                extra_body={
                    "asyncToolsID": async_tools,
                    "fileLinks": file_links,
                    "is_app_bot": True,
                },
            )

            full_response = []
            text_buffer = ""
            last_update_time = time.time()

            initial_resp = await msg.reply("...")
            reply_msg = initial_resp

            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta

                tool_link = getattr(delta, "tool_link", None)
                if tool_link and settings.get("tools", {}).get("toolMemorandum", {}).get("enabled"):
                    if tool_link not in self.file_links[cid]:
                        self.file_links[cid].append(tool_link)

                async_tool_id = getattr(delta, "async_tool_id", None)
                if async_tool_id:
                    if async_tool_id not in self.async_tools[cid]:
                        self.async_tools[cid].append(async_tool_id)
                    else:
                        self.async_tools[cid].remove(async_tool_id)

                content = delta.content or ""
                reasoning = getattr(delta, "reasoning_content", None) or ""
                if reasoning and self.config.reasoning_visible:
                    content = reasoning

                full_response.append(content)
                text_buffer += content

                now = time.time()
                if (now - last_update_time > 1.2) or any(sep in content for sep in self.config.separators):
                    seg = self._clean_text(text_buffer)
                    if seg and seg.strip():
                        await reply_msg.edit(content=seg + " ▌")
                        last_update_time = now

            full_content = "".join(full_response)
            final_text = self._clean_text(full_content)
            await reply_msg.edit(content=final_text or "回复完成。")

            self._extract_images(text_buffer)
            # Handle image cache...

            if self.config.enable_tts:
                await self._send_voice(msg.channel, full_content)

            self.memory[cid].append({"role": "assistant", "content": full_content})
            if self.config.memory_limit > 0:
                while len(self.memory[cid]) > self.config.memory_limit * 2:
                    self.memory[cid].pop(0)

        except Exception as e:
            logger.exception("AI generation failed")
            await msg.reply(f"处理消息失败: {e}")

    def _extract_images(self, text: str) -> List[str]:
        """Extract image URLs from text."""
        pattern = r'!\[.*?\]\((https?://[^\s)]+)'
        return re.findall(pattern, text)

    def _clean_text(self, text: str) -> str:
        """Clean text by removing HTML and image markdown."""
        text = re.sub(r'<.*?>', '', text)
        return re.sub(r"!\[.*?\]\(.*?\)", "", text).strip()

    async def _transcribe_audio(self, audio_bytes: bytes, filename: str) -> Optional[str]:
        """Transcribe audio file."""
        # Placeholder - would need actual ASR implementation
        return None

    async def _send_voice(self, channel, text: str) -> None:
        """Send voice message."""
        # Placeholder - would need actual TTS implementation
        pass

    async def execute_behavior_event(self, chat_id: str, behavior_item: Any) -> None:
        """Execute behavior event triggered by behavior engine."""
        logger.info(f"[Discord] Behavior trigger! Target: {chat_id}")

        prompt_content = await self._resolve_behavior_prompt(behavior_item)
        if not prompt_content:
            return

        cid = int(chat_id)
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
                model=self.config.llm_model,
                messages=messages,
                stream=False,
                extra_body={
                    "is_app_bot": True,
                    "behavior_trigger": True,
                },
            )

            reply_content = response.choices[0].message.content
            if reply_content:
                channel = self.get_channel(cid)
                if channel:
                    await channel.send(reply_content)
                    self.memory[cid].append({"role": "assistant", "content": reply_content})

        except Exception as e:
            logger.error(f"[Discord] Behavior execution failed: {e}")

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


import time
