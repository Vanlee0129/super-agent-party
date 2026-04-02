"""DuckDuckGo search provider plugin.

Refactored from web_search.py
"""

import asyncio
import logging
from typing import Any, Dict, List

from langchain_community.tools import DuckDuckGoSearchResults

from py.plugins.base import PluginMetadata
from py.search.providers.base import SearchProvider

logger = logging.getLogger(__name__)


class DuckDuckGoSearchProvider(SearchProvider):
    """DuckDuckGo search provider implementation."""

    provider_name = "duckduckgo"

    def __init__(self) -> None:
        super().__init__()
        self._max_results = 10

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="search.provider.duckduckgo",
            name="DuckDuckGo Search",
            version="1.0.0",
            description="Search provider using DuckDuckGo",
        )

    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize DuckDuckGo search."""
        self._max_results = config.get("max_results", 10)

    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Execute DuckDuckGo search."""
        try:
            def sync_search():
                try:
                    dds = DuckDuckGoSearchResults(
                        num_results=max_results or self._max_results,
                        output_format="json"
                    )
                    results = dds.invoke(query)
                    return results
                except Exception as e:
                    logger.error(f"DuckDuckGo search error: {e}")
                    return ""

            return await asyncio.get_event_loop().run_in_executor(None, sync_search)
        except Exception as e:
            logger.error(f"DuckDuckGo search exception: {e}")
            return []

    def get_tool_definition(self) -> Dict[str, Any]:
        """Return tool definition."""
        return {
            "type": "function",
            "function": {
                "name": "DDGsearch_async",
                "description": "Search DuckDuckGo for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search keywords, can be multiple words separated by spaces",
                        },
                    },
                    "required": ["query"],
                },
            },
        }
