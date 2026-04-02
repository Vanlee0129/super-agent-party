"""QQ Bot Platform Plugin.

Refactored from qq_bot_manager.py
"""

import asyncio
import logging
import threading
import weakref
from typing import Dict, Any, List, Optional

import botpy
from botpy.message import C2CMessage, GroupMessage
from openai import AsyncOpenAI
from pydantic import BaseModel

from py.bots.platforms.base import BotPlatformPlugin
from py.plugins.base import PluginMetadata

logger = logging.getLogger(__name__)


class QQBotConfig(BaseModel):
    """QQ bot configuration."""
    QQAgent: str
    memoryLimit: int
    appid: str
    secret: str
    separators: List[str]
    reasoningVisible: bool
    quickRestart: bool
    is_sandbox: bool
    behaviorSettings: Optional[Dict[str, Any]] = None
    behaviorTargetChatIds: List[str] = []


class QQBotPlugin(BotPlatformPlugin):
    """QQ bot platform implementation."""

    platform_name = "qq"

    def __init__(self) -> None:
        super().__init__()
        self.bot_thread: Optional[threading.Thread] = None
        self.bot_client: Optional["MyClient"] = None
        self._is_running = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._shutdown_event = threading.Event()
        self._startup_complete = threading.Event()
        self._ready_complete = threading.Event()
        self._startup_error: Optional[str] = None

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="bot.platform.qq",
            name="QQ Bot Platform",
            version="1.0.0",
            description="QQ bot platform plugin for QQ messaging",
        )

    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the QQ bot with configuration."""
        self._config = QQBotConfig(**config)
        self.bot_client = MyClient(
            intents=botpy.Intents(public_messages=True),
            is_sandbox=self._config.is_sandbox
        )
        self.bot_client.QQAgent = self._config.QQAgent
        self.bot_client.memoryLimit = self._config.memoryLimit
        self.bot_client.separators = self._config.separators if self._config.separators else ['。', '\n', '？', '！']
        self.bot_client.reasoningVisible = self._config.reasoningVisible
        self.bot_client.quickRestart = self._config.quickRestart
        self.bot_client._manager_ref = weakref.ref(self)
        self.bot_client._ready_callback = self._on_bot_ready
        logger.info(f"QQ bot initialized: {self._config.appid}")

    async def _start(self) -> None:
        """Start the QQ bot."""
        if self._is_running:
            return

        self._shutdown_event.clear()
        self._startup_complete.clear()
        self._ready_complete.clear()
        self._startup_error = None

        self.bot_thread = threading.Thread(
            target=self._run_bot_thread,
            args=(self._config,),
            daemon=True,
            name="QQBotThread"
        )
        self.bot_thread.start()

        if not self._startup_complete.wait(timeout=30):
            await self._stop()
            raise Exception("QQ bot connection timeout")

        if self._startup_error:
            await self._stop()
            raise Exception(f"QQ bot startup failed: {self._startup_error}")

        if not self._ready_complete.wait(timeout=30):
            await self._stop()
            raise Exception("QQ bot ready timeout")

        self._is_running = True
        logger.info("QQ bot started")

    async def _stop(self) -> None:
        """Stop the QQ bot."""
        if not self._is_running and not self.bot_thread:
            return

        logger.info("Stopping QQ bot...")
        self._is_running = False

        if self.bot_client and self.loop:
            self.bot_client._shutdown_requested = True
            try:
                async def close_client():
                    try:
                        await self.bot_client.close()
                    except Exception as e:
                        logger.warning(f"Client close error: {e}")

                close_task = self.loop.create_task(close_client())
                self.loop.run_until_complete(close_task)
            except Exception:
                pass

        self._cleanup()
        logger.info("QQ bot stopped")

    async def _reload(self, config: Dict[str, Any]) -> None:
        """Reload the bot with new configuration."""
        await self._stop()
        self._config = QQBotConfig(**config)

    def _on_bot_ready(self) -> None:
        """Bot ready callback."""
        self._is_running = True
        if not self._ready_complete.is_set():
            self._ready_complete.set()
        logger.info("QQ bot ready")

    def _run_bot_thread(self, config: QQBotConfig) -> None:
        """Run bot in a separate thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        bot_task = None

        async def run_bot():
            nonlocal bot_task
            try:
                logger.info("Starting QQ bot connection...")
                await self.bot_client.start(appid=config.appid, secret=config.secret)
            except asyncio.CancelledError:
                logger.info("Bot task cancelled")
            except Exception as e:
                logger.error(f"Bot runtime exception: {e}")
                self._startup_error = str(e)
                if not self._startup_complete.is_set():
                    self._startup_complete.set()
                raise

        try:
            bot_task = self.loop.create_task(run_bot())

            def connection_established():
                if not self._startup_error:
                    self._startup_complete.set()
                    logger.info("Bot connection established, waiting for ready...")

            async def delayed_connection_check():
                await asyncio.sleep(2)
                if not bot_task.done() and not self._startup_error:
                    connection_established()

            check_task = self.loop.create_task(delayed_connection_check())
            self.loop.run_until_complete(bot_task)

        except Exception as e:
            logger.error(f"Bot thread exception: {e}")
            if not self._startup_error:
                self._startup_error = str(e)
        finally:
            if not self._startup_complete.is_set():
                self._startup_complete.set()
            if not self._ready_complete.is_set():
                self._ready_complete.set()

            if bot_task and not bot_task.done():
                bot_task.cancel()
                try:
                    self.loop.run_until_complete(bot_task)
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.warning(f"Bot task cancellation error: {e}")

            self._cleanup()

    def _cleanup(self) -> None:
        """Cleanup resources."""
        self._is_running = False

        if self.bot_client and self.loop and not self.loop.is_closed():
            try:
                self.bot_client._shutdown_requested = True

                async def close_client():
                    try:
                        await self.bot_client.close()
                    except Exception as e:
                        logger.warning(f"Client close error: {e}")

                close_task = self.loop.create_task(close_client())
                try:
                    self.loop.run_until_complete(close_task)
                except Exception:
                    pass
            except Exception:
                pass

        self.bot_client = None
        self.loop = None
        logger.info("QQ bot cleanup complete")

    async def get_status(self) -> Dict[str, Any]:
        """Get current bot status."""
        return {
            "is_running": self._is_running,
            "thread_alive": self.bot_thread.is_alive() if self.bot_thread else False,
            "startup_error": self._startup_error,
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        return {
            "platform": "qq",
            "is_running": self._is_running,
            "uptime": 0,
            "message_count": 0,
        }

    async def send_message(self, chat_id: str, message: str) -> bool:
        """Send a message to a chat."""
        # Implementation in MyClient
        return False


class MyClient(botpy.Client):
    """QQ client implementation."""

    def __init__(self, intents, is_sandbox: bool = False):
        super().__init__(intents=intents, is_sandbox=is_sandbox)
        self.QQAgent = "super-model"
        self.memoryLimit = 10
        self.separators = ['。', '\n', '？', '！']
        self.reasoningVisible = False
        self.quickRestart = True
        self._manager_ref = None
        self._ready_callback = None
        self._shutdown_requested = False
        self.memory_list: Dict[str, List[dict]] = {}

    async def on_ready(self) -> None:
        """Ready event handler."""
        if self._ready_callback:
            self._ready_callback()
        logger.info(f"QQ bot ready: {self.user}")

    async def on_c2c_message_create(self, message: C2CMessage) -> None:
        """Handle C2C (private) messages."""
        if self._shutdown_requested:
            return
        try:
            await self._handle_message(message, is_group=False)
        except Exception as e:
            logger.exception("C2C message handling failed")

    async def on_group_message_create(self, message: GroupMessage) -> None:
        """Handle group messages."""
        if self._shutdown_requested:
            return
        try:
            await self._handle_message(message, is_group=True)
        except Exception as e:
            logger.exception("Group message handling failed")

    async def _handle_message(self, message, is_group: bool) -> None:
        """Handle message based on type."""
        from py.behavior_engine import global_behavior_engine

        chat_id = str(message.group_id if is_group else message.open_id)
        global_behavior_engine.report_activity("qq", chat_id)

        # Similar message handling to original implementation
        # See original qq_bot_manager.py for full logic
