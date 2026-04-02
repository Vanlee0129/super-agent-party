"""Base plugin class for bot platforms."""

from abc import abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from py.plugins.base import Plugin, PluginMetadata


@dataclass
class BotPlatformConfig:
    """Configuration for a bot platform."""
    memory_limit: int = 30
    separators: list[str] = field(default_factory=["。", "\n", "？", "！"])
    reasoning_visible: bool = True
    quick_restart: bool = True
    enable_tts: bool = False
    wake_word: str = ""
    behavior_settings: Optional[Dict[str, Any]] = None
    behavior_target_chat_ids: list[str] = field(default_factory=list)


class BotPlatformPlugin(Plugin):
    """Abstract base class for bot platform plugins.

    All bot platform implementations should inherit from this class
    and implement the required abstract methods.
    """

    def __init__(self) -> None:
        super().__init__()
        self._client = None
        self._config: Optional[BotPlatformConfig] = None

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform name (e.g., 'feishu', 'discord')."""
        raise NotImplementedError

    @property
    def metadata(self) -> PluginMetadata:
        """Return the plugin metadata."""
        return PluginMetadata(
            id=f"bot.platform.{self.platform_name}",
            name=f"{self.platform_name.title()} Bot Platform",
            version="1.0.0",
            description=f"Bot platform plugin for {self.platform_name}",
        )

    @abstractmethod
    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the bot with configuration."""
        raise NotImplementedError

    @abstractmethod
    async def _start(self) -> None:
        """Start the bot."""
        raise NotImplementedError

    @abstractmethod
    async def _stop(self) -> None:
        """Stop the bot."""
        raise NotImplementedError

    @abstractmethod
    async def _reload(self, config: Dict[str, Any]) -> None:
        """Reload the bot with new configuration."""
        raise NotImplementedError

    async def reload(self, config: Dict[str, Any]) -> None:
        """Reload configuration (public API)."""
        await self._stop()
        await self._reload(config)
        await self._start()

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get current bot status."""
        raise NotImplementedError

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        raise NotImplementedError

    async def send_message(self, chat_id: str, message: str) -> bool:
        """Send a message to a chat.

        Args:
            chat_id: The chat identifier.
            message: The message to send.

        Returns:
            True if message was sent successfully.
        """
        raise NotImplementedError
