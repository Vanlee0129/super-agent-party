"""Telegram Bot Platform Plugin.

Refactored from telegram_bot_manager.py
"""

import asyncio
import logging
import threading
import weakref
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field

from py.bots.platforms.base import BotPlatformPlugin
from py.plugins.base import PluginMetadata

logger = logging.getLogger(__name__)


class TelegramBotConfig(BaseModel):
    """Telegram bot configuration."""
    TelegramAgent: str
    memoryLimit: int
    separators: list[str]
    reasoningVisible: bool
    quickRestart: bool
    enableTTS: bool
    bot_token: str
    wakeWord: str
    behaviorSettings: Optional[Dict[str, Any]] = None
    behaviorTargetChatIds: list[str] = Field(default_factory=list)


class TelegramBotPlugin(BotPlatformPlugin):
    """Telegram bot platform implementation."""

    platform_name = "telegram"

    def __init__(self) -> None:
        super().__init__()
        self.bot_thread: Optional[threading.Thread] = None
        self.bot_client = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._shutdown_event = threading.Event()
        self._startup_complete = threading.Event()
        self._ready_complete = threading.Event()
        self._startup_error: Optional[str] = None
        self._stop_requested = False
        self._is_running = False

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="bot.platform.telegram",
            name="Telegram Bot Platform",
            version="1.0.0",
            description="Telegram bot platform plugin for messaging",
        )

    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the Telegram bot with configuration."""
        from py.telegram_client import TelegramClient

        self._config = TelegramBotConfig(**config)
        self.bot_client = TelegramClient()
        self.bot_client.TelegramAgent = self._config.TelegramAgent
        self.bot_client.memoryLimit = self._config.memoryLimit
        self.bot_client.separators = self._config.separators or ["。", "\n", "？", "！"]
        self.bot_client.reasoningVisible = self._config.reasoningVisible
        self.bot_client.quickRestart = self._config.quickRestart
        self.bot_client.enableTTS = self._config.enableTTS
        self.bot_client.wakeWord = self._config.wakeWord
        self.bot_client.bot_token = self._config.bot_token
        self.bot_client.config = self._config
        self.bot_client._manager_ref = weakref.ref(self)
        self.bot_client._ready_callback = self._on_bot_ready
        logger.info(f"Telegram bot initialized: {self._config.bot_token[:10]}...")

    async def _start(self) -> None:
        """Start the Telegram bot."""
        if self._is_running:
            return

        self._shutdown_event.clear()
        self._startup_complete.clear()
        self._ready_complete.clear()
        self._startup_error = None
        self._stop_requested = False

        self.bot_thread = threading.Thread(
            target=self._run_bot_thread,
            args=(self._config,),
            daemon=True,
            name="TelegramBotThread"
        )
        self.bot_thread.start()

        if not self._startup_complete.wait(timeout=30):
            raise Exception("Telegram bot connection timeout")
        if self._startup_error:
            raise Exception(f"Telegram bot startup failed: {self._startup_error}")
        if not self._ready_complete.wait(timeout=30):
            raise Exception("Telegram bot ready timeout")

        self._is_running = True
        logger.info("Telegram bot started")

    async def _stop(self) -> None:
        """Stop the Telegram bot."""
        if not self._is_running and not self.bot_thread:
            return

        logger.info("Stopping Telegram bot...")
        self._stop_requested = True
        self._is_running = False

        if self.bot_client:
            self.bot_client._shutdown_requested = True

        self._shutdown_event.set()

        if self.bot_thread and self.bot_thread.is_alive():
            self.bot_thread.join(timeout=15)

        self._stop_requested = False
        logger.info("Telegram bot stopped")

    async def _reload(self, config: Dict[str, Any]) -> None:
        """Reload the bot with new configuration."""
        self._config = TelegramBotConfig(**config)
        if self.bot_client:
            self.bot_client.TelegramAgent = self._config.TelegramAgent
            self.bot_client.enableTTS = self._config.enableTTS
            self.bot_client.wakeWord = self._config.wakeWord
            self.bot_client.config = self._config

    def _on_bot_ready(self) -> None:
        """Bot ready callback."""
        self._is_running = True
        if not self._ready_complete.is_set():
            self._ready_complete.set()
        logger.info("Telegram bot ready")

    def _run_bot_thread(self, config: TelegramBotConfig) -> None:
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
                    tg_conf = settings.get("telegramBotConfig", {})
                    target_ids = tg_conf.get("behaviorTargetChatIds", [])

                if behavior_data:
                    logger.info(f"Telegram: syncing behavior config... targets: {len(target_ids)}")
                    target_map = {"telegram": target_ids}
                    global_behavior_engine.update_config(behavior_data, target_map)

                    if isinstance(behavior_data, dict):
                        config.behaviorSettings = BehaviorSettings(**behavior_data)
                    else:
                        config.behaviorSettings = behavior_data
                    config.behaviorTargetChatIds = target_ids

                if not global_behavior_engine.is_running:
                    asyncio.create_task(global_behavior_engine.start())
                    logger.info("Behavior engine started in Telegram thread")

                self._startup_complete.set()
                await self.bot_client.run()

            except Exception as e:
                if not self._stop_requested:
                    logger.error(f"Telegram bot exception: {e}")
                    self._startup_error = str(e)
                if not self._startup_complete.is_set():
                    self._startup_complete.set()
                if not self._ready_complete.is_set():
                    self._ready_complete.set()

        try:
            self.loop.run_until_complete(main_startup())
        except Exception as e:
            if not self._stop_requested:
                logger.error(f"Telegram thread loop exception: {e}")
        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Cleanup resources."""
        self._is_running = False
        logger.info("Cleaning up Telegram bot resources...")

        if self.loop and not self.loop.is_closed():
            try:
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    task.cancel()
                if self.loop.is_running():
                    self.loop.stop()
                self.loop.close()
            except Exception as e:
                logger.warning(f"Error closing event loop: {e}")

        self.bot_client = None
        self.loop = None
        self._shutdown_event.set()
        logger.info("Telegram bot cleanup complete")

    async def get_status(self) -> Dict[str, Any]:
        """Get current bot status."""
        return {
            "is_running": self._is_running,
            "thread_alive": self.bot_thread.is_alive() if self.bot_thread else False,
            "client_ready": self.bot_client._is_ready if self.bot_client else False,
            "loop_running": self.loop and not self.loop.is_closed() if self.loop else False,
            "startup_error": self._startup_error,
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        return {
            "platform": "telegram",
            "is_running": self._is_running,
            "uptime": 0,
            "message_count": 0,
            "error_count": 0,
        }

    async def send_message(self, chat_id: str, message: str) -> bool:
        """Send a message to a chat."""
        # Implementation delegated to telegram_client
        return False
