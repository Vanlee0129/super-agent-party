"""CLI Tool Plugin.

Refactored from cli_tool.py
"""

import asyncio
import json
import logging
import os
import platform
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

from py.plugins.base import PluginMetadata
from py.tools.base import ToolPlugin

logger = logging.getLogger(__name__)


class CLIToolPlugin(ToolPlugin):
    """CLI tool plugin for command-line execution."""

    tool_name = "cli"

    def __init__(self) -> None:
        super().__init__()
        self.timeout = 30000
        self.allowed_commands: List[str] = []
        self._shell = os.environ.get('SHELL', '/bin/zsh')

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="tool.cli",
            name="CLI Tools",
            version="1.0.0",
            description="Command-line execution tools for shell commands",
        )

    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize CLI tools."""
        self.timeout = config.get("timeout", 30000)
        self.allowed_commands = config.get("allowed_commands", [])

    async def execute(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a CLI tool."""
        if tool_name == "bash":
            return await self._bash(args)
        elif tool_name == "python":
            return await self._python(args)
        elif tool_name == "node":
            return await self._node(args)
        elif tool_name == "get_env":
            return await self._get_env(args)
        elif tool_name == "cd":
            return await self._cd(args)
        else:
            raise ValueError(f"Unknown CLI tool: {tool_name}")

    async def _bash(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bash command."""
        command = args.get("command", "")
        cwd = args.get("cwd")

        if not command:
            return {"success": False, "error": "Command is required"}

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout / 1000
                )
            except asyncio.TimeoutError:
                process.kill()
                return {"success": False, "error": "Command timed out"}

            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "exit_code": process.returncode,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _python(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Run Python script."""
        code = args.get("code", "")

        if not code:
            return {"success": False, "error": "Code is required"}

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_path = f.name

            try:
                process = await asyncio.create_subprocess_shell(
                    f"python {temp_path}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout / 1000
                )

                return {
                    "success": process.returncode == 0,
                    "stdout": stdout.decode('utf-8', errors='replace'),
                    "stderr": stderr.decode('utf-8', errors='replace'),
                    "exit_code": process.returncode,
                }
            finally:
                os.unlink(temp_path)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _node(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Run Node.js script."""
        code = args.get("code", "")

        if not code:
            return {"success": False, "error": "Code is required"}

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_path = f.name

            try:
                process = await asyncio.create_subprocess_shell(
                    f"node {temp_path}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout / 1000
                )

                return {
                    "success": process.returncode == 0,
                    "stdout": stdout.decode('utf-8', errors='replace'),
                    "stderr": stderr.decode('utf-8', errors='replace'),
                    "exit_code": process.returncode,
                }
            finally:
                os.unlink(temp_path)
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_env(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get environment variables."""
        keys = args.get("keys", [])

        if not keys:
            return {"success": True, "env": dict(os.environ)}

        env = {k: os.environ.get(k, "") for k in keys}
        return {"success": True, "env": env}

    async def _cd(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Change working directory."""
        path = args.get("path", "")

        if not path:
            return {"success": False, "error": "Path is required"}

        try:
            os.chdir(path)
            return {"success": True, "cwd": os.getcwd()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_tool_definitions(self) -> list:
        """Return tool definitions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "bash",
                    "description": "Execute shell command",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                            "cwd": {"type": "string"},
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "python",
                    "description": "Run Python code",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                        },
                        "required": ["code"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "node",
                    "description": "Run Node.js code",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                        },
                        "required": ["code"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_env",
                    "description": "Get environment variables",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keys": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "cd",
                    "description": "Change working directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                        },
                        "required": ["path"],
                    },
                },
            },
        ]
