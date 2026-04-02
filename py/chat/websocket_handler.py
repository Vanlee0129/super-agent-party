"""WebSocket handler for JSON-RPC chat messages."""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


# JSON-RPC error codes
JSONRPC_ERRORS = {
    "PARSE_ERROR": -32700,
    "INVALID_REQUEST": -32600,
    "METHOD_NOT_FOUND": -32601,
    "INVALID_PARAMS": -32602,
    "INTERNAL_ERROR": -32603,
}

# Supported JSON-RPC methods
CHAT_METHODS = {
    "chat.send": "Send message, get response",
    "chat.stream": "Stream response chunks",
    "chat.history": "Get conversation history",
    "chat.clear": "Clear conversation",
}


class ChatWebSocket:
    """Handles a single WebSocket connection for chat."""

    def __init__(self, websocket: WebSocket, client_id: Optional[str] = None):
        self.websocket = websocket
        self.client_id = client_id or str(id(websocket))
        self.conversation_id: Optional[str] = None
        self._streaming = False

    async def connect(self) -> None:
        """Accept the WebSocket connection."""
        await self.websocket.accept()
        logger.info(f"Client {self.client_id} connected")

    def disconnect(self) -> None:
        """Handle client disconnection."""
        logger.info(f"Client {self.client_id} disconnected")

    def _add_message_to_history(self, conversation_id: str, role: str, content: str) -> tuple[str, float]:
        """Add a message to history and return (msg_id, timestamp)."""
        from py.chat.history import ChatHistory
        msg_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().timestamp()
        ChatHistory.add_message(conversation_id, {
            "id": msg_id,
            "role": role,
            "content": content,
            "timestamp": timestamp,
        })
        return msg_id, timestamp

    async def handle_message(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming JSON-RPC message."""
        if not isinstance(data, dict):
            return self._error_response(None, JSONRPC_ERRORS["PARSE_ERROR"], "Parse error")

        jsonrpc_id = data.get("id")
        method = data.get("method")
        params = data.get("params", {})

        if not method:
            return self._error_response(jsonrpc_id, JSONRPC_ERRORS["INVALID_REQUEST"], "Method is required")

        # Route to appropriate handler
        if method == "chat.send":
            return await self._handle_chat_send(jsonrpc_id, params)
        elif method == "chat.stream":
            return await self._handle_chat_stream(jsonrpc_id, params)
        elif method == "chat.history":
            return self._handle_chat_history(jsonrpc_id, params)
        elif method == "chat.clear":
            return self._handle_chat_clear(jsonrpc_id, params)
        else:
            return self._error_response(jsonrpc_id, JSONRPC_ERRORS["METHOD_NOT_FOUND"], f"Method not found: {method}")

    async def _handle_chat_send(self, jsonrpc_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle non-streaming chat.send."""
        from py.chat.streamer import ChatStreamer

        message = params.get("message", "")
        model = params.get("model", "gpt-4")
        conversation_id = params.get("conversation_id")
        provider = params.get("provider", "openai")

        if not message:
            return self._error_response(jsonrpc_id, JSONRPC_ERRORS["INVALID_PARAMS"], "Message is required")

        # Add user message to history
        if conversation_id:
            self._add_message_to_history(conversation_id, "user", message)

        # Get streaming response
        streamer = ChatStreamer()
        response_text = ""
        async for chunk in streamer.stream_chat(message, model=model, provider=provider):
            if chunk.get("type") == "chunk":
                response_text += chunk.get("content", "")

        # Create assistant message
        if conversation_id:
            assistant_id, assistant_timestamp = self._add_message_to_history(conversation_id, "assistant", response_text)
        else:
            assistant_id = str(uuid.uuid4())
            assistant_timestamp = datetime.utcnow().timestamp()

        return {
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "result": {
                "type": "message",
                "id": assistant_id,
                "role": "assistant",
                "content": response_text,
                "timestamp": assistant_timestamp,
                "conversation_id": conversation_id,
            },
        }

    async def _handle_chat_stream(self, jsonrpc_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle streaming chat.stream - returns immediately, client should listen for chunks."""
        message = params.get("message", "")
        conversation_id = params.get("conversation_id")

        if not message:
            return self._error_response(jsonrpc_id, JSONRPC_ERRORS["INVALID_PARAMS"], "Message is required")

        # Add user message to history
        if conversation_id:
            self._add_message_to_history(conversation_id, "user", message)
            self.conversation_id = conversation_id

        # Return stream ID for client to subscribe
        stream_id = str(uuid.uuid4())
        self._streaming = True

        return {
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "result": {
                "type": "stream_start",
                "stream_id": stream_id,
                "conversation_id": conversation_id,
            },
        }

    async def send_stream_chunk(self, stream_id: str, chunk: Dict[str, Any], done: bool = False) -> None:
        """Send a streaming chunk to the client."""
        message = {
            "type": "chunk",
            "stream_id": stream_id,
            "content": chunk.get("delta", ""),
            "done": done,
        }
        if done:
            self._streaming = False
        try:
            await self.websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending stream chunk: {e}")

    def _handle_chat_history(self, jsonrpc_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat.history request."""
        from py.chat.history import ChatHistory

        conversation_id = params.get("conversation_id")
        limit = params.get("limit", 50)

        if not conversation_id:
            return self._error_response(jsonrpc_id, JSONRPC_ERRORS["INVALID_PARAMS"], "conversation_id is required")

        messages = ChatHistory.get_messages(conversation_id, limit=limit)

        return {
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "result": {
                "type": "history",
                "conversation_id": conversation_id,
                "messages": messages,
            },
        }

    def _handle_chat_clear(self, jsonrpc_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat.clear request."""
        from py.chat.history import ChatHistory

        conversation_id = params.get("conversation_id")

        if not conversation_id:
            return self._error_response(jsonrpc_id, JSONRPC_ERRORS["INVALID_PARAMS"], "conversation_id is required")

        ChatHistory.clear_conversation(conversation_id)

        return {
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "result": {
                "type": "cleared",
                "conversation_id": conversation_id,
            },
        }

    def _error_response(self, jsonrpc_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create an error response."""
        return {
            "jsonrpc": "2.0",
            "id": jsonrpc_id,
            "error": {
                "code": code,
                "message": message,
            },
        }


class ChatWebSocketManager:
    """Manages multiple WebSocket chat connections."""

    def __init__(self):
        self._connections: Dict[str, ChatWebSocket] = {}
        self._streams: Dict[str, Dict[str, Any]] = {}  # stream_id -> stream info

    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> ChatWebSocket:
        """Accept and register a new WebSocket connection."""
        chat_ws = ChatWebSocket(websocket, client_id)
        await chat_ws.connect()
        self._connections[chat_ws.client_id] = chat_ws
        return chat_ws

    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection."""
        if client_id in self._connections:
            self._connections[client_id].disconnect()
            del self._connections[client_id]

    async def send_to_client(self, client_id: str, message: Dict[str, Any]) -> None:
        """Send a message to a specific client."""
        if client_id in self._connections:
            await self._connections[client_id].websocket.send_json(message)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        for chat_ws in self._connections.values():
            await chat_ws.websocket.send_json(message)

    def get_client(self, client_id: str) -> Optional[ChatWebSocket]:
        """Get a specific client by ID."""
        return self._connections.get(client_id)

    @property
    def active_connections(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)


# Global chat WebSocket manager
chat_ws_manager = ChatWebSocketManager()
