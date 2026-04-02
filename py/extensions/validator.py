"""Manifest validation for extension packages."""
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ManifestValidator:
    """Validates extension manifests (package.json)."""
    
    REQUIRED_FIELDS = ["name", "version"]
    OPTIONAL_FIELDS = [
        "description", "author", "systemPrompt", "repository", 
        "backupRepository", "category", "transparent", "width", 
        "height", "enableVrmWindowSize"
    ]
    
    # Required files for a valid extension
    REQUIRED_FILES = ["index.html", "index.js", "package.json"]
    ENTRY_POINTS = ["index.html", "index.js", "index.ts"]
    
    @classmethod
    def validate_manifest(cls, manifest: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate a manifest dictionary.
        Returns (is_valid, error_message).
        """
        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in manifest or not manifest[field]:
                return False, f"Missing required field: {field}"
        
        # Validate name format (no spaces, special chars except - and _)
        name = manifest.get("name", "")
        if not name.replace("-", "").replace("_", "").isalnum():
            return False, "Invalid name format: must contain only letters, numbers, hyphens, and underscores"
        
        # Validate version format (basic semver check)
        version = manifest.get("version", "1.0.0")
        parts = version.replace("-", ".").split(".")
        if not all(part.isdigit() or part == "x" for part in parts[:3]):
            return False, f"Invalid version format: {version}"
        
        return True, None
    
    @classmethod
    def validate_directory(cls, ext_dir: Path) -> tuple[bool, Optional[str]]:
        """
        Validate an extension directory.
        Returns (is_valid, error_message).
        """
        if not ext_dir.exists() or not ext_dir.is_dir():
            return False, "Extension directory does not exist"
        
        # Check for package.json
        pkg_json = ext_dir / "package.json"
        if not pkg_json.exists():
            return False, "Missing package.json"
        
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except json.JSONDecodeError as e:
            return False, f"Invalid package.json: {e}"
        
        # Validate manifest
        is_valid, error = cls.validate_manifest(manifest)
        if not is_valid:
            return False, error
        
        # Check for at least one entry point
        has_entry = any((ext_dir / entry).exists() for entry in cls.ENTRY_POINTS)
        if not has_entry:
            return False, f"Missing entry point. Need at least one of: {', '.join(cls.ENTRY_POINTS)}"
        
        return True, None
    
    @classmethod
    def get_manifest_from_directory(cls, ext_dir: Path) -> Optional[Dict[str, Any]]:
        """Load and validate manifest from extension directory."""
        pkg_json = ext_dir / "package.json"
        if not pkg_json.exists():
            return None
        
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            is_valid, _ = cls.validate_manifest(manifest)
            if is_valid:
                return manifest
        except Exception:
            pass
        
        return None
