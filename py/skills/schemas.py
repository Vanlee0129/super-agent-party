"""
Skill schemas for the Skills management system.

Defines the core dataclasses for skill metadata, parameters, execution, and manifests.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class SkillMetadata:
    """Metadata for a skill."""
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = "unknown"
    tags: List[str] = field(default_factory=list)
    category: str = "general"


@dataclass
class SkillParameter:
    """A parameter for a skill."""
    name: str
    type: str = "string"
    description: str = ""
    required: bool = False
    default: Any = None


@dataclass
class SkillManifest:
    """Manifest describing a skill's structure and contents."""
    metadata: SkillMetadata
    parameters: List[SkillParameter] = field(default_factory=list)
    scripts: Dict[str, str] = field(default_factory=dict)
    references: List[str] = field(default_factory=list)


@dataclass
class SkillExecution:
    """Records a skill execution instance."""
    skill_id: str
    parameters: Dict[str, Any]
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
