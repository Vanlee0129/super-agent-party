"""Task Management API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any

from .models import Task, TaskStatus, CreateTaskRequest, TaskProgress
from .manager import get_task_orchestrator

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


def _get_orchestrator() -> Any:
    """Get the task orchestrator instance."""
    return get_task_orchestrator()


@router.get("/", response_model=List[Task])
async def list_tasks(
    status: Optional[TaskStatus] = None,
    parent_id: Optional[str] = None
) -> List[Task]:
    """List tasks with optional filtering by status and parent ID."""
    orchestrator = _get_orchestrator()
    return await orchestrator.list_tasks(status=status, parent_id=parent_id)


@router.post("/", response_model=Task)
async def create_task(request: CreateTaskRequest) -> Task:
    """Create a new task."""
    orchestrator = _get_orchestrator()
    return await orchestrator.create_task(
        title=request.title,
        description=request.description,
        parent_task_id=request.parent_task_id,
        agent_type=request.agent_type,
        context=request.context
    )


@router.get("/{task_id}", response_model=Task)
async def get_task(task_id: str) -> Task:
    """Get task details by ID."""
    orchestrator = _get_orchestrator()
    task = await orchestrator.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return task


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Delete a task."""
    orchestrator = _get_orchestrator()
    success = await orchestrator.delete_task(task_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return {"success": True, "message": f"Task {task_id} deleted"}


@router.post("/{task_id}/cancel", response_model=Task)
async def cancel_task(task_id: str) -> Task:
    """Cancel a running task."""
    orchestrator = _get_orchestrator()
    task = await orchestrator.cancel_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    return task


@router.get("/{task_id}/progress")
async def get_progress(task_id: str) -> Dict[str, Any]:
    """Get task progress details."""
    orchestrator = _get_orchestrator()
    progress = await orchestrator.get_progress(task_id)

    if "error" in progress:
        raise HTTPException(status_code=404, detail=progress["error"])

    return progress
