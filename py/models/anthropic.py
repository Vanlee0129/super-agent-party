"""Anthropic provider implementation."""

import json
from typing import Any, AsyncIterator, Dict, List, Optional

import aiohttp

from .capabilities import MODELS, ModelInfo
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


class AnthropicProvider(Provider):
    """Anthropic API provider."""

    def __init__(self, config: ProviderConfig):
        """Initialize Anthropic provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self._client: Optional[aiohttp.ClientSession] = None
        self.base_url = config.base_url or "https://api.anthropic.com/v1"

    @property
    def provider_type(self) -> str:
        return "anthropic"

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "x-api-key": self.config.api_key or "",
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

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
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Format messages for Anthropic API.

        Anthropic requires system messages to be separate and uses a different format.

        Returns:
            Tuple of (formatted_messages, system_prompt)
        """
        formatted = []
        system_prompt = None

        for msg in messages:
            if msg.role == "system":
                # Anthropic handles system message separately
                system_prompt = msg.content
            elif msg.role == "user":
                formatted.append({
                    "role": "user",
                    "content": msg.content,
                })
            elif msg.role == "assistant":
                formatted.append({
                    "role": "assistant",
                    "content": msg.content,
                })
            elif msg.role == "tool":
                formatted.append({
                    "role": "user",
                    "content": f"<tool_result>{msg.content}</tool_result>",
                })

        return formatted, system_prompt

    def _merge_config(
        self,
        request: ChatCompletionRequest,
        model_config: Optional[ModelConfig],
    ) -> Dict[str, Any]:
        """Merge request and model config into API payload."""
        formatted_messages, system_prompt = self._format_messages(request.messages)

        payload: Dict[str, Any] = {
            "model": request.model,
            "messages": formatted_messages,
        }

        if system_prompt:
            payload["system"] = system_prompt

        if request.temperature is not None:
            payload["temperature"] = request.temperature
        elif model_config:
            payload["temperature"] = model_config.temperature

        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        elif model_config and model_config.max_tokens:
            payload["max_tokens"] = model_config.max_tokens
        else:
            # Anthropic requires max_tokens
            payload["max_tokens"] = 1024

        if request.top_p is not None:
            payload["top_p"] = request.top_p
        elif model_config:
            payload["top_p"] = model_config.top_p

        if request.stop:
            payload["stop_sequences"] = request.stop
        elif model_config and model_config.stop:
            payload["stop_sequences"] = model_config.stop

        if request.stream:
            payload["stream"] = True

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

        async with client.post("/messages", json=payload) as response:
            response.raise_for_status()
            data = await response.json()

        # Convert Anthropic response to standard format
        content = data.get("content", [])
        message_text = ""
        if content and isinstance(content, list):
            for block in content:
                if block.get("type") == "text":
                    message_text = block.get("text", "")

        choices = [
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(
                    role="assistant",
                    content=message_text,
                ),
                finish_reason=data.get("stop_reason"),
            )
        ]

        usage_data = data.get("usage", {})
        usage = ChatCompletionUsage(
            prompt_tokens=usage_data.get("input_tokens", 0),
            completion_tokens=usage_data.get("output_tokens", 0),
            total_tokens=usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
        )

        return ChatCompletionResponse(
            id=data.get("id", ""),
            model=data.get("model", request.model),
            choices=choices,
            usage=usage,
            created=data.get("created", 0),
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

        async with client.post("/messages", json=payload) as response:
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

                event_type = data.get("type")

                if event_type == "message_start":
                    msg = data.get("message", {})
                    yield StreamChunk(
                        id=msg.get("id", ""),
                        delta="",
                        index=0,
                        role=msg.get("role"),
                    )
                elif event_type == "content_block_delta":
                    delta = data.get("delta", {})
                    if delta.get("type") == "text_delta":
                        yield StreamChunk(
                            id="",
                            delta=delta.get("text", ""),
                            index=0,
                        )
                elif event_type == "message_delta":
                    yield StreamChunk(
                        id="",
                        delta="",
                        index=0,
                        finish_reason=data.get("content_block", {}).get("stop_reason"),
                    )

    async def list_models(self) -> List[ModelInfo]:
        """List available models from Anthropic.

        Returns:
            List of available models
        """
        # Return predefined Anthropic models
        return [m for m in MODELS.values() if m.provider == "anthropic"]

    async def health_check(self) -> bool:
        """Check if Anthropic API is accessible.

        Returns:
            True if API is healthy
        """
        try:
            client = await self._get_client()
            async with client.post(
                "/messages",
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "hi"}],
                },
            ) as response:
                return response.status in (200, 201)
        except Exception:
            return False
