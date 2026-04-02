"""Sandbox management for code execution."""
import asyncio
import httpx
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel

from py.get_setting import load_settings


class SandboxType(str, Enum):
    """Sandbox type enumeration."""
    E2B = "e2b"
    LOCAL = "local"


class SandboxConfig(BaseModel):
    """Sandbox configuration."""
    type: SandboxType = SandboxType.LOCAL
    api_key: Optional[str] = None
    local_endpoint: str = "http://localhost:3001"


class SandboxManager:
    """Manages sandbox configurations and status."""
    
    _instance: Optional["SandboxManager"] = None
    
    def __init__(self):
        self._config = SandboxConfig()
        self._status_cache: Dict[str, Any] = {}
    
    @classmethod
    def get_instance(cls) -> "SandboxManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = SandboxManager()
        return cls._instance
    
    def get_config(self) -> SandboxConfig:
        """Get current sandbox configuration."""
        return self._config
    
    def update_config(self, config: SandboxConfig) -> SandboxConfig:
        """Update sandbox configuration."""
        self._config = config
        return self._config
    
    async def check_e2b_status(self) -> Dict[str, Any]:
        """Check E2B sandbox availability."""
        if not self._config.api_key:
            return {"available": False, "error": "No API key configured"}
        
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    "https://api.e2b.dev/v1/sandbox",
                    headers={"Authorization": f"Bearer {self._config.api_key}"}
                )
                return {"available": response.status_code == 200}
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    async def check_local_status(self) -> Dict[str, Any]:
        """Check local sandbox (node_runner) availability."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self._config.local_endpoint}/health")
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "available": True,
                        "status": data.get("status", "running"),
                        "version": data.get("version", "unknown")
                    }
                return {"available": False, "error": f"Status code: {response.status_code}"}
        except httpx.ConnectError:
            return {"available": False, "error": "Connection refused - is node_runner running?"}
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get status of all sandboxes."""
        e2b_status = await self.check_e2b_status()
        local_status = await self.check_local_status()
        
        return {
            "e2b": e2b_status,
            "local": local_status,
            "current_type": self._config.type.value,
            "configured": {
                "e2b": bool(self._config.api_key),
                "local": bool(self._config.local_endpoint)
            }
        }
    
    async def load_config_from_settings(self):
        """Load sandbox configuration from application settings."""
        try:
            settings = await load_settings()
            code_settings = settings.get("codeSettings", {})
            
            self._config = SandboxConfig(
                type=SandboxType(code_settings.get("sandbox_type", "local")),
                api_key=code_settings.get("e2b_api_key"),
                local_endpoint=code_settings.get("sandbox_url", "http://localhost:3001")
            )
        except Exception:
            pass  # Use defaults
    
    @property
    def current_type(self) -> SandboxType:
        """Get current sandbox type."""
        return self._config.type
    
    @property
    def e2b_api_key(self) -> Optional[str]:
        """Get E2B API key."""
        return self._config.api_key
    
    @property
    def local_endpoint(self) -> str:
        """Get local sandbox endpoint."""
        return self._config.local_endpoint
