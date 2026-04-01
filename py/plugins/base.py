"""Base plugin classes for Super Agent Party."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from py.core.exceptions import PluginError


@dataclass
class PluginMetadata:
    """Metadata information for a plugin."""

    id: str
    name: str
    version: str
    description: str = ""
    author: str = "Unknown"
    dependencies: List[str] = field(default_factory=list)


class Plugin(ABC):
    """Abstract base class for all plugins."""

    def __init__(self) -> None:
        self._enabled: bool = False

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return the plugin metadata."""
        raise NotImplementedError

    @property
    def enabled(self) -> bool:
        """Check if the plugin is enabled."""
        return self._enabled

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the plugin with optional configuration.

        Args:
            config: Optional configuration dictionary for the plugin.
        """
        if self._enabled:
            raise PluginError(f"Plugin {self.metadata.id} is already initialized")

        try:
            self._initialize(config or {})
            self._enabled = True
        except Exception as e:
            raise PluginError(f"Failed to initialize plugin {self.metadata.id}: {e}") from e

    def start(self) -> None:
        """Start the plugin. Called after initialization."""
        if not self._enabled:
            raise PluginError(f"Plugin {self.metadata.id} is not initialized")
        self._start()

    def stop(self) -> None:
        """Stop the plugin. Called during shutdown."""
        if not self._enabled:
            return
        self._stop()
        self._enabled = False

    def cleanup(self) -> None:
        """Perform cleanup operations. Called after stop."""
        self._cleanup()

    @abstractmethod
    def _initialize(self, config: Dict[str, Any]) -> None:
        """Internal initialization logic. Override in subclasses."""
        raise NotImplementedError

    def _start(self) -> None:
        """Internal start logic. Override in subclasses if needed."""
        pass

    def _stop(self) -> None:
        """Internal stop logic. Override in subclasses if needed."""
        pass

    def _cleanup(self) -> None:
        """Internal cleanup logic. Override in subclasses if needed."""
        pass
