"""Plugin loader for discovering and loading plugins."""

import importlib.util
import sys
from pathlib import Path
from typing import List, Optional

from py.core.config import EXTENSIONS_DIR
from py.core.exceptions import PluginError
from py.plugins.base import Plugin
from py.plugins.registry import registry


class PluginLoader:
    """Handles plugin discovery and loading from various sources."""

    def __init__(self) -> None:
        self._loaded_plugin_ids: set = set()

    def load_from_directory(
        self, directory: str, pattern: str = "plugin*.py"
    ) -> List[Plugin]:
        """Discover and load plugins from a directory.

        Args:
            directory: The directory path to search for plugins.
            pattern: Glob pattern for matching plugin files.

        Returns:
            A list of loaded plugin instances.
        """
        loaded_plugins: List[Plugin] = []
        dir_path = Path(directory)

        if not dir_path.exists() or not dir_path.is_dir():
            return loaded_plugins

        for plugin_file in dir_path.glob(pattern):
            try:
                plugin = self._load_from_file(str(plugin_file))
                if plugin is not None:
                    registry.register(plugin)
                    self._loaded_plugin_ids.add(plugin.metadata.id)
                    loaded_plugins.append(plugin)
            except Exception as e:
                print(f"Failed to load plugin from {plugin_file}: {e}")

        return loaded_plugins

    def _load_from_file(self, filepath: str) -> Optional[Plugin]:
        """Load a plugin module from a file path.

        Args:
            filepath: The path to the plugin file.

        Returns:
            The loaded plugin instance, or None if not a valid plugin.
        """
        module_name = Path(filepath).stem

        spec = importlib.util.spec_from_file_location(module_name, filepath)
        if spec is None or spec.loader is None:
            return None

        try:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except Exception as e:
            raise PluginError(f"Failed to load plugin module '{module_name}': {e}") from e

        # Look for a plugin class in the module
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, Plugin)
                and attr is not Plugin
            ):
                return attr()  # Instantiate the plugin

        return None

    def load_builtin_plugins(self) -> List[Plugin]:
        """Load built-in plugins from the extensions directory.

        Returns:
            A list of loaded built-in plugin instances.
        """
        return self.load_from_directory(EXTENSIONS_DIR, "*.py")


# Global loader instance
loader = PluginLoader()
