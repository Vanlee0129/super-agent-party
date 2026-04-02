"""Settings API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from .manager import get_settings_manager, SettingsManager

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class Settings(BaseModel):
    """Application settings structure."""
    general: Dict[str, Any] = {}
    llm: Dict[str, Any] = {}
    proxy: Dict[str, Any] = {}
    api_endpoints: Dict[str, str] = {}
    asr: Dict[str, Any] = {}
    tts: Dict[str, Any] = {}


class LLMProviderInfo(BaseModel):
    """LLM provider information."""
    id: str
    name: str
    models: List[str]
    features: List[str]


# LLM providers metadata
LLM_PROVIDERS = {
    "openai": LLMProviderInfo(
        id="openai",
        name="OpenAI",
        models=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
        features=["chat", "function_calling", "vision", "json_mode"]
    ),
    "anthropic": LLMProviderInfo(
        id="anthropic",
        name="Anthropic",
        models=["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
        features=["chat", "function_calling", "vision"]
    ),
    "ollama": LLMProviderInfo(
        id="ollama",
        name="Ollama (Local)",
        models=["llama2", "mistral", "codellama"],
        features=["chat", "completion"]
    ),
}


@router.get("/", response_model=Settings)
async def get_settings():
    """Get all settings."""
    manager = get_settings_manager()
    settings = await manager.get_all_settings()

    return Settings(
        general=settings.get("general", {}),
        llm=settings.get("llm", {}),
        proxy=settings.get("proxy", {}),
        api_endpoints=settings.get("api_endpoints", {}),
        asr=settings.get("asr", {}),
        tts=settings.get("tts", {})
    )


@router.put("/")
async def update_settings(settings: Settings):
    """Update all settings."""
    manager = get_settings_manager()

    # Convert to dict format
    settings_dict = {
        "general": settings.general,
        "llm": settings.llm,
        "proxy": settings.proxy,
        "api_endpoints": settings.api_endpoints,
        "asr": settings.asr,
        "tts": settings.tts
    }

    await manager.update_all_settings(settings_dict)
    return {"success": True, "message": "Settings updated successfully"}


@router.get("/{section}")
async def get_section(section: str) -> Dict[str, Any]:
    """Get a specific settings section."""
    manager = get_settings_manager()

    if section not in SettingsManager.VALID_SECTIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Section '{section}' not found. Valid sections: {list(SettingsManager.VALID_SECTIONS)}"
        )

    try:
        return await manager.get_section(section)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{section}")
async def update_section(section: str, data: Dict[str, Any]):
    """Update a specific settings section."""
    manager = get_settings_manager()

    if section not in SettingsManager.VALID_SECTIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Section '{section}' not found. Valid sections: {list(SettingsManager.VALID_SECTIONS)}"
        )

    try:
        result = await manager.update_section(section, data)
        return {"success": True, "section": section, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/llm/providers", response_model=List[LLMProviderInfo])
async def list_llm_providers():
    """List available LLM providers."""
    return list(LLM_PROVIDERS.values())


@router.get("/llm/models")
async def list_models(provider: Optional[str] = None) -> List[Dict[str, Any]]:
    """List available models for provider(s)."""
    from py.models.capabilities import MODELS

    if provider:
        # Filter by provider
        filtered = {k: v for k, v in MODELS.items() if v.provider == provider}
        if not filtered:
            raise HTTPException(
                status_code=404,
                detail=f"No models found for provider '{provider}'"
            )
        models = filtered
    else:
        models = MODELS

    return [
        {
            "id": info.id,
            "name": info.name,
            "provider": info.provider,
            "context_window": info.context_window,
            "max_output_tokens": info.max_output_tokens,
            "supports_vision": info.supports_vision,
            "supports_function_calling": info.supports_function_calling,
            "supports_json_mode": info.supports_json_mode,
        }
        for info in models.values()
    ]
