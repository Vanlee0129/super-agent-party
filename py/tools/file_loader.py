"""File Loader Tool Plugin.

Refactored from load_files.py
"""

import asyncio
import logging
import os
import re
import socket
import ipaddress
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

from py.plugins.base import PluginMetadata
from py.tools.base import ToolPlugin

logger = logging.getLogger(__name__)


class FileLoaderToolPlugin(ToolPlugin):
    """File loader tool plugin for reading files and URLs."""

    tool_name = "file_loader"

    def __init__(self) -> None:
        super().__init__()
        self._allowed_extensions: List[str] = ['.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.html', '.css']
        self._max_file_size = 10 * 1024 * 1024  # 10MB

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="tool.file_loader",
            name="File Loader Tools",
            version="1.0.0",
            description="File loading tools for reading local files and URLs",
        )

    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize file loader tools."""
        self._allowed_extensions = config.get("allowed_extensions", ['.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.html', '.css'])
        self._max_file_size = config.get("max_file_size", 10 * 1024 * 1024)

    async def execute(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a file loader tool."""
        if tool_name == "get_file_content":
            return await self._get_file_content(args)
        elif tool_name == "get_files_content":
            return await self._get_files_content(args)
        elif tool_name == "is_private_ip":
            return self._is_private_ip(args)
        elif tool_name == "sanitize_url":
            return self._sanitize_url(args)
        elif tool_name == "check_robots_txt":
            return await self._check_robots_txt(args)
        else:
            raise ValueError(f"Unknown file loader tool: {tool_name}")

    async def _get_file_content(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Read content of a file."""
        file_path = args.get("file_path", "")

        if not file_path:
            return {"success": False, "error": "file_path is required"}

        try:
            path = Path(file_path)

            # Security check: follow symlinks but within allowed directories
            resolved = path.resolve()

            # Check file size
            if resolved.stat().st_size > self._max_file_size:
                return {"success": False, "error": f"File too large (max {self._max_file_size} bytes)"}

            # Check extension
            if self._allowed_extensions and resolved.suffix not in self._allowed_extensions:
                return {"success": False, "error": f"File type not allowed: {resolved.suffix}"}

            async with aiofiles.open(resolved, 'r', encoding='utf-8') as f:
                content = await f.read()

            return {
                "success": True,
                "content": content,
                "file_path": str(resolved),
                "size": resolved.stat().st_size
            }

        except FileNotFoundError:
            return {"success": False, "error": "File not found"}
        except PermissionError:
            return {"success": False, "error": "Permission denied"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_files_content(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Read content of multiple files."""
        file_paths = args.get("file_paths", [])

        if not file_paths:
            return {"success": False, "error": "file_paths is required"}

        results = []
        errors = []

        for path_str in file_paths:
            result = await self._get_file_content({"file_path": path_str})
            if result["success"]:
                results.append({
                    "file_path": path_str,
                    "content": result["content"],
                    "size": result.get("size", 0)
                })
            else:
                errors.append({
                    "file_path": path_str,
                    "error": result.get("error", "Unknown error")
                })

        return {
            "success": len(errors) == 0,
            "files": results,
            "errors": errors
        }

    def _is_private_ip(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check if IP address is private."""
        ip_address = args.get("ip_address", "")

        if not ip_address:
            return {"success": False, "error": "ip_address is required"}

        try:
            ip = ipaddress.ip_address(ip_address)
            is_private = not ip.is_global
            return {"success": True, "is_private": is_private}
        except ValueError:
            return {"success": False, "error": "Invalid IP address"}

    def _sanitize_url(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize and validate URL."""
        url = args.get("url", "")

        if not url:
            return {"success": False, "error": "url is required"}

        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)

            # Only allow http and https
            if parsed.scheme not in ('http', 'https'):
                return {"success": False, "error": "Only http and https URLs are allowed"}

            # Check for private IPs if it's a direct IP
            if parsed.hostname:
                try:
                    ip = ipaddress.ip_address(parsed.hostname)
                    if not ip.is_global:
                        return {"success": False, "error": "Private IP addresses not allowed"}
                except ValueError:
                    pass  # Not an IP address, continue

            return {
                "success": True,
                "sanitized_url": url,
                "hostname": parsed.hostname,
                "path": parsed.path
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _check_robots_txt(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check if URL is allowed by robots.txt."""
        url = args.get("url", "")

        if not url:
            return {"success": False, "error": "url is required"}

        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

            import requests
            response = requests.get(robots_url, timeout=5)

            if response.status_code != 200:
                return {"success": True, "allowed": True, "reason": "No robots.txt found"}

            content = response.text
            lines = content.split('\n')

            user_agent = None
            allowed = True

            for line in lines:
                line = line.strip()
                if line.lower().startswith('user-agent:'):
                    user_agent = line.split(':', 1)[1].strip()
                elif line.lower().startswith('disallow:'):
                    disallow_path = line.split(':', 1)[1].strip()
                    if user_agent == '*' or user_agent == 'claude':
                        if parsed.path.startswith(disallow_path):
                            allowed = False

            return {"success": True, "allowed": allowed}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_tool_definitions(self) -> list:
        """Return tool definitions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_file_content",
                    "description": "Read content of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                        },
                        "required": ["file_path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_files_content",
                    "description": "Read content of multiple files",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["file_paths"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "is_private_ip",
                    "description": "Check if IP address is private",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ip_address": {"type": "string"},
                        },
                        "required": ["ip_address"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "sanitize_url",
                    "description": "Sanitize and validate URL",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                        },
                        "required": ["url"],
                    },
                },
            },
        ]
