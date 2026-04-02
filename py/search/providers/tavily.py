"""Tavily search provider plugin.

Refactored from web_search.py
"""

import asyncio
import logging
from typing import Any, Dict, List

from tavily import TavilyClient

from py.plugins.base import PluginMetadata
from py.search.providers.base import SearchProvider

logger = logging.getLogger(__name__)


class TavilySearchProvider(SearchProvider):
    """Tavily search provider implementation."""

    provider_name = "tavily"

    def __init__(self) -> None:
        super().__init__()
        self._max_results = 10
        self._api_key = ""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="search.provider.tavily",
            name="Tavily Search",
            version="1.0.0",
            description="Search provider using Tavily",
        )

    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize Tavily search."""
        self._max_results = config.get("max_results", 10)
        self._api_key = config.get("api_key", "")

    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Execute Tavily search."""
        if not self._api_key:
            return [{"error": "API key not configured"}]

        try:
            def sync_search():
                try:
                    client = TavilyClient(api_key=self._api_key)
                    results = client.search(
                        query=query,
                        max_results=max_results or self._max_results
                    )
                    return results
                except Exception as e:
                    logger.error(f"Tavily search error: {e}")
                    return {"results": []}

            return await asyncio.get_event_loop().run_in_executor(None, sync_search)
        except Exception as e:
            logger.error(f"Tavily search exception: {e}")
            return {"results": []}

    def get_tool_definition(self) -> Dict[str, Any]:
        """Return tool definition."""
        return {
            "type": "function",
            "function": {
                "name": "tavily_search",
                "description": "Search using Tavily AI search",
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
