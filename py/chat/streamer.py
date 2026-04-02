"""Streaming response handling for chat."""

import logging
from typing import Any, AsyncIterator, Dict, Optional

from py.models import (
    ChatCompletionRequest,
    ChatMessage,
    StreamChunk,
    get_registry,
)

logger = logging.getLogger(__name__)


class ChatStreamer:
    """Handles streaming chat responses from LLM providers."""

    def __init__(self):
        self.registry = get_registry()

    async def stream_chat(
        self,
        message: str,
        model: str = "gpt-4",
        provider: str = "openai",
        conversation_history: Optional[list] = None,
        **kwargs,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream chat response from LLM.

        Args:
            message: The user message
            model: Model name
            provider: Provider name
            conversation_history: Optional list of previous messages
            **kwargs: Additional provider-specific parameters

        Yields:
            Stream chunks with type, content, and done flag
        """
        # Build messages list
        messages = []
        if conversation_history:
            for hist_msg in conversation_history:
                messages.append(ChatMessage(
                    role=hist_msg.get("role", "user"),
                    content=hist_msg.get("content", ""),
                ))

        messages.append(ChatMessage(role="user", content=message))

        # Create chat completion request
        request = ChatCompletionRequest(
            model=model,
            messages=messages,
            stream=True,
            **{k: v for k, v in kwargs.items() if v is not None},
        )

        # Get provider instance
        provider_config = self.registry.get_config(provider)
        if not provider_config:
            yield {
                "type": "error",
                "content": f"Provider not configured: {provider}",
                "done": True,
            }
            return

        provider_instance = self.registry.get_instance(provider)
        if not provider_instance:
            provider_instance = self.registry.create(provider_config)

        try:
            # Stream response
            async for chunk in provider_instance.chat_complete_stream(request):
                yield {
                    "type": "chunk",
                    "id": chunk.id,
                    "delta": chunk.delta,
                    "index": chunk.index,
                    "finish_reason": chunk.finish_reason,
                    "done": False,
                }

            yield {"type": "chunk", "content": "", "done": True}

        except Exception as e:
            logger.exception(f"Error streaming chat: {e}")
            yield {
                "type": "error",
                "content": str(e),
                "done": True,
            }

    async def complete_chat(
        self,
        message: str,
        model: str = "gpt-4",
        provider: str = "openai",
        conversation_history: Optional[list] = None,
        **kwargs,
    ) -> str:
        """Non-streaming chat completion.

        Args:
            message: The user message
            model: Model name
            provider: Provider name
            conversation_history: Optional list of previous messages
            **kwargs: Additional provider-specific parameters

        Returns:
            Complete response text
        """
        response_text = ""
        async for chunk in self.stream_chat(message, model, provider, conversation_history, **kwargs):
            if chunk.get("type") == "chunk":
                response_text += chunk.get("delta", "")

        return response_text
