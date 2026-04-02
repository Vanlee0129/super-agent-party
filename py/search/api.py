"""FastAPI routes for web search."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from py.search.aggregator import SearchAggregator
from py.search.reranker import SearchReranker
from py.get_setting import load_settings


router = APIRouter(prefix="/api/v1/search", tags=["search"])


# ============== Request/Response Models ==============

class SearchProvider(BaseModel):
    """Search provider model."""

    name: str
    enabled: bool
    api_key_required: bool
    requires_api_key: bool = False


class SearchResult(BaseModel):
    """Search result model."""

    title: str
    url: str
    snippet: str
    provider: str
    score: float = 1.0


class SearchRequest(BaseModel):
    """Search request model."""

    query: str
    providers: Optional[List[str]] = None
    top_k: int = 10
    rerank: bool = False


class ProviderConfig(BaseModel):
    """Provider configuration model."""

    name: str
    enabled: bool
    requires_api_key: bool
    config: dict = {}


# ============== API Endpoints ==============

@router.get("/providers", response_model=List[SearchProvider])
async def list_providers():
    """
    List all available search providers.

    Returns:
        List of search providers
    """
    settings = await load_settings()
    web_search_settings = settings.get("webSearch", {})

    # Default providers
    default_providers = [
        "duckduckgo",
        "tavily",
        "bing",
        "google",
        "brave",
        "exa",
        "searxng",
        "jina",
        "crawl4ai",
        "firecrawl",
    ]

    # Providers that require API keys
    api_key_providers = {
        "tavily": True,
        "bing": True,
        "google": True,
        "brave": True,
        "exa": True,
        "serper": True,
        "bochaai": True,
        "jina": False,  # Has free tier
        "firecrawl": True,
    }

    providers = []
    enabled_providers = web_search_settings.get("enabledProviders", [])

    for name in default_providers:
        enabled = name in enabled_providers if enabled_providers else True
        providers.append(
            SearchProvider(
                name=name,
                enabled=enabled,
                api_key_required=api_key_providers.get(name, False),
            )
        )

    return providers


@router.post("/query", response_model=List[SearchResult])
async def search(
    request: SearchRequest,
    api_key: Optional[str] = Header(None),
):
    """
    Execute web search using specified providers.

    Args:
        request: Search request with query, providers, top_k, rerank
        api_key: Optional API key for authenticated providers

    Returns:
        List of search results
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    aggregator = SearchAggregator()

    try:
        results = await aggregator.search(
            query=request.query.strip(),
            providers=request.providers,
            top_k=request.top_k,
        )

        # Apply reranking if requested
        if request.rerank and results:
            results = await SearchReranker.rerank(
                request.query.strip(),
                results,
                top_n=request.top_k,
            )

        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("snippet", ""),
                provider=r.get("provider", "unknown"),
                score=r.get("score", 1.0),
            )
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/providers/{provider}/test")
async def test_provider(
    provider: str,
    api_key: Optional[str] = Header(None),
):
    """
    Test a search provider.

    Args:
        provider: Provider name
        api_key: Optional API key for the provider

    Returns:
        Test result
    """
    aggregator = SearchAggregator()

    if provider.lower() not in aggregator.PROVIDER_FUNCTIONS:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    # Test with a simple query
    test_query = "test query"

    try:
        results = await aggregator.search(
            query=test_query,
            providers=[provider],
            top_k=3,
        )

        return {
            "provider": provider,
            "success": True,
            "result_count": len(results),
            "results": results[:3] if results else [],
        }
    except Exception as e:
        return {
            "provider": provider,
            "success": False,
            "error": str(e),
        }


@router.get("/providers/{provider}/config", response_model=ProviderConfig)
async def get_provider_config(provider: str):
    """
    Get provider configuration.

    Args:
        provider: Provider name

    Returns:
        Provider configuration
    """
    settings = await load_settings()
    web_search_settings = settings.get("webSearch", {})

    all_providers = [
        "duckduckgo",
        "tavily",
        "bing",
        "google",
        "brave",
        "exa",
        "searxng",
        "serper",
        "bochaai",
        "jina",
        "crawl4ai",
        "firecrawl",
    ]

    if provider.lower() not in all_providers:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    # Get provider-specific settings
    provider_settings = web_search_settings.get(f"{provider}_settings", {})

    api_key_providers = {
        "tavily", "bing", "google", "brave", "exa", "serper", "bochaai", "firecrawl"
    }

    return ProviderConfig(
        name=provider,
        enabled=web_search_settings.get("enabledProviders", []),
        requires_api_key=provider.lower() in api_key_providers,
        config=provider_settings,
    )


@router.put("/providers/{provider}/config")
async def update_provider_config(
    provider: str,
    config_update: dict,
):
    """
    Update provider configuration.

    Args:
        provider: Provider name
        config_update: Configuration updates

    Returns:
        Success message
    """
    settings = await load_settings()

    if "webSearch" not in settings:
        settings["webSearch"] = {}

    web_search_settings = settings["webSearch"]

    # Update provider-specific settings
    provider_key = f"{provider}_settings"
    current_config = web_search_settings.get(provider_key, {})

    web_search_settings[provider_key] = {**current_config, **config_update}

    # Save settings
    from py.get_setting import save_settings
    await save_settings(settings)

    return {"success": True, "message": f"Provider {provider} config updated"}


@router.post("/crawl")
async def crawl_url(
    url: str,
    provider: str = "jina",
):
    """
    Crawl a specific URL using a crawler provider.

    Args:
        url: The URL to crawl
        provider: Crawler provider to use

    Returns:
        Crawled content
    """
    aggregator = SearchAggregator()

    try:
        result = await aggregator.crawl_url(url, provider)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crawl failed: {str(e)}")
