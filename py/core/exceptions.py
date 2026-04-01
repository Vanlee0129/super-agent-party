"""Custom exceptions for Super Agent Party."""

from typing import Optional


class SuperAgentError(Exception):
    """Base exception for all Super Agent Party errors."""

    pass


class PluginError(SuperAgentError):
    """Exception raised for plugin-related errors."""

    pass


class SkillError(SuperAgentError):
    """Exception raised for skill-related errors."""

    pass


class MCPError(SuperAgentError):
    """Exception raised for MCP (Model Context Protocol) errors."""

    pass


class ModelError(SuperAgentError):
    """Exception raised for model-related errors."""

    pass


class ConfigurationError(SuperAgentError):
    """Exception raised for configuration-related errors."""

    pass


class APIError(SuperAgentError):
    """Exception raised for API-related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
