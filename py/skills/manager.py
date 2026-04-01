"""
SkillManager - Manages skill lifecycle.

Provides high-level API for loading, querying, and executing skills.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from py.skills.scanner import SkillScanner
from py.skills.runner import SkillRunner
from py.skills.schemas import SkillManifest, SkillExecution

logger = logging.getLogger(__name__)


class SkillManager:
    """Manages skills - loading, querying, and execution."""

    def __init__(self, skills_dir: Path):
        """
        Initialize the skill manager.

        Args:
            skills_dir: Root directory containing skill subdirectories
        """
        self.skills_dir = Path(skills_dir)
        self.scanner = SkillScanner(skills_dir)
        self.runner = SkillRunner(skills_dir)
        self._manifests: Dict[str, SkillManifest] = {}
        self._execution_history: Dict[str, List[SkillExecution]] = {}

    def load_all(self) -> List[SkillManifest]:
        """
        Scan and load all skills.

        Returns:
            List of loaded SkillManifest objects
        """
        manifests = self.scanner.scan_all()
        self._manifests = {m.metadata.id: m for m in manifests}
        logger.info(f"Loaded {len(manifests)} skills")
        return manifests

    def get(self, skill_id: str) -> Optional[SkillManifest]:
        """
        Get a skill manifest by ID.

        Args:
            skill_id: The skill identifier

        Returns:
            SkillManifest or None if not found
        """
        return self._manifests.get(skill_id)

    def list_all(self) -> List[SkillManifest]:
        """
        List all loaded skills.

        Returns:
            List of all SkillManifest objects
        """
        return list(self._manifests.values())

    def list_by_category(self, category: str) -> List[SkillManifest]:
        """
        List skills in a specific category.

        Args:
            category: Category to filter by

        Returns:
            List of skills in the category
        """
        return [
            m for m in self._manifests.values()
            if m.metadata.category == category
        ]

    async def execute(
        self,
        skill_id: str,
        parameters: Dict[str, Any]
    ) -> SkillExecution:
        """
        Execute a skill.

        Args:
            skill_id: The skill identifier
            parameters: Parameters to pass to the skill

        Returns:
            SkillExecution with results
        """
        manifest = self.get(skill_id)
        if manifest is None:
            execution = SkillExecution(
                skill_id=skill_id,
                parameters=parameters,
            )
            execution.error = f"Skill '{skill_id}' not found"
            execution.completed_at = datetime.utcnow()
            return execution

        execution = await self.runner.run(manifest, parameters)

        # Store in history
        if skill_id not in self._execution_history:
            self._execution_history[skill_id] = []
        self._execution_history[skill_id].append(execution)

        return execution

    def get_execution(self, skill_id: str) -> List[SkillExecution]:
        """
        Get execution history for a skill.

        Args:
            skill_id: The skill identifier

        Returns:
            List of SkillExecution objects, oldest first
        """
        return self._execution_history.get(skill_id, [])
