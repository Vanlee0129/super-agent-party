"""Model configuration system with provider abstraction.

This package provides a unified interface for interacting with different
model providers (OpenAI, Anthropic, Ollama, etc.) following CoPaw patterns.
"""

from .capabilities import ModelCapability, ModelInfo, MODELS, get_model, list_models_by_provider
from .config import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionUsage,
    ChatMessage,
    ModelConfig,
    ProviderConfig,
    ProviderType,
    StreamChunk,
)
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .ollama import OllamaProvider
from .provider import Provider
from .registry import (
    ProviderRegistry,
    get_registry,
    list_available_models,
    register_provider,
)


def setup_providers() -> ProviderRegistry:
    """Set up and return the global provider registry with all built-in providers.

    Returns:
        Configured provider registry
    """
    registry = get_registry()

    # Register built-in providers
    registry.register("openai", OpenAIProvider)
    registry.register("anthropic", AnthropicProvider)
    registry.register("ollama", OllamaProvider)

    return registry


__all__ = [
    # Capabilities
    "ModelCapability",
    "ModelInfo",
    "MODELS",
    "get_model",
    "list_models_by_provider",
    # Config
    "ChatCompletionChoice",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatCompletionUsage",
    "ChatMessage",
    "ModelConfig",
    "ProviderConfig",
    "ProviderType",
    "StreamChunk",
    # Provider
    "Provider",
    # Registry
    "ProviderRegistry",
    "get_registry",
    "list_available_models",
    "register_provider",
    # Providers
    "OpenAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    # Functions
    "setup_providers",
]
