"""Bot manager registry for unified bot management."""

import logging
from typing import Dict, Optional, Any
from datetime import datetime

from py.feishu_bot_manager import FeishuBotManager, FeishuBotConfig
from py.qq_bot_manager import QQBotManager, QQBotConfig
from py.discord_bot_manager import DiscordBotManager, DiscordBotConfig
from py.slack_bot_manager import SlackBotManager, SlackBotConfig
from py.dingtalk_bot_manager import DingtalkBotManager, DingtalkBotConfig
from py.telegram_bot_manager import TelegramBotManager, TelegramBotConfig

logger = logging.getLogger(__name__)

PLATFORM_CONFIGS = {
    "feishu": (FeishuBotManager, FeishuBotConfig),
    "qq": (QQBotManager, QQBotConfig),
    "discord": (DiscordBotManager, DiscordBotConfig),
    "slack": (SlackBotManager, SlackBotConfig),
    "dingtalk": (DingtalkBotManager, DingtalkBotConfig),
    "telegram": (TelegramBotManager, TelegramBotConfig),
}


class BotManagerAdapter:
    """Adapter wrapper for platform-specific bot managers.

    Provides a unified interface for start, stop, status, reload, and stats operations
    across all supported bot platforms.
    """

    def __init__(self, platform: str, manager_instance: Any):
        self.platform = platform
        self._manager = manager_instance
        self._start_time: Optional[datetime] = None
        self._message_count = 0
        self._error_count = 0

    async def start(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Start the bot with optional config."""
        try:
            if config:
                config_model = PLATFORM_CONFIGS.get(self.platform, (None, None))[1]
                config_obj = config_model(**config.get("config", config)) if config_model else config
                self._manager.start_bot(config_obj)
            else:
                self._manager.start_bot(None)

            self._start_time = datetime.now()
            logger.info(f"Bot started: {self.platform}")
        except Exception as e:
            self._error_count += 1
            logger.error(f"Failed to start {self.platform} bot: {e}")
            raise

    async def stop(self) -> None:
        """Stop the bot."""
        try:
            self._manager.stop_bot()
            self._start_time = None
            logger.info(f"Bot stopped: {self.platform}")
        except Exception as e:
            self._error_count += 1
            logger.error(f"Failed to stop {self.platform} bot: {e}")
            raise

    async def reload(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Reload the bot with new config."""
        await self.stop()
        await self.start(config)

    async def get_status(self) -> Dict[str, Any]:
        """Get bot status."""
        status = self._manager.get_status()

        # Calculate uptime
        uptime = 0.0
        if self._start_time and status.get("is_running"):
            uptime = (datetime.now() - self._start_time).total_seconds()

        return {
            "platform": self.platform,
            "status": "running" if status.get("is_running") else "stopped",
            "uptime": uptime,
            "message_count": self._message_count,
            "error": status.get("startup_error"),
            "details": status,
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        return {
            "platform": self.platform,
            "uptime": (datetime.now() - self._start_time).total_seconds() if self._start_time else 0,
            "message_count": self._message_count,
            "error_count": self._error_count,
            "running": self._manager.is_running if hasattr(self._manager, "is_running") else False,
        }

    def increment_message_count(self) -> None:
        """Increment message count (can be called by bot handlers)."""
        self._message_count += 1


class BotRegistry:
    """Registry for all bot managers.

    Provides a central registry for managing bot managers across all platforms.
    """

    _managers: Dict[str, BotManagerAdapter] = {}

    @classmethod
    def register(cls, platform: str, manager: Any) -> None:
        """Register a bot manager for a platform."""
        adapter = BotManagerAdapter(platform, manager)
        cls._managers[platform] = adapter
        logger.info(f"Registered bot manager: {platform}")

    @classmethod
    def get(cls, platform: str) -> Optional[BotManagerAdapter]:
        """Get the bot manager adapter for a platform."""
        return cls._managers.get(platform)

    @classmethod
    def list_platforms(cls) -> list:
        """List all registered platforms."""
        return list(cls._managers.keys())

    @classmethod
    def is_registered(cls, platform: str) -> bool:
        """Check if a platform is registered."""
        return platform in cls._managers

    @classmethod
    async def start_all(cls) -> None:
        """Start all registered bots."""
        for platform, manager in cls._managers.items():
            try:
                await manager.start()
            except Exception as e:
                logger.error(f"Failed to start {platform}: {e}")

    @classmethod
    async def stop_all(cls) -> None:
        """Stop all registered bots."""
        for platform, manager in cls._managers.items():
            try:
                await manager.stop()
            except Exception as e:
                logger.error(f"Failed to stop {platform}: {e}")

    @classmethod
    def get_all_status(cls) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered bots."""
        return {platform: manager.get_status() for platform, manager in cls._managers.items()}


def get_bot_manager(platform: str) -> Optional[BotManagerAdapter]:
    """Get bot manager for a specific platform."""
    return BotRegistry.get(platform)


def get_supported_platforms() -> list:
    """Get list of all supported platforms."""
    return ["feishu", "qq", "discord", "slack", "dingtalk", "telegram"]


def initialize_managers() -> None:
    """Initialize and register all bot managers."""
    for platform, (manager_class, _) in PLATFORM_CONFIGS.items():
        try:
            BotRegistry.register(platform, manager_class())
        except Exception as e:
            logger.warning(f"Could not register {platform} manager: {e}")
