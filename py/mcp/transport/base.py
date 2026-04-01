"""Base Transport class for MCP communication."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class Transport(ABC):
    """Abstract base class for MCP transports.

    A transport handles the underlying communication mechanism
    (stdio, websocket, etc.) for MCP protocol messages.
    """

    def __init__(self) -> None:
        """Initialize transport."""
        self._connected: bool = False
        self._on_message: Optional[Callable[[dict], None]] = None
        self._on_error: Optional[Callable[[Exception], None]] = None

    @property
    def connected(self) -> bool:
        """Check if transport is connected."""
        return self._connected

    def on_message(self, handler: Callable[[dict], None]) -> None:
        """Set message handler callback.

        Args:
            handler: Callback function that receives parsed message dicts
        """
        self._on_message = handler

    def on_error(self, handler: Callable[[Exception], None]) -> None:
        """Set error handler callback.

        Args:
            handler: Callback function that receives exceptions
        """
        self._on_error = handler

    def handle_message(self, message: dict) -> None:
        """Handle received message by calling the registered handler.

        Args:
            message: Parsed message dictionary
        """
        if self._on_message:
            try:
                self._on_message(message)
            except Exception as e:
                logger.exception("Error in message handler: %s", e)
                self.handle_error(e)

    def handle_error(self, error: Exception) -> None:
        """Handle error by calling the registered handler.

        Args:
            error: The exception that occurred
        """
        if self._on_error:
            try:
                self._on_error(error)
            except Exception:
                logger.exception("Error in error handler: %s", error)
        else:
            logger.error("Transport error: %s", error)

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection.

        Raises:
            Exception: If connection fails
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection gracefully."""
        pass

    @abstractmethod
    async def send(self, message: dict) -> None:
        """Send a message.

        Args:
            message: Message dictionary to send

        Raises:
            Exception: If send fails
        """
        pass

    @abstractmethod
    async def receive(self) -> dict:
        """Receive a message.

        Returns:
            Received message dictionary

        Raises:
            Exception: If receive fails or connection closed
        """
        pass
