"""Base plugin class for tools."""

from abc import abstractmethod
from typing import Dict, Any, List, Optional

from py.plugins.base import Plugin, PluginMetadata


class ToolPlugin(Plugin):
    """Abstract base class for tool plugins.

    Tools provide specific functionality like CLI execution,
    web search, file handling, etc.
    """

    def __init__(self) -> None:
        super().__init__()

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Return the tool name."""
        raise NotImplementedError

    @property
    def metadata(self) -> PluginMetadata:
        """Return the plugin metadata."""
        return PluginMetadata(
            id=f"tool.{self.tool_name}",
            name=f"{self.tool_name.title()} Tool",
            version="1.0.0",
            description=f"Tool plugin for {self.tool_name}",
        )

    @abstractmethod
    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the tool with configuration."""
        raise NotImplementedError

    @abstractmethod
    async def execute(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with given arguments.

        Args:
            tool_name: Name of the tool to execute.
            args: Arguments for the tool.

        Returns:
            Result dictionary with tool output.
        """
        raise NotImplementedError

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return list of tool definitions for this plugin.

        Returns:
            List of tool definition dictionaries compatible with
            OpenAI's function calling format.
        """
        return []
