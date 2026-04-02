"""BochaAI search provider plugin.

Refactored from web_search.py
"""

import asyncio
import json
import logging
from typing import Any, Dict, List

import requests

from py.plugins.base import PluginMetadata
from py.search.providers.base import SearchProvider

logger = logging.getLogger(__name__)


class BochaAISearchProvider(SearchProvider):
    """BochaAI search provider implementation."""

    provider_name = "bochaai"

    def __init__(self) -> None:
        super().__init__()
        self._max_results = 10
        self._api_key = ""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="search.provider.bochaai",
            name="BochaAI Search",
            version="1.0.0",
            description="Search provider using BochaAI",
        )

    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize BochaAI search."""
        self._max_results = config.get("max_results", 10)
        self._api_key = config.get("api_key", "")

    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Execute BochaAI search."""
        if not self._api_key:
            return [{"error": "API key not configured"}]

        def sync_search():
            try:
                url = "https://api.bochaai.com/v1/web-search"
                headers = {
                    'Authorization': f'Bearer {self._api_key}',
                    'Content-Type': 'application/json'
                }
                payload = json.dumps({
                    "query": query,
                    "summary": True,
                    "count": max_results or self._max_results
                })

                response = requests.post(url, headers=headers, data=payload, timeout=30)

                if response.status_code == 200:
                    result_data = response.json()
                    formatted_results = []
                    search_results = result_data.get('data', {}).get('webPages', {}).get('value', [])

                    for item in search_results:
                        formatted_item = {
                            'title': item.get('name', 'No title'),
                            'link': item.get('url', ''),
                            'displayUrl': item.get('displayUrl', ''),
                            'snippet': item.get('snippet', '')
                        }
                        formatted_results.append(formatted_item)

                    return json.dumps(formatted_results, indent=2, ensure_ascii=False)

                return "[]"

            except Exception as e:
                logger.error(f"BochaAI search error: {e}")
                return "[]"

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, sync_search)
        except Exception as e:
            logger.error(f"BochaAI search exception: {e}")
            return []

    def get_tool_definition(self) -> Dict[str, Any]:
        """Return tool definition."""
        return {
            "type": "function",
            "function": {
                "name": "bochaai_search_async",
                "description": "Search using BochaAI web search",
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
