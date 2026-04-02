"""SearXNG search provider plugin.

Refactored from web_search.py
"""

import asyncio
import json
import logging
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup

from py.plugins.base import PluginMetadata
from py.search.providers.base import SearchProvider

logger = logging.getLogger(__name__)


class SearXNGSearchProvider(SearchProvider):
    """SearXNG search provider implementation."""

    provider_name = "searxng"

    def __init__(self) -> None:
        super().__init__()
        self._max_results = 10
        self._api_url = "http://127.0.0.1:8080"

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="search.provider.searxng",
            name="SearXNG Search",
            version="1.0.0",
            description="Search provider using SearXNG",
        )

    async def _initialize(self, config: Dict[str, Any]) -> None:
        """Initialize SearXNG search."""
        self._max_results = config.get("max_results", 10)
        self._api_url = config.get("api_url", "http://127.0.0.1:8080")

    async def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Execute SearXNG search."""
        def sync_search():
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                params = {
                    "q": query,
                    "categories": "general",
                    "count": max_results or self._max_results
                }

                response = requests.get(
                    self._api_url + "/search",
                    headers=headers,
                    params=params,
                    timeout=30
                )
                html_content = response.text

                soup = BeautifulSoup(html_content, 'html.parser')
                results = []

                for result in soup.find_all('article', class_='result'):
                    title = result.find('h3').get_text() if result.find('h3') else 'No title'

                    link_elem = result.find('a', class_='url_header')
                    if not link_elem:
                        h3 = result.find('h3')
                        link_elem = h3.find('a') if h3 else None

                    link = link_elem['href'] if link_elem and link_elem.get('href') else 'No link'

                    snippet = result.find('p', class_='content').get_text() if result.find('p', class_='content') else 'No snippet'

                    results.append({
                        'title': title,
                        'link': link,
                        'snippet': snippet
                    })

                return json.dumps(results, indent=2, ensure_ascii=False)

            except Exception as e:
                logger.error(f"SearXNG search error: {e}")
                return "[]"

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, sync_search)
        except Exception as e:
            logger.error(f"SearXNG search exception: {e}")
            return []

    def get_tool_definition(self) -> Dict[str, Any]:
        """Return tool definition."""
        return {
            "type": "function",
            "function": {
                "name": "searxng_async",
                "description": "Search using SearXNG open source meta search engine",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query, supports natural language and multi-keyword queries",
                        },
                    },
                    "required": ["query"],
                },
            },
        }
