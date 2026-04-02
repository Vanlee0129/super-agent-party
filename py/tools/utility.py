"""Utility Tools Plugin.

Refactored from utility_tools.py
"""

import logging
from datetime import datetime
from typing import Any, Dict

from py.plugins.base import PluginMetadata
from py.tools.base import ToolPlugin

logger = logging.getLogger(__name__)


class UtilityToolPlugin(ToolPlugin):
    """Utility tools plugin providing common helper functions."""

    tool_name = "utility"

    def __init__(self) -> None:
        super().__init__()
        self._tools: Dict[str, Any] = {}

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="tool.utility",
            name="Utility Tools",
            version="1.0.0",
            description="Utility tools for time, date, and other helpers",
        )

    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize utility tools."""
        self._tools = {
            "time_tool": self._get_current_time,
            "date_tool": self._get_current_date,
        }

    async def execute(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a utility tool."""
        if tool_name not in self._tools:
            raise ValueError(f"Unknown utility tool: {tool_name}")
        return await self._tools[tool_name](args)

    def _get_current_time(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get current time."""
        now = datetime.now()
        return {
            "time": now.strftime("%H:%M:%S"),
            "timestamp": now.timestamp(),
            "timezone": str(now.astimezone().tzinfo),
        }

    def _get_current_date(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get current date."""
        now = datetime.now()
        return {
            "date": now.strftime("%Y-%m-%d"),
            "weekday": now.strftime("%A"),
            "timestamp": now.timestamp(),
        }

    def get_tool_definitions(self) -> list:
        """Return tool definitions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "time_tool",
                    "description": "Get current time",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "date_tool",
                    "description": "Get current date",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            },
        ]
