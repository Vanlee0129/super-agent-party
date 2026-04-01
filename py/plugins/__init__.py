"""Plugin system for Super Agent Party."""

from py.plugins.base import Plugin, PluginMetadata
from py.plugins.hooks import PluginHooks, hooks
from py.plugins.loader import PluginLoader
from py.plugins.registry import PluginRegistry, registry

__all__ = [
    "Plugin",
    "PluginMetadata",
    "PluginRegistry",
    "registry",
    "PluginLoader",
    "PluginHooks",
    "hooks",
]
