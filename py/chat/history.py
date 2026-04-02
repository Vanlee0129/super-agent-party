"""Conversation history management for chat."""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """A single chat message."""
    id: str
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ChatHistory:
    """In-memory conversation history store (per-process).

    Note: For production, replace with Redis or database backend.
    """

    _lock = threading.Lock()
    _conversations: Dict[str, List[Dict[str, Any]]] = {}
    _max_messages_per_conversation = 100

    @classmethod
    def add_message(cls, conversation_id: str, message: Dict[str, Any]) -> None:
        """Add a message to a conversation.

        Args:
            conversation_id: The conversation identifier
            message: Message dict with id, role, content, timestamp
        """
        with cls._lock:
            if conversation_id not in cls._conversations:
                cls._conversations[conversation_id] = []

            cls._conversations[conversation_id].append(message)

            # Trim if exceeds max
            if len(cls._conversations[conversation_id]) > cls._max_messages_per_conversation:
                cls._conversations[conversation_id] = cls._conversations[conversation_id][-cls._max_messages_per_conversation:]

            logger.debug(f"Added message to conversation {conversation_id}, total: {len(cls._conversations[conversation_id])}")

    @classmethod
    def get_messages(cls, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get messages from a conversation.

        Args:
            conversation_id: The conversation identifier
            limit: Maximum number of messages to return

        Returns:
            List of message dicts
        """
        with cls._lock:
            messages = cls._conversations.get(conversation_id, [])
            # Return most recent messages
            return messages[-limit:] if limit > 0 else messages

    @classmethod
    def clear_conversation(cls, conversation_id: str) -> None:
        """Clear all messages in a conversation.

        Args:
            conversation_id: The conversation identifier
        """
        with cls._lock:
            if conversation_id in cls._conversations:
                del cls._conversations[conversation_id]
            logger.debug(f"Cleared conversation {conversation_id}")

    @classmethod
    def delete_conversation(cls, conversation_id: str) -> None:
        """Delete a conversation entirely.

        Args:
            conversation_id: The conversation identifier
        """
        cls.clear_conversation(conversation_id)

    @classmethod
    def list_conversations(cls) -> List[str]:
        """List all conversation IDs.

        Returns:
            List of conversation IDs
        """
        with cls._lock:
            return list(cls._conversations.keys())

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get statistics about stored conversations.

        Returns:
            Dict with conversation count and message counts
        """
        with cls._lock:
            return {
                "total_conversations": len(cls._conversations),
                "total_messages": sum(len(m) for m in cls._conversations.values()),
                "conversations": {
                    cid: len(messages) for cid, messages in cls._conversations.items()
                },
            }


class ConversationHistory:
    """Alias for ChatHistory for backward compatibility."""

    @staticmethod
    def add_message(conversation_id: str, message: Dict[str, Any]) -> None:
        ChatHistory.add_message(conversation_id, message)

    @staticmethod
    def get_messages(conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return ChatHistory.get_messages(conversation_id, limit)

    @staticmethod
    def clear_conversation(conversation_id: str) -> None:
        ChatHistory.clear_conversation(conversation_id)

    @staticmethod
    def list_conversations() -> List[str]:
        return ChatHistory.list_conversations()

    @staticmethod
    def get_stats() -> Dict[str, Any]:
        return ChatHistory.get_stats()
