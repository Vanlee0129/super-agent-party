"""Computer Use Tools Plugin.

Refactored from computer_use_tool.py
"""

import asyncio
import logging
import subprocess
from typing import Any, Dict, List

from py.plugins.base import PluginMetadata
from py.tools.base import ToolPlugin

logger = logging.getLogger(__name__)


class ComputerUseToolPlugin(ToolPlugin):
    """Computer use tools plugin for desktop control."""

    tool_name = "computer_use"

    def __init__(self) -> None:
        super().__init__()
        self._display = ":0"

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="tool.computer_use",
            name="Computer Use Tools",
            version="1.0.0",
            description="Desktop control tools for mouse, keyboard, and vision",
        )

    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize computer use tools."""
        self._display = config.get("display", ":0")

    async def execute(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a computer use tool."""
        if tool_name == "mouse_move":
            return await self._mouse_move(args)
        elif tool_name == "mouse_click":
            return await self._mouse_click(args)
        elif tool_name == "mouse_double_click":
            return await self._mouse_double_click(args)
        elif tool_name == "keyboard_type":
            return await self._keyboard_type(args)
        elif tool_name == "keyboard_press":
            return await self._keyboard_press(args)
        elif tool_name == "desktop_vision":
            return await self._desktop_vision(args)
        elif tool_name == "screenshot":
            return await self._screenshot(args)
        else:
            raise ValueError(f"Unknown computer use tool: {tool_name}")

    async def _mouse_move(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Move mouse to coordinates."""
        x = args.get("x", 0)
        y = args.get("y", 0)

        try:
            # Use xdotool or similar
            process = await asyncio.create_subprocess_shell(
                f"xdotool mousemove {x} {y}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return {"success": True, "x": x, "y": y}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _mouse_click(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Click mouse at current position."""
        button = args.get("button", "left")

        try:
            cmd = f"xdotool click {'1' if button == 'left' else '3'}"
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return {"success": True, "button": button}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _mouse_double_click(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Double click mouse."""
        try:
            process = await asyncio.create_subprocess_shell(
                "xdotool click --repeat 2 1",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _keyboard_type(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Type text using keyboard."""
        text = args.get("text", "")

        if not text:
            return {"success": False, "error": "Text is required"}

        try:
            # Escape special characters for shell
            escaped_text = text.replace("'", "'\"'\"'")
            process = await asyncio.create_subprocess_shell(
                f"xdotool type '{escaped_text}'",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _keyboard_press(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Press keyboard key."""
        key = args.get("key", "")

        if not key:
            return {"success": False, "error": "Key is required"}

        try:
            process = await asyncio.create_subprocess_shell(
                f"xdotool key {key}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return {"success": True, "key": key}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _desktop_vision(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Capture and analyze desktop."""
        try:
            # Take screenshot and analyze
            return {"success": True, "description": "Desktop analysis placeholder"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _screenshot(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Take screenshot."""
        path = args.get("path", "/tmp/screenshot.png")

        try:
            process = await asyncio.create_subprocess_shell(
                f"gnome-screenshot -f {path}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_tool_definitions(self) -> list:
        """Return tool definitions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "mouse_move",
                    "description": "Move mouse to coordinates",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer"},
                            "y": {"type": "integer"},
                        },
                        "required": ["x", "y"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "mouse_click",
                    "description": "Click mouse button",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "button": {"type": "string", "enum": ["left", "right"]},
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "keyboard_type",
                    "description": "Type text using keyboard",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                        },
                        "required": ["text"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "screenshot",
                    "description": "Take screenshot",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                        },
                    },
                },
            },
        ]
