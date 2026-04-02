"""Main FastAPI server with plugin architecture."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from py.core.config import config, SKILLS_DIR
from py.core.events import events
from py.plugins.registry import registry
from py.plugins.loader import PluginLoader
from py.plugins.hooks import hooks, Hook
from py.skills import SkillManager
from py.mcp.client import MCPClient
from py.models import setup_providers, registry as model_registry
from py.bots.api import router as bots_router
from py.bots.registry import initialize_managers, BotRegistry
from py.chat.routes import router as chat_router
from py.chat.websocket_handler import ChatWebSocketManager
from py.chat.history import ChatHistory
from py.chat.streamer import ChatStreamer

logger = logging.getLogger(__name__)


# Global instances
_loader = PluginLoader()
_skill_manager: Optional[SkillManager] = None
_mcp_clients: Dict[str, MCPClient] = {}


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self) -> None:
        self._connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        self._connections[client_id] = websocket
        logger.info(f"Client connected: {client_id}")

    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection."""
        if client_id in self._connections:
            del self._connections[client_id]
            logger.info(f"Client disconnected: {client_id}")

    async def send(self, client_id: str, message: Dict[str, Any]) -> None:
        """Send a message to a specific client."""
        if client_id in self._connections:
            await self._connections[client_id].send_json(message)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        for websocket in self._connections.values():
            await websocket.send_json(message)


connection_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown hooks."""
    global _skill_manager

    # Startup
    logger.info("Starting server...")

    # Emit before_startup hook
    hooks.emit(Hook.BEFORE_STARTUP)

    # Load plugins
    loaded_plugins = _loader.load_builtin_plugins()
    logger.info(f"Loaded {len(loaded_plugins)} plugins")

    # Load skills
    _skill_manager = SkillManager(SKILLS_DIR)
    _skill_manager.load_all()
    logger.info(f"Loaded skills from {SKILLS_DIR}")

    # Setup model providers
    setup_providers()
    logger.info("Initializing bot managers...")
    initialize_managers()
    logger.info(f"Bot managers initialized: {BotRegistry.list_platforms()}")
    logger.info("Model providers initialized")

    # Emit after_startup hook
    hooks.emit(Hook.AFTER_STARTUP)

    logger.info("Server started successfully")

    yield

    # Shutdown
    logger.info("Shutting down server...")

    # Emit before_shutdown hook
    hooks.emit(Hook.BEFORE_SHUTDOWN)

    # Disconnect all MCP clients
    for client_id, client in _mcp_clients.items():
        if client.is_connected:
            await client.disconnect()
    _mcp_clients.clear()

    # Emit after_shutdown hook
    hooks.emit(Hook.AFTER_SHUTDOWN)

    logger.info("Server shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Super Agent Party API",
    description="Plugin-based AI agent server with WebSocket support",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include bot management router
app.include_router(bots_router)

# Include chat API router
app.include_router(chat_router)


# ==================== HTTP Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint returning server info."""
    return {
        "name": "Super Agent Party API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "plugins": len(registry.list_all()),
        "skills": len(_skill_manager.list_all()) if _skill_manager else 0,
    }


# ==================== WebSocket Endpoint ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for JSON-RPC messages."""
    client_id = str(id(websocket))
    await connection_manager.connect(client_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            response = await handle_jsonrpc(data)
            if response:
                await connection_manager.send(client_id, response)
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        connection_manager.disconnect(client_id)


async def handle_jsonrpc(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Handle incoming JSON-RPC request."""
    method = data.get("method")
    request_id = data.get("id")
    params = data.get("params", {})

    if not method:
        return error_response(request_id, -32600, "Invalid Request: method is required")

    # Emit on_request hook
    hooks.emit(Hook.ON_REQUEST, method=method, params=params)

    try:
        if method == "chat.complete":
            result = await handle_chat_complete(params)
        elif method == "chat.complete_stream":
            result = await handle_chat_complete_stream(params)
        elif method == "skills.list":
            result = handle_skills_list(params)
        elif method == "skills.execute":
            result = await handle_skills_execute(params)
        elif method == "mcp.connect":
            result = await handle_mcp_connect(params)
        elif method == "mcp.tools":
            result = await handle_mcp_tools(params)
        elif method == "settings.get":
            result = handle_settings_get(params)
        elif method == "settings.update":
            result = handle_settings_update(params)
        else:
            return error_response(request_id, -32601, f"Method not found: {method}")

        return success_response(request_id, result)

    except Exception as e:
        logger.exception(f"Error handling method {method}")
        return error_response(request_id, -32603, str(e))


def success_response(request_id: Any, result: Any) -> Dict[str, Any]:
    """Create a successful JSON-RPC response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }


def error_response(request_id: Any, code: int, message: str) -> Dict[str, Any]:
    """Create an error JSON-RPC response."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message,
        },
    }


# ==================== Message Handlers ====================

async def handle_chat_complete(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle non-streaming chat completion."""
    messages = params.get("messages", [])
    model = params.get("model", "gpt-4")
    provider = params.get("provider", "openai")

    provider_config = model_registry.get_config(provider)
    if not provider_config:
        raise ValueError(f"Provider not configured: {provider}")

    provider_instance = model_registry.get_instance(provider)
    if not provider_instance:
        provider_instance = model_registry.create(provider_config)

    response = await provider_instance.chat_complete(messages, model=model)
    return response.to_dict() if hasattr(response, "to_dict") else response


async def handle_chat_complete_stream(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle streaming chat completion."""
    messages = params.get("messages", [])
    model = params.get("model", "gpt-4")
    provider = params.get("provider", "openai")

    provider_config = model_registry.get_config(provider)
    if not provider_config:
        raise ValueError(f"Provider not configured: {provider}")

    provider_instance = model_registry.get_instance(provider)
    if not provider_instance:
        provider_instance = model_registry.create(provider_config)

    chunks = []
    async for chunk in provider_instance.chat_complete_stream(messages, model=model):
        chunks.append(chunk.to_dict() if hasattr(chunk, "to_dict") else chunk)

    return chunks


def handle_skills_list(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle skills.list request."""
    category = params.get("category")
    all_skills = _skill_manager.list_all()

    if category:
        all_skills = _skill_manager.list_by_category(category)

    return [
        {
            "id": s.metadata.id,
            "name": s.metadata.name,
            "description": s.metadata.description,
            "category": s.metadata.category,
            "version": s.metadata.version,
        }
        for s in all_skills
    ]


async def handle_skills_execute(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle skills.execute request."""
    skill_id = params.get("skill_id")
    parameters = params.get("parameters", {})

    if not skill_id:
        raise ValueError("skill_id is required")

    execution = await _skill_manager.execute(skill_id, parameters)

    return {
        "skill_id": execution.skill_id,
        "result": execution.result,
        "error": execution.error,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
    }


async def handle_mcp_connect(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle mcp.connect request."""
    server_id = params.get("server_id")
    command = params.get("command")
    url = params.get("url")
    args = params.get("args")
    env = params.get("env")
    cwd = params.get("cwd")
    headers = params.get("headers")

    if not server_id:
        raise ValueError("server_id is required")

    client = MCPClient()

    if command:
        await client.connect_stdio(command=command, args=args, env=env, cwd=cwd)
    elif url:
        await client.connect_websocket(url=url, headers=headers)
    else:
        raise ValueError("Either command or url is required")

    await client.initialize()

    _mcp_clients[server_id] = client

    return {
        "server_id": server_id,
        "connected": True,
        "capabilities": client._capabilities,
    }


async def handle_mcp_tools(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handle mcp.tools request."""
    server_id = params.get("server_id")

    if not server_id:
        raise ValueError("server_id is required")

    client = _mcp_clients.get(server_id)
    if not client:
        raise ValueError(f"MCP client not found: {server_id}")

    tools = await client.list_tools()
    return tools


def handle_settings_get(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle settings.get request."""
    key = params.get("key")
    if key:
        return {key: config.get(key)}
    return config.to_dict()


def handle_settings_update(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle settings.update request."""
    updates = params.get("updates", {})
    if not updates:
        raise ValueError("updates is required")

    config.update(updates)
    return {"updated": True, "settings": config.to_dict()}


# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info",
    )
