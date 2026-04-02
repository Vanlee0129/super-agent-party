"""Multi-provider search aggregation."""

import asyncio
import json
from typing import List, Dict, Any, Optional

import py.web_search as ws


class SearchAggregator:
    """Aggregates results from multiple search providers."""

    PROVIDER_FUNCTIONS = {
        "duckduckgo": ws.DDGsearch_async,
        "tavily": ws.Tavily_search_async,
        "bing": ws.Bing_search_async,
        "google": ws.Google_search_async,
        "brave": ws.Brave_search_async,
        "exa": ws.Exa_search_async,
        "searxng": ws.searxng_async,
        "serper": ws.Serper_search_async,
        "bochaai": ws.bochaai_search_async,
        "jina": ws.jina_crawler_async,
        "crawl4ai": ws.Crawl4Ai_search_async,
        "firecrawl": ws.firecrawl_search_async,
    }

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available provider names."""
        return list(cls.PROVIDER_FUNCTIONS.keys())

    @classmethod
    def get_provider_requires_url(cls, provider: str) -> bool:
        """Check if provider requires a URL (for crawling) vs a query."""
        url_providers = {"jina", "crawl4ai", "firecrawl"}
        return provider.lower() in url_providers

    async def search(
        self,
        query: str,
        providers: List[str] = None,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search using multiple providers.

        Args:
            query: Search query
            providers: List of provider names to use (None = all)
            top_k: Number of results per provider

        Returns:
            Combined and deduplicated search results
        """
        if providers is None:
            providers = self.get_available_providers()

        # Filter valid providers
        valid_providers = [p for p in providers if p.lower() in self.PROVIDER_FUNCTIONS]

        if not valid_providers:
            return []

        # Execute searches in parallel
        tasks = []
        for provider in valid_providers:
            func = self.PROVIDER_FUNCTIONS[provider.lower()]
            if self.get_provider_requires_url(provider):
                # URL-based providers need a URL, not a query
                # Skip for now, they require separate handling
                continue
            tasks.append(self._search_provider(provider, func, query, top_k))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine results
        combined = []
        seen_urls = set()

        for provider_results in results:
            if isinstance(provider_results, Exception):
                continue

            try:
                parsed = self._parse_results(provider_results, provider)
                for item in parsed:
                    url = item.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        item["provider"] = provider
                        combined.append(item)
            except Exception:
                continue

        # Sort by score if available
        combined.sort(key=lambda x: x.get("score", 0), reverse=True)

        return combined[:top_k]

    async def _search_provider(
        self,
        provider: str,
        func,
        query: str,
        top_k: int,
    ) -> str:
        """Execute a single provider search."""
        try:
            result = await func(query)
            return result if isinstance(result, str) else json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _parse_results(
        self,
        raw_result: str,
        provider: str,
    ) -> List[Dict[str, Any]]:
        """Parse raw search results into normalized format."""
        try:
            if isinstance(raw_result, str):
                data = json.loads(raw_result)
            else:
                data = raw_result

            results = []

            # Handle different provider result formats
            if provider == "duckduckgo":
                results = self._parse_ddg_results(data)
            elif provider == "tavily":
                results = self._parse_tavily_results(data)
            elif provider in ["bing", "google", "brave", "exa", "serper"]:
                results = self._parse_standard_results(data)
            elif provider == "searxng":
                results = self._parse_searxng_results(data)
            else:
                results = self._parse_generic_results(data)

            return results

        except Exception:
            return []

    def _parse_ddg_results(self, data) -> List[Dict[str, Any]]:
        """Parse DuckDuckGo results."""
        results = []
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                return results

        items = data if isinstance(data, list) else data.get("results", [])
        for item in items:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", item.get("url", "")),
                "snippet": item.get("snippet", item.get("description", "")),
                "score": 1.0,
            })
        return results

    def _parse_tavily_results(self, data) -> List[Dict[str, Any]]:
        """Parse Tavily results."""
        results = []
        items = data if isinstance(data, list) else data.get("results", [])
        for item in items:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", item.get("snippet", "")),
                "score": item.get("score", 1.0),
            })
        return results

    def _parse_standard_results(self, data) -> List[Dict[str, Any]]:
        """Parse standard search results (Bing, Google, etc.)."""
        results = []
        items = data if isinstance(data, list) else data.get("results", data.get("items", []))
        for item in items:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", item.get("url", "")),
                "snippet": item.get("snippet", item.get("description", "")),
                "score": item.get("score", 1.0),
            })
        return results

    def _parse_searxng_results(self, data) -> List[Dict[str, Any]]:
        """Parse SearXNG results."""
        results = []
        items = data if isinstance(data, list) else data.get("results", [])
        for item in items:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", item.get("link", "")),
                "snippet": item.get("snippet", item.get("content", "")),
                "score": 1.0,
            })
        return results

    def _parse_generic_results(self, data) -> List[Dict[str, Any]]:
        """Parse generic search results."""
        results = []
        items = data if isinstance(data, list) else data.get("results", data.get("items", []))
        for item in items:
            if isinstance(item, dict):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", item.get("link", "")),
                    "snippet": item.get("snippet", item.get("content", item.get("description", ""))),
                    "score": item.get("score", 1.0),
                })
        return results

    async def crawl_url(
        self,
        url: str,
        provider: str = "jina",
    ) -> Dict[str, Any]:
        """
        Crawl a specific URL using a crawler provider.

        Args:
            url: The URL to crawl
            provider: Crawler provider to use

        Returns:
            Crawled content
        """
        if provider.lower() not in self.PROVIDER_FUNCTIONS:
            return {"error": f"Unknown provider: {provider}"}

        func = self.PROVIDER_FUNCTIONS[provider.lower()]

        try:
            if provider.lower() == "jina":
                result = await func(url)
            elif provider.lower() == "firecrawl":
                result = await func(url)
            elif provider.lower() == "crawl4ai":
                result = await func(url)
            else:
                result = await func(url)

            return {
                "url": url,
                "provider": provider,
                "content": result,
            }
        except Exception as e:
            return {"error": str(e), "url": url, "provider": provider}
