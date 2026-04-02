"""Task orchestration layer - self-contained TaskCenter implementation."""

import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any

import aiofiles
import aiofiles.os
from pydantic import BaseModel, Field

from .models import Task, TaskStatus


class SubTask(BaseModel):
    """Internal task model matching TaskCenter's SubTask."""
    task_id: str
    parent_task_id: Optional[str] = None
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = Field(default=0, ge=0, le=100)
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    agent_type: str = "default"
    context: Dict[str, Any] = Field(default_factory=dict)


class TaskCenter:
    """Task center - manages all tasks and subtasks."""

    def __init__(self, workspace_dir: str):
        self.workspace_dir = Path(workspace_dir)
        self.task_dir = self.workspace_dir / ".agent" / "tasks"
        self._lock = asyncio.Lock()
        self._ensure_task_dir()

    def _ensure_task_dir(self):
        """Ensure task directory exists."""
        self.task_dir.mkdir(parents=True, exist_ok=True)

    def _get_task_file(self, task_id: str) -> Path:
        """Get task file path."""
        return self.task_dir / f"{task_id}.json"

    async def create_task(
        self,
        title: str,
        description: str,
        parent_task_id: Optional[str] = None,
        agent_type: str = "default",
        context: Optional[Dict[str, Any]] = None
    ) -> SubTask:
        """Create a new task."""
        async with self._lock:
            task_id = str(uuid.uuid4())[:8]
            now = datetime.now().isoformat()

            task = SubTask(
                task_id=task_id,
                parent_task_id=parent_task_id,
                title=title,
                description=description,
                created_at=now,
                updated_at=now,
                agent_type=agent_type,
                context=context or {}
            )

            await self._save_task(task)
            return task

    async def _save_task(self, task: SubTask):
        """Save task to file."""
        task_file = self._get_task_file(task.task_id)
        async with aiofiles.open(task_file, 'w', encoding='utf-8') as f:
            await f.write(task.model_dump_json(indent=2))

    async def get_task(self, task_id: str) -> Optional[SubTask]:
        """Get task details."""
        task_file = self._get_task_file(task_id)
        if not task_file.exists():
            return None

        try:
            async with aiofiles.open(task_file, 'r', encoding='utf-8') as f:
                data = await f.read()
                return SubTask.model_validate_json(data)
        except Exception as e:
            print(f"Error loading task {task_id}: {e}")
            return None

    async def update_task_progress(
        self,
        task_id: str,
        progress: int,
        status: Optional[TaskStatus] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update task progress and context."""
        async with self._lock:
            task = await self.get_task(task_id)
            if not task:
                return False

            # Progress calculation logic
            safe_progress = max(0, min(100, progress))
            target_status = status if status else task.status

            if target_status == TaskStatus.COMPLETED:
                final_progress = 100
            elif target_status == TaskStatus.FAILED:
                final_progress = max(task.progress, safe_progress)
            elif target_status == TaskStatus.CANCELLED:
                final_progress = task.progress
            else:
                final_progress = max(task.progress, safe_progress)
                final_progress = min(99, final_progress)

            task.progress = final_progress
            task.updated_at = datetime.now().isoformat()

            if status:
                task.status = status
                if status == TaskStatus.RUNNING and not task.started_at:
                    task.started_at = datetime.now().isoformat()
                elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    task.completed_at = datetime.now().isoformat()

            if result is not None:
                task.result = result

            if error is not None:
                task.error = error
                task.status = TaskStatus.FAILED

            if context is not None:
                task.context.update(context)

            await self._save_task(task)
            return True

    async def list_tasks(
        self,
        parent_task_id: Optional[str] = None,
        status: Optional[TaskStatus] = None
    ) -> List[SubTask]:
        """List tasks."""
        tasks = []

        if not self.task_dir.exists():
            return tasks

        files = list(self.task_dir.glob("*.json"))

        for task_file in files:
            try:
                async with aiofiles.open(task_file, 'r', encoding='utf-8') as f:
                    data = await f.read()
                    task = SubTask.model_validate_json(data)

                    if parent_task_id is not None and task.parent_task_id != parent_task_id:
                        continue
                    if status is not None and task.status != status:
                        continue

                    tasks.append(task)
            except Exception as e:
                print(f"Error loading task file {task_file}: {e}")
                continue

        tasks.sort(key=lambda x: x.created_at, reverse=True)
        return tasks

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        return await self.update_task_progress(
            task_id=task_id,
            progress=0,
            status=TaskStatus.CANCELLED
        )

    async def delete_task(self, task_id: str) -> bool:
        """Delete task file."""
        async with self._lock:
            task_file = self._get_task_file(task_id)
            if task_file.exists():
                try:
                    await aiofiles.os.remove(task_file)
                    return True
                except Exception as e:
                    print(f"Error deleting task {task_id}: {e}")
                    return False
            return False

    async def cleanup_old_tasks(self, days: int = 7):
        """Cleanup old tasks (not yet implemented)."""
        pass


# --- Global TaskCenter instance management ---

_task_centers: Dict[str, TaskCenter] = {}


async def get_task_center(workspace_dir: str) -> TaskCenter:
    """Get or create a TaskCenter instance."""
    if workspace_dir not in _task_centers:
        _task_centers[workspace_dir] = TaskCenter(workspace_dir)
    return _task_centers[workspace_dir]


# --- TaskOrchestrator (existing wrapper for API) ---


class TaskOrchestrator:
    """Orchestrates tasks using the TaskCenter backend."""

    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        self._task_center: Optional[TaskCenter] = None

    async def _get_center(self) -> TaskCenter:
        """Get or create the TaskCenter instance."""
        if self._task_center is None:
            self._task_center = await get_task_center(self.workspace_dir)
        return self._task_center

    async def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        parent_id: Optional[str] = None
    ) -> List[Task]:
        """List tasks with optional filtering."""
        center = await self._get_center()

        tc_status = None
        if status:
            tc_status = TaskStatus(status.value)

        tc_tasks = await center.list_tasks(
            parent_task_id=parent_id,
            status=tc_status
        )

        return [self._convert_task(tc_task) for tc_task in tc_tasks]

    async def create_task(
        self,
        title: str,
        description: str = "",
        parent_task_id: Optional[str] = None,
        agent_type: str = "default",
        context: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Create a new task."""
        center = await self._get_center()

        tc_task = await center.create_task(
            title=title,
            description=description,
            parent_task_id=parent_task_id,
            agent_type=agent_type,
            context=context
        )

        return self._convert_task(tc_task)

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task details by ID."""
        center = await self._get_center()
        tc_task = await center.get_task(task_id)

        if tc_task is None:
            return None

        return self._convert_task(tc_task)

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        center = await self._get_center()
        return await center.delete_task(task_id)

    async def cancel_task(self, task_id: str) -> Optional[Task]:
        """Cancel a running task."""
        center = await self._get_center()
        success = await center.cancel_task(task_id)

        if not success:
            return None

        tc_task = await center.get_task(task_id)
        return self._convert_task(tc_task) if tc_task else None

    async def get_progress(self, task_id: str) -> Dict[str, Any]:
        """Get task progress details."""
        center = await self._get_center()
        tc_task = await center.get_task(task_id)

        if tc_task is None:
            return {"error": "Task not found"}

        return {
            "task_id": tc_task.task_id,
            "progress": tc_task.progress,
            "status": tc_task.status.value,
            "result": tc_task.result,
        }

    def _convert_task(self, tc_task: SubTask) -> Task:
        """Convert TaskCenter SubTask to API Task model."""
        return Task(
            task_id=tc_task.task_id,
            parent_task_id=tc_task.parent_task_id,
            title=tc_task.title,
            description=tc_task.description,
            status=TaskStatus(tc_task.status.value),
            progress=tc_task.progress,
            result=tc_task.result,
            context=tc_task.context,
            agent_type=tc_task.agent_type,
            created_at=self._datetime_to_timestamp(tc_task.created_at),
            updated_at=self._datetime_to_timestamp(tc_task.updated_at),
        )

    def _datetime_to_timestamp(self, dt_str: str) -> float:
        """Convert ISO datetime string to timestamp."""
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(dt_str)
            return dt.timestamp()
        except (ValueError, TypeError):
            return asyncio.get_event_loop().time()


# Global orchestrator instance
_task_orchestrator: Optional[TaskOrchestrator] = None
_default_workspace: str = ""


def get_task_orchestrator(workspace_dir: str = None) -> TaskOrchestrator:
    """Get or create the global task orchestrator instance."""
    global _task_orchestrator, _default_workspace

    if workspace_dir:
        _default_workspace = workspace_dir

    if _task_orchestrator is None or not _default_workspace:
        if not _default_workspace:
            _default_workspace = "/tmp"
        _task_orchestrator = TaskOrchestrator(_default_workspace)

    return _task_orchestrator
