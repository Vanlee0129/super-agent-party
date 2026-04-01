"""Model configuration data models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ProviderType(str, Enum):
    """Supported provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    AZURE = "azure"
    GOOGLE = "google"


@dataclass
class ProviderConfig:
    """Configuration for a model provider."""

    id: str
    name: str
    provider_type: ProviderType
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    timeout: float = 60.0
    max_retries: int = 3
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class ModelConfig:
    """Configuration for a specific model."""

    id: str
    provider_id: str
    model_name: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    top_k: Optional[int] = None
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatMessage:
    """A single chat message."""

    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass
class ChatCompletionRequest:
    """Request for chat completion."""

    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    stream: bool = False
    stop: Optional[List[str]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatCompletionChoice:
    """A single choice in a chat completion response."""

    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None


@dataclass
class ChatCompletionUsage:
    """Usage statistics for a completion."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ChatCompletionResponse:
    """Response from chat completion."""

    id: str
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage
    created: int
    provider: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any], provider: Optional[str] = None) -> "ChatCompletionResponse":
        """Create response from dictionary (e.g., OpenAI format)."""
        choices = [
            ChatCompletionChoice(
                index=c.get("index", 0),
                message=ChatMessage(
                    role=c.get("message", {}).get("role", "assistant"),
                    content=c.get("message", {}).get("content", ""),
                ),
                finish_reason=c.get("finish_reason"),
            )
            for c in data.get("choices", [])
        ]
        usage_data = data.get("usage", {})
        usage = ChatCompletionUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )
        return cls(
            id=data.get("id", ""),
            model=data.get("model", ""),
            choices=choices,
            usage=usage,
            created=data.get("created", 0),
            provider=provider,
        )


@dataclass
class StreamChunk:
    """A chunk from a streaming response."""

    id: str
    delta: str
    index: int
    finish_reason: Optional[str] = None
    role: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
