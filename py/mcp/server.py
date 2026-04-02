"""MCP Server implementation for Super Agent Party.

This module provides an MCP server that can host tools and resources
for consumption by MCP clients.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional

from py.mcp.protocol import MCPMethod, MCPRequest, MCPResponse

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP Server that exposes tools and resources to MCP clients.

    This server implements the MCP protocol and can be used with
    different transport mechanisms (stdio, SSE, WebSocket).
    """

    def __init__(
        self,
        server_name: str = "super-agent-party",
        server_version: str = "1.0.0",
    ) -> None:
        """Initialize MCP server.

        Args:
            server_name: Name of the server
            server_version: Version of the server
        """
        self.server_name = server_name
        self.server_version = server_version
        self._tools: Dict[str, Callable[..., Any]] = {}
        self._resources: Dict[str, Any] = {}
        self._prompts: Dict[str, Any] = {}
        self._initialized = False
        self._client_info: Optional[Dict[str, Any]] = None

    @property
    def tools(self) -> Dict[str, Callable[..., Any]]:
        """Get registered tools."""
        return self._tools

    @property
    def resources(self) -> Dict[str, Any]:
        """Get registered resources."""
        return self._resources

    @property
    def prompts(self) -> Dict[str, Any]:
        """Get registered prompts."""
        return self._prompts

    def register_tool(
        self,
        name: str,
        handler: Callable[..., Any],
        description: Optional[str] = None,
        input_schema: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a tool.

        Args:
            name: Tool name
            handler: Async function to call
            description: Tool description
            input_schema: JSON Schema for tool input
        """
        self._tools[name] = handler
        logger.info("Registered tool: %s", name)

    def register_resource(
        self,
        uri: str,
        content: Any,
        mime_type: str = "text/plain",
    ) -> None:
        """Register a resource.

        Args:
            uri: Resource URI
            content: Resource content
            mime_type: MIME type of the content
        """
        self._resources[uri] = {
            "content": content,
            "mime_type": mime_type,
        }
        logger.info("Registered resource: %s", uri)

    def register_prompt(
        self,
        name: str,
        prompt: Dict[str, Any],
    ) -> None:
        """Register a prompt.

        Args:
            name: Prompt name
            prompt: Prompt definition
        """
        self._prompts[name] = prompt
        logger.info("Registered prompt: %s", name)

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle an incoming MCP request.

        Args:
            request: The MCP request

        Returns:
            MCP response
        """
        try:
            method = request.method

            if method == MCPMethod.INITIALIZE.value:
                return await self._handle_initialize(request)
            elif method == MCPMethod.TOOLS_LIST.value:
                return await self._handle_tools_list(request)
            elif method == MCPMethod.TOOLS_CALL.value:
                return await self._handle_tools_call(request)
            elif method == MCPMethod.RESOURCES_LIST.value:
                return await self._handle_resources_list(request)
            elif method == MCPMethod.RESOURCES_READ.value:
                return await self._handle_resources_read(request)
            elif method == MCPMethod.PROMPTS_LIST.value:
                return await self._handle_prompts_list(request)
            elif method == MCPMethod.PROMPTS_GET.value:
                return await self._handle_prompts_get(request)
            else:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                )

        except Exception as e:
            logger.exception("Error handling request: %s", request.method)
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}",
                },
            )

    async def _handle_initialize(self, request: MCPRequest) -> MCPResponse:
        """Handle initialize request."""
        params = request.params or {}
        self._client_info = params.get("clientInfo", {})

        self._initialized = True

        return MCPResponse(
            id=request.id,
            result={
                "serverInfo": {
                    "name": self.server_name,
                    "version": self.server_version,
                },
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": True, "listChanged": True},
                    "prompts": {"listChanged": True},
                },
                "protocolVersion": "2024-11-05",
            },
        )

    async def _handle_tools_list(self, request: MCPRequest) -> MCPResponse:
        """Handle tools/list request."""
        tools = []
        for name, handler in self._tools.items():
            tool_def = {
                "name": name,
                "description": getattr(handler, "__doc__", "") or "",
                "inputSchema": getattr(handler, "_input_schema", {}),
            }
            tools.append(tool_def)

        return MCPResponse(
            id=request.id,
            result={"tools": tools},
        )

    async def _handle_tools_call(self, request: MCPRequest) -> MCPResponse:
        """Handle tools/call request."""
        params = request.params or {}
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self._tools:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32602,
                    "message": f"Unknown tool: {tool_name}",
                },
            )

        try:
            handler = self._tools[tool_name]
            result = await handler(**arguments)

            return MCPResponse(
                id=request.id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False),
                        }
                    ],
                    "isError": False,
                },
            )
        except Exception as e:
            return MCPResponse(
                id=request.id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: {str(e)}",
                        }
                    ],
                    "isError": True,
                },
            )

    async def _handle_resources_list(self, request: MCPRequest) -> MCPResponse:
        """Handle resources/list request."""
        resources = []
        for uri, resource in self._resources.items():
            resources.append({
                "uri": uri,
                "name": uri.split("/")[-1],
                "mimeType": resource.get("mime_type", "text/plain"),
            })

        return MCPResponse(
            id=request.id,
            result={"resources": resources},
        )

    async def _handle_resources_read(self, request: MCPRequest) -> MCPResponse:
        """Handle resources/read request."""
        params = request.params or {}
        uri = params.get("uri")

        if uri not in self._resources:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32602,
                    "message": f"Unknown resource: {uri}",
                },
            )

        resource = self._resources[uri]
        return MCPResponse(
            id=request.id,
            result={
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": resource.get("mime_type", "text/plain"),
                        "text": str(resource.get("content", "")),
                    }
                ]
            },
        )

    async def _handle_prompts_list(self, request: MCPRequest) -> MCPResponse:
        """Handle prompts/list request."""
        prompts = []
        for name, prompt in self._prompts.items():
            prompts.append({
                "name": name,
                "description": prompt.get("description", ""),
                "arguments": prompt.get("arguments", []),
            })

        return MCPResponse(
            id=request.id,
            result={"prompts": prompts},
        )

    async def _handle_prompts_get(self, request: MCPRequest) -> MCPResponse:
        """Handle prompts/get request."""
        params = request.params or {}
        name = params.get("name")
        arguments = params.get("arguments", {})

        if name not in self._prompts:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32602,
                    "message": f"Unknown prompt: {name}",
                },
            )

        prompt = self._prompts[name]
        return MCPResponse(
            id=request.id,
            result={
                "messages": prompt.get("messages", []),
            },
        )

    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a raw JSON-RPC message.

        Args:
            message: Raw message dictionary

        Returns:
            Response dictionary or None for notifications
        """
        request = MCPRequest(
            jsonrpc=message.get("jsonrpc", "2.0"),
            id=message.get("id"),
            method=message.get("method", ""),
            params=message.get("params"),
        )

        # Handle notifications (no id)
        if request.id is None:
            # Process but don't respond
            await self.handle_request(request)
            return None

        response = await self.handle_request(request)
        return response.to_dict()
