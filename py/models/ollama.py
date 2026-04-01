"""Ollama provider implementation for local models."""

import json
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from .capabilities import MODELS, ModelCapability, ModelInfo
from .config import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatCompletionUsage,
    ChatMessage,
    ModelConfig,
    ProviderConfig,
    StreamChunk,
)
from .provider import Provider


class OllamaProvider(Provider):
    """Ollama local model provider."""

    def __init__(self, config: ProviderConfig):
        """Initialize Ollama provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._client: Optional[aiohttp.ClientSession] = None
        self.base_url = config.base_url or "http://localhost:11434"

    @property
    def provider_type(self) -> str:
        return "ollama"

    async def _get_client(self) -> aiohttp.ClientSession:
        """Get or create HTTP client."""
        if self._client is None or self._client.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._client = aiohttp.ClientSession(
                base_url=self.base_url,
                timeout=timeout,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.closed:
            await self._client.close()
            self._client = None

    def _format_messages(
        self, messages: List[ChatMessage]
    ) -> List[Dict[str, Any]]:
        """Format messages for Ollama API."""
        formatted = []
        for msg in messages:
            msg_dict: Dict[str, Any] = {
                "role": msg.role,
                "content": msg.content,
            }
            if msg.name:
                msg_dict["name"] = msg.name
            formatted.append(msg_dict)
        return formatted

    def _merge_config(
        self,
        request: ChatCompletionRequest,
        model_config: Optional[ModelConfig],
    ) -> Dict[str, Any]:
        """Merge request and model config into API payload."""
        payload: Dict[str, Any] = {
            "model": request.model,
            "messages": self._format_messages(request.messages),
            "stream": request.stream,
        }

        options: Dict[str, Any] = {}

        if request.temperature is not None:
            options["temperature"] = request.temperature
        elif model_config:
            options["temperature"] = model_config.temperature

        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens
        elif model_config and model_config.max_tokens:
            options["num_predict"] = model_config.max_tokens

        if request.top_p is not None:
            options["top_p"] = request.top_p
        elif model_config:
            options["top_p"] = model_config.top_p

        if request.stop:
            options["stop"] = request.stop
        elif model_config and model_config.stop:
            options["stop"] = model_config.stop

        if options:
            payload["options"] = options

        return payload

    async def chat_complete(
        self,
        request: ChatCompletionRequest,
        model_config: Optional[ModelConfig] = None,
    ) -> ChatCompletionResponse:
        """Execute a chat completion request.

        Args:
            request: Chat completion request
            model_config: Optional model configuration

        Returns:
            Chat completion response
        """
        client = await self._get_client()
        payload = self._merge_config(request, model_config)
        payload["stream"] = False

        async with client.post("/api/chat", json=payload) as response:
            response.raise_for_status()
            data = await response.json()

        # Convert Ollama response to standard format
        message = data.get("message", {})
        choices = [
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role=message.get("role", "assistant"),
                    content=message.get("content", ""),
                ),
                finish_reason=data.get("done_reason"),
            )
        ]

        usage = ChatCompletionUsage(
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
        )

        return ChatCompletionResponse(
            id=f"ollama-{data.get('model', request.model)}-{data.get('created_at', '')}",
            model=data.get("model", request.model),
            choices=choices,
            usage=usage,
            created=0,
            provider=self.provider_type,
        )

    async def chat_complete_stream(
        self,
        request: ChatCompletionRequest,
        model_config: Optional[ModelConfig] = None,
    ) -> AsyncIterator[StreamChunk]:
        """Execute a streaming chat completion request.

        Args:
            request: Chat completion request
            model_config: Optional model configuration

        Yields:
            Stream chunks
        """
        client = await self._get_client()
        payload = self._merge_config(request, model_config)
        payload["stream"] = True

        async with client.post("/api/chat", json=payload) as response:
            response.raise_for_status()
            async for line in response.content:
                line = line.decode("utf-8").strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                message = data.get("message", {})
                yield StreamChunk(
                    id=f"ollama-{data.get('model', request.model)}",
                    delta=message.get("content", ""),
                    index=0,
                    finish_reason=data.get("done_reason") if data.get("done") else None,
                    role=message.get("role"),
                )

    async def list_models(self) -> List[ModelInfo]:
        """List available models from Ollama.

        Returns:
            List of available models
        """
        try:
            client = await self._get_client()
            async with client.get("/api/tags") as response:
                response.raise_for_status()
                data = await response.json()

            models = []
            for model_data in data.get("models", []):
                model_info = ModelInfo(
                    id=model_data.get("name", ""),
                    name=model_data.get("name", ""),
                    provider="ollama",
                    capabilities=ModelCapability.CHAT | ModelCapability.COMPLETION | ModelCapability.STREAMING,
                    metadata={"size": model_data.get("size", 0)},
                )
                models.append(model_info)

            # Fallback to predefined if none available
            if not models:
                return [m for m in MODELS.values() if m.provider == "ollama"]
            return models

        except Exception:
            # Return predefined models on error
            return [m for m in MODELS.values() if m.provider == "ollama"]

    async def health_check(self) -> bool:
        """Check if Ollama is accessible.

        Returns:
            True if Ollama is running
        """
        try:
            client = await self._get_client()
            async with client.get("/api/tags") as response:
                return response.status == 200
        except Exception:
            return False
