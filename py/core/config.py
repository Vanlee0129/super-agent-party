"""Centralized configuration management for Super Agent Party."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from appdirs import user_data_dir

# ----------------- 1. Basic Environment Detection -----------------
APP_NAME = "Super-Agent-Party"
IS_DOCKER = os.environ.get("IS_DOCKER", "").lower() in ("1", "true")

# Host and port settings
HOST: Optional[str] = None
PORT: Optional[int] = None


def get_base_path() -> str:
    """Get the base path of the application."""
    import sys

    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.abspath(".")


base_path = get_base_path()

# ----------------- 2. Path Definitions -----------------
if IS_DOCKER:
    USER_DATA_DIR = "/app/data"
else:
    USER_DATA_DIR = user_data_dir(APP_NAME, roaming=True)

# Core directories
DATABASE_PATH = os.path.join(USER_DATA_DIR, "super_agent_party.db")
MEMORY_CACHE_DIR = os.path.join(USER_DATA_DIR, "memory_cache")
UPLOAD_FILES_DIR = os.path.join(USER_DATA_DIR, "uploaded_files")
AGENT_DIR = os.path.join(USER_DATA_DIR, "agents")
KB_DIR = os.path.join(USER_DATA_DIR, "kb")
DEFAULT_VRM_DIR = os.path.join(base_path, "vrm")


def get_global_skills_dir() -> str:
    """Get the standard global skills directory, cross-platform."""
    if IS_DOCKER:
        docker_skills_dir = Path("/app/.agents/skills")
        docker_skills_dir.mkdir(parents=True, exist_ok=True)
        return str(docker_skills_dir)

    global_skills_dir = Path.home() / ".agents" / "skills"
    global_skills_dir.mkdir(parents=True, exist_ok=True)
    return str(global_skills_dir)


SKILLS_DIR = get_global_skills_dir()

# Extensions directory (in user data dir)
EXTENSIONS_DIR = os.path.join(USER_DATA_DIR, "ext")


# Ensure all directories exist
def _ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    dirs_to_create = [
        USER_DATA_DIR,
        MEMORY_CACHE_DIR,
        UPLOAD_FILES_DIR,
        AGENT_DIR,
        KB_DIR,
        EXTENSIONS_DIR,
        SKILLS_DIR,
    ]
    for d in set(dirs_to_create):
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass


_ensure_directories()


# ----------------- 3. Config Class -----------------
class Config:
    """Centralized configuration management with JSON persistence."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}
        self._host: Optional[str] = HOST
        self._port: Optional[int] = PORT

    @property
    def host(self) -> Optional[str]:
        return self._host or "127.0.0.1"

    @property
    def port(self) -> Optional[int]:
        return self._port or 3456

    def set_host_port(self, host: Optional[str], port: Optional[int]) -> None:
        """Update host and port settings."""
        self._host = host
        self._port = port

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._data[key] = value

    def update(self, data: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        self._data.update(data)

    def load_from_file(self, filepath: Optional[str] = None) -> None:
        """Load configuration from a JSON file."""
        if filepath is None:
            filepath = os.path.join(USER_DATA_DIR, "config.json")

        if not os.path.exists(filepath):
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except Exception:
            pass

    def save_to_file(self, filepath: Optional[str] = None) -> None:
        """Save configuration to a JSON file."""
        if filepath is None:
            filepath = os.path.join(USER_DATA_DIR, "config.json")

        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary."""
        return self._data.copy()


# Global config instance
config = Config()
