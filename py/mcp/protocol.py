"""MCP Protocol definitions - JSON-RPC 2.0 based."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Dict
import uuid
import json


class MCPMethod(Enum):
    """MCP protocol methods."""

    INITIALIZE = "initialize"
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"
    NOTIFICATION_INITIALIZED = "notifications/initialized"
    NOTIFICATION_CANCELLED = "notifications/cancelled"


@dataclass
class MCPRequest:
    """MCP JSON-RPC 2.0 request."""

    jsonrpc: str = "2.0"
    id: Optional[str | int] = None
    method: str = ""
    params: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"jsonrpc": self.jsonrpc, "method": self.method}
        if self.id is not None:
            result["id"] = self.id
        if self.params is not None:
            result["params"] = self.params
        return result


@dataclass
class MCPResponse:
    """MCP JSON-RPC 2.0 response."""

    jsonrpc: str = "2.0"
    id: Optional[str | int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPResponse":
        """Create response from dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            result=data.get("result"),
            error=data.get("error"),
        )


@dataclass
class MCPError:
    """MCP error object."""

    code: int
    message: str
    data: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result


def create_request(
    method: MCPMethod | str,
    params: Optional[Dict[str, Any]] = None,
    request_id: Optional[str | int] = None,
) -> MCPRequest:
    """Create an MCP request.

    Args:
        method: The MCP method to call
        params: Optional parameters for the method
        request_id: Optional request ID (auto-generated if not provided)

    Returns:
        MCPRequest instance
    """
    if isinstance(method, MCPMethod):
        method_str = method.value
    else:
        method_str = method

    if request_id is None:
        request_id = str(uuid.uuid4())

    return MCPRequest(
        jsonrpc="2.0",
        id=request_id,
        method=method_str,
        params=params,
    )


def parse_response(data: Dict[str, Any]) -> MCPResponse:
    """Parse a JSON-RPC 2.0 response.

    Args:
        data: Raw response dictionary from JSON

    Returns:
        MCPResponse instance

    Raises:
        ValueError: If the response is invalid
    """
    if not isinstance(data, dict):
        raise ValueError(f"Response must be a dictionary, got {type(data)}")

    jsonrpc = data.get("jsonrpc")
    if jsonrpc != "2.0":
        raise ValueError(f"Invalid JSON-RPC version: {jsonrpc}")

    return MCPResponse.from_dict(data)


def serialize_request(request: MCPRequest) -> str:
    """Serialize an MCP request to JSON string.

    Args:
        request: The request to serialize

    Returns:
        JSON string
    """
    return json.dumps(request.to_dict())


def deserialize_response(data: str) -> MCPResponse:
    """Deserialize a JSON string to MCP response.

    Args:
        data: JSON string

    Returns:
        MCPResponse instance
    """
    parsed = json.loads(data)
    return parse_response(parsed)
