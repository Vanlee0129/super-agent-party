"""Plugin registry for managing installed plugins."""

from typing import Dict, List, Optional

from py.core.exceptions import PluginError
from py.plugins.base import Plugin, PluginMetadata


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

    def unregister(self, plugin_id: str) -> None:
        """Unregister a plugin by ID.

        Args:
            plugin_id: The unique identifier of the plugin to unregister.
        """
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]

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


# Global registry instance
registry = PluginRegistry()
