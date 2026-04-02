"""Task models."""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """Task model matching the API specification."""
    task_id: str
    parent_task_id: Optional[str] = None
    title: str
    description: str
    status: TaskStatus
    progress: int = Field(default=0, ge=0, le=100)
    result: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    agent_type: str = "default"
    created_at: float
    updated_at: float


class CreateTaskRequest(BaseModel):
    """Request model for creating a new task."""
    title: str
    description: str = ""
    parent_task_id: Optional[str] = None
    agent_type: str = "default"
    context: Dict[str, Any] = Field(default_factory=dict)


class TaskProgress(BaseModel):
    """Task progress response model."""
    task_id: str
    progress: int
    status: TaskStatus
    message: Optional[str] = None
