"""
SkillScanner - Scans directories for skill manifests.

Scans skill directories and parses SKILL.md YAML frontmatter to build SkillManifest objects.
"""

import logging
import re
from pathlib import Path
from typing import List, Optional

import yaml

from py.skills.schemas import SkillManifest, SkillMetadata, SkillParameter

logger = logging.getLogger(__name__)


class SkillScanner:
    """Scans directories for skills and parses their manifests."""

    def __init__(self, skills_dir: Path):
        """
        Initialize the scanner.

        Args:
            skills_dir: Root directory containing skill subdirectories
        """
        self.skills_dir = Path(skills_dir)

    def scan_all(self) -> List[SkillManifest]:
        """
        Scan all skill directories.

        Returns:
            List of SkillManifest objects found
        """
        manifests = []

        if not self.skills_dir.exists():
            logger.warning(f"Skills directory does not exist: {self.skills_dir}")
            return manifests

        for item in self.skills_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                try:
                    manifest = self.scan_skill(item)
                    if manifest is not None:
                        manifests.append(manifest)
                except Exception as e:
                    logger.error(f"Error scanning skill {item.name}: {e}")

        return manifests

    def scan_skill(self, skill_path: Path) -> Optional[SkillManifest]:
        """
        Scan a single skill directory.

        Args:
            skill_path: Path to the skill directory

        Returns:
            SkillManifest or None if not a valid skill
        """
        skill_path = Path(skill_path)

        if not skill_path.exists() or not skill_path.is_dir():
            return None

        # Find SKILL.md file
        skill_md = None
        for name in ["SKILL.md", "skill.md", "SKILLS.md", "skills.md"]:
            candidate = skill_path / name
            if candidate.exists() and candidate.is_file():
                skill_md = candidate
                break

        if skill_md is None:
            return None

        try:
            content = skill_md.read_text(encoding="utf-8")
            return self._parse_skill_md(content, skill_path)
        except Exception as e:
            logger.error(f"Error reading skill file {skill_md}: {e}")
            return None

    def _parse_skill_md(self, content: str, skill_path: Path) -> Optional[SkillManifest]:
        """
        Parse SKILL.md YAML frontmatter.

        Args:
            content: Raw file content
            skill_path: Path to the skill directory

        Returns:
            SkillManifest parsed from frontmatter
        """
        # Extract YAML frontmatter between --- markers
        match = re.search(r'^\s*---\s*\n(.*?)\n---\s*', content, re.DOTALL | re.MULTILINE)

        meta = {}
        description = ""
        remaining_content = content

        if match:
            yaml_text = match.group(1).strip()
            remaining_content = content[match.end():]
            try:
                meta = yaml.safe_load(yaml_text) or {}
            except yaml.YAMLError as e:
                logger.warning(f"YAML parse error in {skill_path}/SKILL.md: {e}")

        # Extract description from content after frontmatter
        desc_match = re.search(r'^#\s+(.+?)\n', remaining_content, re.MULTILINE)
        if desc_match:
            description = desc_match.group(1).strip()

        # Build metadata
        metadata = SkillMetadata(
            id=skill_path.name,
            name=meta.get("name", skill_path.name),
            description=meta.get("description", description),
            version=str(meta.get("version", "1.0.0")),
            author=meta.get("author", "unknown"),
            tags=meta.get("tags", []),
            category=meta.get("category", "general"),
        )

        # Parse parameters
        parameters = []
        for param in meta.get("parameters", []):
            if isinstance(param, dict):
                parameters.append(SkillParameter(
                    name=param.get("name", ""),
                    type=param.get("type", "string"),
                    description=param.get("description", ""),
                    required=param.get("required", False),
                    default=param.get("default"),
                ))

        # Build scripts dict from files
        scripts = {}
        for file_path in skill_path.iterdir():
            if file_path.is_file() and not file_path.name.startswith('.'):
                scripts[file_path.name] = str(file_path)

        return SkillManifest(
            metadata=metadata,
            parameters=parameters,
            scripts=scripts,
            references=meta.get("references", []),
        )
