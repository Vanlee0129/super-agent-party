"""Base class for search providers."""

from abc import abstractmethod
from typing import Any, Dict, List

from py.plugins.base import Plugin, PluginMetadata


class SearchProvider(Plugin):
    """Abstract base class for search provider plugins."""

    def __init__(self) -> None:
        super().__init__()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        raise NotImplementedError

    @property
    def metadata(self) -> PluginMetadata:
        """Return the plugin metadata."""
        return PluginMetadata(
            id=f"search.provider.{self.provider_name}",
            name=f"{self.provider_name.title()} Search Provider",
            version="1.0.0",
            description=f"Search provider plugin for {self.provider_name}",
        )

    @abstractmethod
    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the search provider."""
        raise NotImplementedError

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Execute a search query.

        Args:
            query: Search query string.
            max_results: Maximum number of results to return.

        Returns:
            List of search result dictionaries.
        """
        raise NotImplementedError

    def get_tool_definition(self) -> Dict[str, Any]:
        """Return tool definition for this provider."""
        return {
            "type": "function",
            "function": {
                "name": f"{self.provider_name}_search",
                "description": f"Search using {self.provider_name}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                    },
                    "required": ["query"],
                },
            },
        }
