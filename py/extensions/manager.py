"""Extension lifecycle management."""
import json
import os
import shutil
import stat
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

from py.get_setting import EXT_DIR
from py.extensions.validator import ManifestValidator


class ExtensionStatus(str, Enum):
    """Extension status enumeration."""
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class Extension:
    """Represents an installed extension."""
    
    def __init__(
        self,
        ext_id: str,
        name: str,
        description: str = "No description",
        version: str = "1.0.0",
        author: str = "Unknown",
        systemPrompt: str = "",
        repository: str = "",
        backupRepository: str = "",
        category: str = "",
        transparent: bool = False,
        width: int = 800,
        height: int = 600,
        enableVrmWindowSize: bool = False,
        status: ExtensionStatus = ExtensionStatus.INSTALLED,
        config: Dict[str, Any] = None
    ):
        self.id = ext_id
        self.name = name
        self.description = description
        self.version = version
        self.author = author
        self.systemPrompt = systemPrompt
        self.repository = repository
        self.backupRepository = backupRepository
        self.category = category
        self.transparent = transparent
        self.width = width
        self.height = height
        self.enableVrmWindowSize = enableVrmWindowSize
        self.status = status
        self.config = config or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "systemPrompt": self.systemPrompt,
            "repository": self.repository,
            "backupRepository": self.backupRepository,
            "category": self.category,
            "transparent": self.transparent,
            "width": self.width,
            "height": self.height,
            "enableVrmWindowSize": self.enableVrmWindowSize,
            "status": self.status.value if isinstance(self.status, ExtensionStatus) else self.status,
            "config": self.config
        }
    
    @classmethod
    def from_directory(cls, ext_id: str, ext_dir: Path) -> Optional["Extension"]:
        """Load extension from directory."""
        manifest = ManifestValidator.get_manifest_from_directory(ext_dir)
        if not manifest:
            return None
        
        return cls(
            ext_id=ext_id,
            name=manifest.get("name", ext_id),
            description=manifest.get("description", "No description"),
            version=manifest.get("version", "1.0.0"),
            author=manifest.get("author", "Unknown"),
            systemPrompt=manifest.get("systemPrompt", ""),
            repository=manifest.get("repository", ""),
            backupRepository=manifest.get("backupRepository", ""),
            category=manifest.get("category", ""),
            transparent=manifest.get("transparent", False),
            width=manifest.get("width", 800),
            height=manifest.get("height", 600),
            enableVrmWindowSize=manifest.get("enableVrmWindowSize", False)
        )


class ExtensionManager:
    """Manages extension lifecycle operations."""
    
    def __init__(self, extensions_dir: str = None):
        self.extensions_dir = Path(extensions_dir or EXT_DIR)
        self._enabled_extensions: Dict[str, bool] = {}  # ext_id -> enabled
        self._extension_configs: Dict[str, Dict[str, Any]] = {}  # ext_id -> config
    
    def list_all(self) -> List[Extension]:
        """List all installed extensions."""
        if not self.extensions_dir.exists():
            return []
        
        extensions = []
        for dir_name in os.listdir(self.extensions_dir):
            dir_path = self.extensions_dir / dir_name
            if dir_path.is_dir():
                ext = Extension.from_directory(dir_name, dir_path)
                if ext:
                    ext.status = self._get_extension_status(dir_name)
                    ext.config = self._extension_configs.get(dir_name, {})
                    extensions.append(ext)
        
        return extensions
    
    def get(self, ext_id: str) -> Optional[Extension]:
        """Get a specific extension by ID."""
        ext_dir = self.extensions_dir / ext_id
        if not ext_dir.exists():
            return None
        
        ext = Extension.from_directory(ext_id, ext_dir)
        if ext:
            ext.status = self._get_extension_status(ext_id)
            ext.config = self._extension_configs.get(ext_id, {})
        return ext
    
    def _get_extension_status(self, ext_id: str) -> ExtensionStatus:
        """Get the status of an extension."""
        if ext_id in self._enabled_extensions and self._enabled_extensions[ext_id]:
            return ExtensionStatus.ENABLED
        return ExtensionStatus.DISABLED
    
    def enable(self, ext_id: str) -> bool:
        """Enable an extension."""
        ext_dir = self.extensions_dir / ext_id
        if not ext_dir.exists():
            return False
        self._enabled_extensions[ext_id] = True
        return True
    
    def disable(self, ext_id: str) -> bool:
        """Disable an extension."""
        ext_dir = self.extensions_dir / ext_id
        if not ext_dir.exists():
            return False
        self._enabled_extensions[ext_id] = False
        return True
    
    def is_enabled(self, ext_id: str) -> bool:
        """Check if an extension is enabled."""
        return self._enabled_extensions.get(ext_id, True)
    
    def get_config(self, ext_id: str) -> Dict[str, Any]:
        """Get extension configuration."""
        return self._extension_configs.get(ext_id, {})
    
    def update_config(self, ext_id: str, config: Dict[str, Any]) -> bool:
        """Update extension configuration."""
        ext_dir = self.extensions_dir / ext_id
        if not ext_dir.exists():
            return False
        self._extension_configs[ext_id] = config
        return True
    
    def delete(self, ext_id: str) -> bool:
        """Delete an extension."""
        ext_dir = self.extensions_dir / ext_id
        if not ext_dir.exists():
            return False
        
        # Remove read-only files on Windows
        if os.name == 'nt':
            for root, dirs, files in os.walk(ext_dir):
                for name in files:
                    try:
                        os.chmod(Path(root) / name, stat.S_IWRITE)
                    except Exception:
                        pass
        
        try:
            shutil.rmtree(ext_dir)
            self._enabled_extensions.pop(ext_id, None)
            self._extension_configs.pop(ext_id, None)
            return True
        except Exception:
            return False
    
    def exists(self, ext_id: str) -> bool:
        """Check if an extension exists."""
        return (self.extensions_dir / ext_id).exists()
