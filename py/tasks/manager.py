"""Task orchestration layer over TaskCenter."""

from typing import Optional, List, Dict, Any
import time

from py.task_center import TaskCenter, TaskStatus as TCStatus, get_task_center
from .models import Task, TaskStatus


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

        # Convert API TaskStatus to TaskCenter TaskStatus
        tc_status = None
        if status:
            tc_status = TCStatus(status.value)

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

    def _convert_task(self, tc_task) -> Task:
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
            return time.time()


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
