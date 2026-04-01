"""
SkillRunner - Executes skill scripts.

Runs skill scripts (Python, Shell, Node.js) using asyncio subprocess execution.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from py.skills.schemas import SkillManifest, SkillExecution

logger = logging.getLogger(__name__)


class SkillRunner:
    """Executes skill scripts."""

    def __init__(self, skills_dir: Path):
        """
        Initialize the runner.

        Args:
            skills_dir: Root directory containing skill subdirectories
        """
        self.skills_dir = Path(skills_dir)

    async def run(
        self,
        manifest: SkillManifest,
        parameters: Dict[str, Any],
        script_name: str = "run"
    ) -> SkillExecution:
        """
        Execute a skill script.

        Args:
            manifest: The skill manifest
            parameters: Parameters to pass to the script
            script_name: Name of the script to run (default: 'run')

        Returns:
            SkillExecution with results
        """
        execution = SkillExecution(
            skill_id=manifest.metadata.id,
            parameters=parameters,
        )

        # Find the script file
        script_path = None
        for ext in ["", ".py", ".sh", ".js"]:
            candidate = self.skills_dir / manifest.metadata.id / f"{script_name}{ext}"
            if candidate.exists():
                script_path = candidate
                break

        if script_path is None:
            execution.error = f"Script '{script_name}' not found"
            return execution

        try:
            result = await self._execute_script(script_path, parameters)
            execution.result = result
            execution.completed_at = asyncio.get_event_loop().time()
        except Exception as e:
            execution.error = str(e)
            logger.exception(f"Error executing skill {manifest.metadata.id}")

        return execution

    async def _execute_script(
        self,
        script_path: Path,
        parameters: Dict[str, Any]
    ) -> Any:
        """
        Execute a script based on file extension.

        Args:
            script_path: Path to the script
            parameters: Parameters to pass

        Returns:
            Script output
        """
        suffix = script_path.suffix.lower()

        if suffix == ".py":
            return await self._run_python(script_path, parameters)
        elif suffix == ".sh":
            return await self._run_shell(script_path, parameters)
        elif suffix == ".js":
            return await self._run_node(script_path, parameters)
        else:
            # Try to execute as shell script
            return await self._run_shell(script_path, parameters)

    async def _run_python(
        self,
        script_path: Path,
        parameters: Dict[str, Any]
    ) -> Any:
        """Run a Python script."""
        args = [str(script_path)]
        for key, value in parameters.items():
            args.append(f"--{key}={value}")

        proc = await asyncio.create_subprocess_exec(
            "python",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"Script failed: {stderr.decode()}")

        return stdout.decode() if stdout else None

    async def _run_shell(
        self,
        script_path: Path,
        parameters: Dict[str, Any]
    ) -> Any:
        """Run a shell script."""
        # Build environment with parameters
        env = {**__import__("os").environ}
        for key, value in parameters.items():
            env[f"SKILL_PARAM_{key.upper()}"] = str(value)

        proc = await asyncio.create_subprocess_exec(
            "bash",
            str(script_path),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"Script failed: {stderr.decode()}")

        return stdout.decode() if stdout else None

    async def _run_node(
        self,
        script_path: Path,
        parameters: Dict[str, Any]
    ) -> Any:
        """Run a Node.js script."""
        args = [str(script_path)]
        for key, value in parameters.items():
            args.append(f"--{key}={value}")

        proc = await asyncio.create_subprocess_exec(
            "node",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"Script failed: {stderr.decode()}")

        return stdout.decode() if stdout else None
