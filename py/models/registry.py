"""Provider registry for model management."""

from typing import Dict, List, Optional, Type

from .capabilities import ModelInfo, MODELS
from .config import ProviderConfig, ProviderType
from .provider import Provider


class ProviderRegistry:
    """Registry for managing model providers."""

    def __init__(self):
        """Initialize the registry."""
        self._providers: Dict[str, Type[Provider]] = {}
        self._instances: Dict[str, Provider] = {}
        self._configs: Dict[str, ProviderConfig] = {}

    def register(self, provider_type: str, provider_class: Type[Provider]) -> None:
        """Register a provider class.

        Args:
            provider_type: Provider type identifier
            provider_class: Provider class
        """
        self._providers[provider_type] = provider_class

    def get(self, provider_type: str) -> Optional[Type[Provider]]:
        """Get a registered provider class.

        Args:
            provider_type: Provider type identifier

        Returns:
            Provider class or None
        """
        return self._providers.get(provider_type)

    def create(
        self,
        config: ProviderConfig,
        provider_type: Optional[str] = None,
    ) -> Provider:
        """Create a provider instance.

        Args:
            config: Provider configuration
            provider_type: Optional provider type override

        Returns:
            Provider instance
        """
        ptype = provider_type or config.provider_type
        if isinstance(ptype, ProviderType):
            ptype = ptype.value

        provider_class = self._providers.get(ptype)
        if provider_class is None:
            raise ValueError(f"Unknown provider type: {ptype}")

        instance = provider_class(config)
        self._instances[config.id] = instance
        self._configs[config.id] = config
        return instance

    def get_instance(self, provider_id: str) -> Optional[Provider]:
        """Get an existing provider instance.

        Args:
            provider_id: Provider configuration ID

        Returns:
            Provider instance or None
        """
        return self._instances.get(provider_id)

    def list_providers(self) -> List[ProviderConfig]:
        """List all registered provider configurations.

        Returns:
            List of provider configs
        """
        return list(self._configs.values())

    def get_config(self, provider_id: str) -> Optional[ProviderConfig]:
        """Get provider configuration by ID.

        Args:
            provider_id: Provider configuration ID

        Returns:
            Provider config or None
        """
        return self._configs.get(provider_id)

    def clear(self) -> None:
        """Clear all registered providers and instances."""
        self._providers.clear()
        self._instances.clear()
        self._configs.clear()


# Global registry instance
_registry = ProviderRegistry()


def get_registry() -> ProviderRegistry:
    """Get the global provider registry.

    Returns:
        Global registry instance
    """
    return _registry


def register_provider(provider_type: str, provider_class: Type[Provider]) -> None:
    """Register a provider class in the global registry.

    Args:
        provider_type: Provider type identifier
        provider_class: Provider class
    """
    _registry.register(provider_type, provider_class)


def list_available_models(provider_filter: Optional[str] = None) -> Dict[str, ModelInfo]:
    """List available models, optionally filtered by provider.

    Args:
        provider_filter: Optional provider name to filter by

    Returns:
        Dictionary of model_id -> ModelInfo
    """
    if provider_filter:
        return {k: v for k, v in MODELS.items() if v.provider == provider_filter}
    return dict(MODELS)
