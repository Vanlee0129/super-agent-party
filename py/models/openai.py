"""OpenAI provider implementation."""

import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from .capabilities import MODELS, ModelInfo
from .config import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    ModelConfig,
    ProviderConfig,
    StreamChunk,
)
from .provider import Provider


class OpenAIProvider(Provider):
    """OpenAI API provider."""

    def __init__(self, config: ProviderConfig):
        """Initialize OpenAI provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._client: Optional[aiohttp.ClientSession] = None
        self.base_url = config.base_url or "https://api.openai.com/v1"

    @property
    def provider_type(self) -> str:
        return "openai"

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    async def _get_client(self) -> aiohttp.ClientSession:
        """Get or create HTTP client."""
        if self._client is None or self._client.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._client = aiohttp.ClientSession(
                base_url=self.base_url,
                headers=self._get_headers(),
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
        """Format messages for OpenAI API."""
        formatted = []
        for msg in messages:
            msg_dict: Dict[str, Any] = {
                "role": msg.role,
                "content": msg.content,
            }
            if msg.name:
                msg_dict["name"] = msg.name
            if msg.tool_calls:
                msg_dict["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                msg_dict["tool_call_id"] = msg.tool_call_id
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
        }

        if request.temperature is not None:
            payload["temperature"] = request.temperature
        elif model_config:
            payload["temperature"] = model_config.temperature

        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        elif model_config and model_config.max_tokens:
            payload["max_tokens"] = model_config.max_tokens

        if request.top_p is not None:
            payload["top_p"] = request.top_p
        elif model_config:
            payload["top_p"] = model_config.top_p

        if request.stop:
            payload["stop"] = request.stop
        elif model_config and model_config.stop:
            payload["stop"] = model_config.stop

        if request.stream:
            payload["stream"] = True

        if request.tools:
            payload["tools"] = request.tools
        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice

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

        async with client.post("/chat/completions", json=payload) as response:
            response.raise_for_status()
            data = await response.json()

        return ChatCompletionResponse.from_dict(data, provider=self.provider_type)

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

        async with client.post("/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.content:
                line = line.decode("utf-8").strip()
                if not line.startswith("data: "):
                    continue
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break

                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                chunk_data = data.get("choices", [{}])[0]
                delta = chunk_data.get("delta", {})
                finish_reason = chunk_data.get("finish_reason")

                yield StreamChunk(
                    id=data.get("id", ""),
                    delta=delta.get("content", ""),
                    index=chunk_data.get("index", 0),
                    finish_reason=finish_reason,
                    role=delta.get("role"),
                    tool_calls=delta.get("tool_calls"),
                )

    async def list_models(self) -> List[ModelInfo]:
        """List available models from OpenAI.

        Returns:
            List of available models
        """
        # Return predefined OpenAI models
        return [m for m in MODELS.values() if m.provider == "openai"]

    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible.

        Returns:
            True if API is healthy
        """
        try:
            client = await self._get_client()
            async with client.get("/models") as response:
                return response.status == 200
        except Exception:
            return False
