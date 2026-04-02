"""Task Tools Plugin.

Refactored from task_tools.py
"""

import logging
from typing import Any, Dict, List

from py.plugins.base import PluginMetadata
from py.tools.base import ToolPlugin

logger = logging.getLogger(__name__)


class TaskToolPlugin(ToolPlugin):
    """Task tools plugin for task management."""

    tool_name = "task"

    def __init__(self) -> None:
        super().__init__()
        self._tasks: Dict[str, Any] = {}

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="tool.task",
            name="Task Tools",
            version="1.0.0",
            description="Task management tools for creating and tracking tasks",
        )

    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize task tools."""
        self._tasks = {}

    async def execute(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task tool."""
        if tool_name == "create_task":
            return await self._create_task(args)
        elif tool_name == "get_task":
            return await self._get_task(args)
        elif tool_name == "list_tasks":
            return await self._list_tasks(args)
        elif tool_name == "update_task":
            return await self._update_task(args)
        elif tool_name == "delete_task":
            return await self._delete_task(args)
        else:
            raise ValueError(f"Unknown task tool: {tool_name}")

    async def _create_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task."""
        task_id = args.get("task_id", str(len(self._tasks) + 1))
        self._tasks[task_id] = {
            "id": task_id,
            "title": args.get("title", ""),
            "description": args.get("description", ""),
            "status": args.get("status", "pending"),
            "created_at": args.get("created_at"),
        }
        return {"success": True, "task": self._tasks[task_id]}

    async def _get_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get a task by ID."""
        task_id = args.get("task_id")
        task = self._tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        return {"success": True, "task": task}

    async def _list_tasks(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all tasks."""
        return {"success": True, "tasks": list(self._tasks.values())}

    async def _update_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update a task."""
        task_id = args.get("task_id")
        if task_id not in self._tasks:
            return {"success": False, "error": "Task not found"}
        self._tasks[task_id].update(args)
        return {"success": True, "task": self._tasks[task_id]}

    async def _delete_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a task."""
        task_id = args.get("task_id")
        if task_id not in self._tasks:
            return {"success": False, "error": "Task not found"}
        del self._tasks[task_id]
        return {"success": True}

    def get_tool_definitions(self) -> list:
        """Return tool definitions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_task",
                    "description": "Create a new task",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "status": {"type": "string"},
                        },
                        "required": ["task_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_task",
                    "description": "Get a task by ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string"},
                        },
                        "required": ["task_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_tasks",
                    "description": "List all tasks",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]
