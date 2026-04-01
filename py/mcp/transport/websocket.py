"""WebSocket transport for MCP - WebSocket-based communication."""

import asyncio
import json
import logging
from typing import Optional, Dict, Any

from py.mcp.transport.base import Transport

logger = logging.getLogger(__name__)

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketClientProtocol = None


class WebSocketTransport(Transport):
    """Transport that communicates with an MCP server over WebSocket.

    This transport connects to an MCP server via WebSocket protocol
    using JSON-RPC 2.0 messages.
    """

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize WebSocket transport.

        Args:
            url: WebSocket server URL (ws:// or wss://)
            headers: Optional HTTP headers for the connection
        """
        super().__init__()
        self._url = url
        self._headers = headers or {}
        self._websocket: Optional["WebSocketClientProtocol"] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._read_buffer: asyncio.Queue = asyncio.Queue()
        self._send_lock: asyncio.Lock = asyncio.Lock()

    async def start_client(self) -> None:
        """Start WebSocket client connection.

        Raises:
            ImportError: If websockets library is not installed
            Exception: If connection fails
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError(
                "websockets library is required for WebSocket transport. "
                "Install it with: pip install websockets"
            )

        logger.info("Connecting to MCP server via WebSocket: %s", self._url)

        try:
            self._websocket = await websockets.connect(
                self._url,
                extra_headers=self._headers,
            )
            self._connected = True

            # Start background reader
            self._reader_task = asyncio.create_task(self._read_loop())

            logger.info("Connected to MCP server via WebSocket")

        except Exception as e:
            logger.error("Failed to connect to WebSocket server: %s", e)
            self._connected = False
            raise

    async def connect(self) -> None:
        """Establish WebSocket connection (alias for start_client compatibility)."""
        if not self._connected:
            await self.start_client()

    async def disconnect(self) -> None:
        """Close WebSocket connection gracefully."""
        self._connected = False

        # Cancel reader task
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None

        # Close websocket
        if self._websocket:
            try:
                await self._websocket.close()
            except Exception as e:
                logger.debug("Error closing websocket: %s", e)
            self._websocket = None

        logger.info("WebSocket connection closed")

    async def send(self, message: Dict[str, Any]) -> None:
        """Send a JSON-RPC message to the server.

        Args:
            message: The JSON-RPC message dictionary

        Raises:
            RuntimeError: If not connected
            Exception: If write fails
        """
        if not self._websocket or not self._connected:
            raise RuntimeError("Not connected to MCP server")

        try:
            async with self._send_lock:
                data = json.dumps(message)
                await self._websocket.send(data)
            logger.debug("Sent message: %s", message)
        except Exception as e:
            logger.error("Failed to send message: %s", e)
            self.handle_error(e)
            raise

    async def receive(self) -> Dict[str, Any]:
        """Receive a JSON-RPC message from the server.

        Returns:
            Received message dictionary

        Raises:
            asyncio.CancelledError: If connection is closed
        """
        try:
            message = await self._read_buffer.get()
            logger.debug("Received message: %s", message)
            return message
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error("Failed to receive message: %s", e)
            self.handle_error(e)
            raise

    async def _read_loop(self) -> None:
        """Background loop that reads from WebSocket."""
        if not self._websocket:
            return

        try:
            async for raw_message in self._websocket:
                if not self._connected:
                    break

                try:
                    # WebSocket message can be text or bytes
                    if isinstance(raw_message, bytes):
                        text = raw_message.decode("utf-8")
                    else:
                        text = raw_message

                    message = json.loads(text)
                    self._read_buffer.put_nowait(message)
                    self.handle_message(message)

                except json.JSONDecodeError as e:
                    logger.warning("Invalid JSON from server: %s: %s", e, text)
                except Exception as e:
                    logger.exception("Error processing message: %s", e)

        except asyncio.CancelledError:
            logger.debug("WebSocket read loop cancelled")
        except Exception as e:
            if self._connected:
                logger.exception("WebSocket read loop error: %s", e)
                self.handle_error(e)
        finally:
            self._connected = False

    @property
    def url(self) -> str:
        """Get the WebSocket URL."""
        return self._url

    @property
    def is_open(self) -> bool:
        """Check if WebSocket is open."""
        if self._websocket:
            return self._websocket.open
        return False
