"""Model capabilities and metadata."""

from dataclasses import dataclass, field
from enum import Flag, auto
from typing import Dict, Optional


class ModelCapability(Flag):
    """Flags for model capabilities."""

    CHAT = auto()
    COMPLETION = auto()
    STREAMING = auto()
    VISION = auto()
    FUNCTION_CALLING = auto()
    JSON_MODE = auto()
    SYSTEM_MESSAGE = auto()


@dataclass
class ModelInfo:
    """Information about a model."""

    id: str
    name: str
    provider: str
    capabilities: ModelCapability = ModelCapability.CHAT | ModelCapability.STREAMING
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    supports_vision: bool = False
    supports_function_calling: bool = False
    supports_json_mode: bool = False
    metadata: Dict[str, str] = field(default_factory=dict)


# Predefined models registry
MODELS: Dict[str, ModelInfo] = {
    # OpenAI models
    "gpt-4": ModelInfo(
        id="gpt-4",
        name="GPT-4",
        provider="openai",
        capabilities=ModelCapability.CHAT | ModelCapability.COMPLETION | ModelCapability.STREAMING | ModelCapability.FUNCTION_CALLING | ModelCapability.JSON_MODE,
        context_window=8192,
        max_output_tokens=4096,
        supports_function_calling=True,
        supports_json_mode=True,
    ),
    "gpt-4-turbo": ModelInfo(
        id="gpt-4-turbo",
        name="GPT-4 Turbo",
        provider="openai",
        capabilities=ModelCapability.CHAT | ModelCapability.COMPLETION | ModelCapability.STREAMING | ModelCapability.VISION | ModelCapability.FUNCTION_CALLING | ModelCapability.JSON_MODE,
        context_window=128000,
        max_output_tokens=4096,
        supports_vision=True,
        supports_function_calling=True,
        supports_json_mode=True,
    ),
    "gpt-3.5-turbo": ModelInfo(
        id="gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        provider="openai",
        capabilities=ModelCapability.CHAT | ModelCapability.COMPLETION | ModelCapability.STREAMING | ModelCapability.FUNCTION_CALLING | ModelCapability.JSON_MODE,
        context_window=16385,
        max_output_tokens=4096,
        supports_function_calling=True,
        supports_json_mode=True,
    ),
    # Anthropic models
    "claude-3-opus": ModelInfo(
        id="claude-3-opus",
        name="Claude 3 Opus",
        provider="anthropic",
        capabilities=ModelCapability.CHAT | ModelCapability.STREAMING | ModelCapability.VISION | ModelCapability.FUNCTION_CALLING,
        context_window=200000,
        max_output_tokens=4096,
        supports_vision=True,
        supports_function_calling=True,
    ),
    "claude-3-sonnet": ModelInfo(
        id="claude-3-sonnet",
        name="Claude 3 Sonnet",
        provider="anthropic",
        capabilities=ModelCapability.CHAT | ModelCapability.STREAMING | ModelCapability.VISION | ModelCapability.FUNCTION_CALLING,
        context_window=200000,
        max_output_tokens=4096,
        supports_vision=True,
        supports_function_calling=True,
    ),
    "claude-3-haiku": ModelInfo(
        id="claude-3-haiku",
        name="Claude 3 Haiku",
        provider="anthropic",
        capabilities=ModelCapability.CHAT | ModelCapability.STREAMING | ModelCapability.VISION | ModelCapability.FUNCTION_CALLING,
        context_window=200000,
        max_output_tokens=4096,
        supports_vision=True,
        supports_function_calling=True,
    ),
    # Ollama models (local defaults)
    "llama2": ModelInfo(
        id="llama2",
        name="Llama 2",
        provider="ollama",
        capabilities=ModelCapability.CHAT | ModelCapability.COMPLETION | ModelCapability.STREAMING,
        context_window=4096,
        max_output_tokens=2048,
    ),
    "mistral": ModelInfo(
        id="mistral",
        name="Mistral",
        provider="ollama",
        capabilities=ModelCapability.CHAT | ModelCapability.COMPLETION | ModelCapability.STREAMING,
        context_window=8192,
        max_output_tokens=4096,
    ),
    "codellama": ModelInfo(
        id="codellama",
        name="Code Llama",
        provider="ollama",
        capabilities=ModelCapability.CHAT | ModelCapability.COMPLETION | ModelCapability.STREAMING,
        context_window=16384,
        max_output_tokens=4096,
    ),
}


def get_model(model_id: str) -> Optional[ModelInfo]:
    """Get model info by ID."""
    return MODELS.get(model_id)


def list_models_by_provider(provider: str) -> Dict[str, ModelInfo]:
    """List all models for a given provider."""
    return {k: v for k, v in MODELS.items() if v.provider == provider}
