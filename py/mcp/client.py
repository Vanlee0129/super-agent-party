"""MCP Client - high-level client for Model Context Protocol."""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

from py.mcp.protocol import (
    MCPMethod,
    MCPRequest,
    MCPResponse,
    create_request,
    parse_response,
)
from py.mcp.transport.base import Transport
from py.mcp.transport.stdio import StdioTransport
from py.mcp.transport.websocket import WebSocketTransport

logger = logging.getLogger(__name__)


class MCPClient:
    """High-level MCP client with transport abstraction.

    This client provides a simple interface for interacting with
    MCP servers using different transport mechanisms.
    """

    def __init__(self) -> None:
        """Initialize MCP client."""
        self._transport: Optional[Transport] = None
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._server_info: Optional[Dict[str, Any]] = None
        self._capabilities: Optional[Dict[str, Any]] = None
        self._initialized: bool = False

    @property
    def transport(self) -> Optional[Transport]:
        """Get the current transport."""
        return self._transport

    @property
    def is_connected(self) -> bool:
        """Check if client is connected to a server."""
        return self._transport is not None and self._transport.connected

    @property
    def is_initialized(self) -> bool:
        """Check if MCP session is initialized."""
        return self._initialized

    async def connect_stdio(
        self,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> None:
        """Connect to an MCP server using stdio transport.

        Args:
            command: The command to run (e.g., 'npx', 'uv', 'python')
            args: Command arguments
            env: Environment variables
            cwd: Working directory
        """
        transport = StdioTransport()
        await transport.start_server(command=command, args=args, env=env, cwd=cwd)
        self._transport = transport
        self._transport.on_message(self._handle_message)
        self._transport.on_error(self._handle_error)
        logger.info("Connected via stdio transport")

    async def connect_websocket(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Connect to an MCP server using WebSocket transport.

        Args:
            url: WebSocket server URL
            headers: Optional HTTP headers
        """
        transport = WebSocketTransport(url=url, headers=headers)
        await transport.start_client()
        self._transport = transport
        self._transport.on_message(self._handle_message)
        self._transport.on_error(self._handle_error)
        logger.info("Connected via WebSocket transport")

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._transport:
            await self._transport.disconnect()
            self._transport = None
        self._pending_requests.clear()
        self._initialized = False
        logger.info("Disconnected from MCP server")

    async def initialize(
        self,
        client_name: str = "mcp-python-client",
        client_version: str = "1.0.0",
    ) -> Dict[str, Any]:
        """Send initialization request to the MCP server.

        Args:
            client_name: Name of the client
            client_version: Version of the client

        Returns:
            Server capabilities and info
        """
        if not self._transport:
            raise RuntimeError("Not connected to a server")

        params = {
            "clientInfo": {
                "name": client_name,
                "version": client_version,
            },
            "protocolVersion": "2024-11-05",
        }

        response = await self._send_request(
            create_request(MCPMethod.INITIALIZE, params)
        )

        self._server_info = response.result.get("serverInfo", {})
        self._capabilities = response.result.get("capabilities", {})
        self._initialized = True

        # Send initialized notification
        await self._send_notification(MCPMethod.NOTIFICATION_INITIALIZED)

        logger.info(
            "Initialized with server: %s (%s)",
            self._server_info.get("name"),
            self._server_info.get("version"),
        )

        return self._capabilities

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get the list of available tools from the server.

        Returns:
            List of tool definitions
        """
        response = await self._send_request(
            create_request(MCPMethod.TOOLS_LIST)
        )
        tools = response.result.get("tools", [])
        logger.info("Listed %d tools", len(tools))
        return tools

    async def call_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call a tool on the MCP server.

        Args:
            name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")

        params = {
            "name": name,
            "arguments": arguments or {},
        }

        response = await self._send_request(
            create_request(MCPMethod.TOOLS_CALL, params)
        )

        result = response.result
        logger.debug("Called tool '%s': %s", name, result)
        return result

    async def list_resources(self) -> List[Dict[str, Any]]:
        """Get the list of available resources from the server.

        Returns:
            List of resource definitions
        """
        response = await self._send_request(
            create_request(MCPMethod.RESOURCES_LIST)
        )
        resources = response.result.get("resources", [])
        logger.info("Listed %d resources", len(resources))
        return resources

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource from the server.

        Args:
            uri: Resource URI to read

        Returns:
            Resource contents
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")

        params = {"uri": uri}

        response = await self._send_request(
            create_request(MCPMethod.RESOURCES_READ, params)
        )

        result = response.result
        logger.debug("Read resource '%s': %s", uri, result)
        return result

    async def list_prompts(self) -> List[Dict[str, Any]]:
        """Get the list of available prompts from the server.

        Returns:
            List of prompt definitions
        """
        response = await self._send_request(
            create_request(MCPMethod.PROMPTS_LIST)
        )
        prompts = response.result.get("prompts", [])
        logger.info("Listed %d prompts", len(prompts))
        return prompts

    async def get_prompt(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get a prompt from the server.

        Args:
            name: Name of the prompt to get
            arguments: Prompt arguments

        Returns:
            Prompt contents
        """
        if not self._initialized:
            raise RuntimeError("Client not initialized. Call initialize() first.")

        params = {"name": name, "arguments": arguments or {}}

        response = await self._send_request(
            create_request(MCPMethod.PROMPTS_GET, params)
        )

        result = response.result
        logger.debug("Got prompt '%s': %s", name, result)
        return result

    async def _send_request(self, request: MCPRequest) -> MCPResponse:
        """Send a request and wait for response.

        Args:
            request: The request to send

        Returns:
            Response from server

        Raises:
            RuntimeError: If not connected
            TimeoutError: If request times out
            Exception: If server returns an error
        """
        if not self._transport:
            raise RuntimeError("Not connected to a server")

        request_id = str(request.id)
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future

        try:
            await self._transport.send(request.to_dict())

            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(future, timeout=60.0)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Request {request_id} timed out")

            # Check for error response
            if response.error:
                error = response.error
                raise Exception(
                    f"MCP error {error.get('code')}: {error.get('message')}"
                )

            return response

        finally:
            self._pending_requests.pop(request_id, None)

    async def _send_notification(
        self,
        method: MCPMethod,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send a notification (no response expected).

        Args:
            method: The notification method
            params: Optional notification parameters
        """
        if not self._transport:
            raise RuntimeError("Not connected to a server")

        request = create_request(method, params)
        await self._transport.send(request.to_dict())

    def _handle_message(self, message: dict) -> None:
        """Handle incoming message from transport.

        Args:
            message: Raw message dictionary
        """
        try:
            # Check if this is a response to a pending request
            if "id" in message:
                request_id = str(message["id"])
                future = self._pending_requests.get(request_id)

                if future and not future.done():
                    try:
                        response = parse_response(message)
                        future.set_result(response)
                    except Exception as e:
                        future.set_exception(e)
                else:
                    logger.debug("Received response for unknown request: %s", request_id)

            # Check if this is a request from server (not supported in client mode)
            elif "method" in message:
                logger.debug("Received server request: %s", message.get("method"))

        except Exception as e:
            logger.exception("Error handling message: %s", e)

    def _handle_error(self, error: Exception) -> None:
        """Handle error from transport.

        Args:
            error: The exception that occurred
        """
        logger.error("Transport error: %s", error)

        # Cancel all pending requests
        for request_id, future in self._pending_requests.items():
            if not future.done():
                future.set_exception(error)

    def on_message(self, handler: Callable[[dict], None]) -> None:
        """Set custom message handler.

        Args:
            handler: Callback function for received messages
        """
        if self._transport:
            self._transport.on_message(handler)

    def on_error(self, handler: Callable[[Exception], None]) -> None:
        """Set custom error handler.

        Args:
            handler: Callback function for errors
        """
        if self._transport:
            self._transport.on_error(handler)
