"""Abstract base class for model providers."""

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional

from .capabilities import ModelInfo
from .config import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ModelConfig,
    ProviderConfig,
    StreamChunk,
)


class Provider(ABC):
    """Abstract base class for model providers."""

    def __init__(self, config: ProviderConfig):
        """Initialize provider with configuration.

        Args:
            config: Provider configuration
        """
        self.config = config
        self._instance = None

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Return the provider type identifier."""
        pass

    @abstractmethod
    async def chat_complete(
        self,
        request: ChatCompletionRequest,
        model_config: Optional[ModelConfig] = None,
    ) -> ChatCompletionResponse:
        """Execute a chat completion request.

        Args:
            request: Chat completion request
            model_config: Optional model-specific configuration

        Returns:
            Chat completion response
        """
        pass

    @abstractmethod
    async def chat_complete_stream(
        self,
        request: ChatCompletionRequest,
        model_config: Optional[ModelConfig] = None,
    ) -> AsyncIterator[StreamChunk]:
        """Execute a streaming chat completion request.

        Args:
            request: Chat completion request
            model_config: Optional model-specific configuration

        Yields:
            Stream chunks
        """
        pass

    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """List available models from this provider.

        Returns:
            List of available models
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is healthy and accessible.

        Returns:
            True if provider is healthy
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} type={self.provider_type} id={self.config.id}>"
