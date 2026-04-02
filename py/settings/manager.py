"""Settings management with persistent storage."""

import json
from typing import Dict, Any, Optional

from py.get_setting import load_settings, save_settings, get_default_settings_sync


class SettingsManager:
    """Manages application settings with persistent storage."""

    # Valid settings sections
    VALID_SECTIONS = {"general", "llm", "proxy", "api_endpoints", "asr", "tts"}

    def __init__(self):
        self._cache: Optional[Dict[str, Any]] = None

    async def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings, merging defaults with user settings."""
        if self._cache is None:
            self._cache = await load_settings()
        return self._cache.copy()

    async def update_all_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update all settings."""
        # Merge with defaults to ensure all keys exist
        defaults = get_default_settings_sync().copy()
        merged = {**defaults, **settings}

        await save_settings(merged)
        self._cache = merged
        return merged.copy()

    async def get_section(self, section: str) -> Dict[str, Any]:
        """Get a specific settings section."""
        if section not in self.VALID_SECTIONS:
            raise ValueError(f"Invalid section: {section}")

        all_settings = await self.get_all_settings()
        return all_settings.get(section, {})

    async def update_section(self, section: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a specific settings section."""
        if section not in self.VALID_SECTIONS:
            raise ValueError(f"Invalid section: {section}")

        all_settings = await self.get_all_settings()
        all_settings[section] = {**all_settings.get(section, {}), **data}

        await save_settings(all_settings)
        self._cache = all_settings
        return all_settings[section]

    def invalidate_cache(self):
        """Invalidate the settings cache."""
        self._cache = None


# Global settings manager instance
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """Get or create the global settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
