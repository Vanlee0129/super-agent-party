"""Plugin registry for managing installed plugins."""

import logging
from typing import Dict, List, Optional

from py.core.exceptions import PluginError
from py.plugins.base import Plugin, PluginMetadata

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing plugin lifecycle and discovery."""

    def __init__(self) -> None:
        self._plugins: Dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        """Register a plugin.

        Args:
            plugin: The plugin instance to register.

        Raises:
            PluginError: If a plugin with the same ID is already registered.
        """
        plugin_id = plugin.metadata.id
        if plugin_id in self._plugins:
            raise PluginError(f"Plugin with ID '{plugin_id}' is already registered")
        self._plugins[plugin_id] = plugin
        logger.info(f"Registered plugin: {plugin_id}")

    def unregister(self, plugin_id: str) -> None:
        """Unregister a plugin by ID.

        Args:
            plugin_id: The unique identifier of the plugin to unregister.
        """
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            logger.info(f"Unregistered plugin: {plugin_id}")

    def get(self, plugin_id: str) -> Optional[Plugin]:
        """Get a plugin by ID.

        Args:
            plugin_id: The unique identifier of the plugin.

        Returns:
            The plugin instance, or None if not found.
        """
        return self._plugins.get(plugin_id)

    def list_all(self) -> List[Plugin]:
        """List all registered plugins.

        Returns:
            A list of all registered plugin instances.
        """
        return list(self._plugins.values())

    def list_enabled(self) -> List[Plugin]:
        """List all enabled plugins.

        Returns:
            A list of all enabled plugin instances.
        """
        return [p for p in self._plugins.values() if p.enabled]

    def get_metadata(self, plugin_id: str) -> Optional[PluginMetadata]:
        """Get the metadata for a plugin by ID.

        Args:
            plugin_id: The unique identifier of the plugin.

        Returns:
            The plugin metadata, or None if not found.
        """
        plugin = self._plugins.get(plugin_id)
        return plugin.metadata if plugin else None

    def register_bot_platform(self, platform: str, plugin_class) -> None:
        """Register a bot platform plugin.

        Args:
            platform: The platform name (e.g., 'feishu', 'discord').
            plugin_class: The plugin class to instantiate.
        """
        plugin_id = f"bot.platform.{platform}"
        if plugin_id in self._plugins:
            logger.warning(f"Plugin {plugin_id} already registered, skipping")
            return
        plugin = plugin_class()
        self._plugins[plugin_id] = plugin
        logger.info(f"Registered bot platform: {platform}")

    def register_tool(self, tool_name: str, plugin_class) -> None:
        """Register a tool plugin.

        Args:
            tool_name: The tool name.
            plugin_class: The plugin class to instantiate.
        """
        plugin_id = f"tool.{tool_name}"
        if plugin_id in self._plugins:
            logger.warning(f"Plugin {plugin_id} already registered, skipping")
            return
        plugin = plugin_class()
        self._plugins[plugin_id] = plugin
        logger.info(f"Registered tool: {tool_name}")

    def register_search_provider(self, provider: str, plugin_class) -> None:
        """Register a search provider plugin.

        Args:
            provider: The provider name.
            plugin_class: The plugin class to instantiate.
        """
        plugin_id = f"search.provider.{provider}"
        if plugin_id in self._plugins:
            logger.warning(f"Plugin {plugin_id} already registered, skipping")
            return
        plugin = plugin_class()
        self._plugins[plugin_id] = plugin
        logger.info(f"Registered search provider: {provider}")


def load_builtin_plugins() -> None:
    """Load all built-in plugins into the registry."""
    # Bot platforms
    try:
        from py.bots.platforms.feishu import FeishuBotPlugin
        registry.register_bot_platform("feishu", FeishuBotPlugin)
    except ImportError as e:
        logger.warning(f"Could not load FeishuBotPlugin: {e}")

    try:
        from py.bots.platforms.qq import QQBotPlugin
        registry.register_bot_platform("qq", QQBotPlugin)
    except ImportError as e:
        logger.warning(f"Could not load QQBotPlugin: {e}")

    try:
        from py.bots.platforms.discord import DiscordBotPlugin
        registry.register_bot_platform("discord", DiscordBotPlugin)
    except ImportError as e:
        logger.warning(f"Could not load DiscordBotPlugin: {e}")

    try:
        from py.bots.platforms.slack import SlackBotPlugin
        registry.register_bot_platform("slack", SlackBotPlugin)
    except ImportError as e:
        logger.warning(f"Could not load SlackBotPlugin: {e}")

    try:
        from py.bots.platforms.dingtalk import DingtalkBotPlugin
        registry.register_bot_platform("dingtalk", DingtalkBotPlugin)
    except ImportError as e:
        logger.warning(f"Could not load DingtalkBotPlugin: {e}")

    try:
        from py.bots.platforms.telegram import TelegramBotPlugin
        registry.register_bot_platform("telegram", TelegramBotPlugin)
    except ImportError as e:
        logger.warning(f"Could not load TelegramBotPlugin: {e}")

    # Tools
    try:
        from py.tools.cli import CLIToolPlugin
        registry.register_tool("cli", CLIToolPlugin)
    except ImportError as e:
        logger.warning(f"Could not load CLIToolPlugin: {e}")

    try:
        from py.tools.cdp import CDPToolPlugin
        registry.register_tool("cdp", CDPToolPlugin)
    except ImportError as e:
        logger.warning(f"Could not load CDPToolPlugin: {e}")

    try:
        from py.tools.computer_use import ComputerUseToolPlugin
        registry.register_tool("computer_use", ComputerUseToolPlugin)
    except ImportError as e:
        logger.warning(f"Could not load ComputerUseToolPlugin: {e}")

    try:
        from py.tools.utility import UtilityToolPlugin
        registry.register_tool("utility", UtilityToolPlugin)
    except ImportError as e:
        logger.warning(f"Could not load UtilityToolPlugin: {e}")

    try:
        from py.tools.task import TaskToolPlugin
        registry.register_tool("task", TaskToolPlugin)
    except ImportError as e:
        logger.warning(f"Could not load TaskToolPlugin: {e}")

    try:
        from py.tools.file_loader import FileLoaderToolPlugin
        registry.register_tool("file_loader", FileLoaderToolPlugin)
    except ImportError as e:
        logger.warning(f"Could not load FileLoaderToolPlugin: {e}")

    # Search providers
    try:
        from py.search.providers.duckduckgo import DuckDuckGoSearchProvider
        registry.register_search_provider("duckduckgo", DuckDuckGoSearchProvider)
    except ImportError as e:
        logger.warning(f"Could not load DuckDuckGoSearchProvider: {e}")

    try:
        from py.search.providers.searxng import SearXNGSearchProvider
        registry.register_search_provider("searxng", SearXNGSearchProvider)
    except ImportError as e:
        logger.warning(f"Could not load SearXNGSearchProvider: {e}")

    try:
        from py.search.providers.bochaai import BochaAISearchProvider
        registry.register_search_provider("bochaai", BochaAISearchProvider)
    except ImportError as e:
        logger.warning(f"Could not load BochaAISearchProvider: {e}")

    try:
        from py.search.providers.tavily import TavilySearchProvider
        registry.register_search_provider("tavily", TavilySearchProvider)
    except ImportError as e:
        logger.warning(f"Could not load TavilySearchProvider: {e}")


# Global registry instance
registry = PluginRegistry()
