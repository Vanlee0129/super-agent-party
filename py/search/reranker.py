"""Result reranking for search."""

import asyncio
import httpx
from typing import List, Dict, Any

from py.get_setting import load_settings


class SearchReranker:
    """Reranks search results using Jina or VLLM reranking models."""

    @classmethod
    async def rerank(
        cls,
        query: str,
        results: List[Dict[str, Any]],
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Rerank search results.

        Args:
            query: Original search query
            results: List of search results with content, url, title
            top_n: Number of results to return

        Returns:
            Reranked results
        """
        if not results:
            return []

        settings = await load_settings()
        provider_id = settings.get("webSearch", {}).get("selectedProvider", "jina")
        provider = cls._find_provider(provider_id, settings)

        if not provider:
            # No reranking available, return original results
            return results[:top_n]

        documents = [r.get("snippet", r.get("content", "")) for r in results]

        try:
            if provider["vendor"] == "jina":
                return await cls._rerank_jina(query, results, documents, top_n, provider)
            elif provider["vendor"] == "Vllm":
                return await cls._rerank_vllm(query, results, documents, top_n, provider)
            else:
                return results[:top_n]
        except Exception:
            return results[:top_n]

    @classmethod
    def _find_provider(cls, provider_id: str, settings: dict) -> dict:
        """Find reranking provider from settings."""
        model_providers = settings.get("modelProviders", [])

        for p in model_providers:
            if p.get("id") == provider_id or p.get("vendor") == provider_id:
                return p

        # Try to find by vendor name
        for p in model_providers:
            vendor = p.get("vendor", "").lower()
            if vendor in ["jina", "vllm"]:
                return p

        return None

    @classmethod
    async def _rerank_jina(
        cls,
        query: str,
        results: List[Dict[str, Any]],
        documents: List[str],
        top_n: int,
        provider: dict,
    ) -> List[Dict[str, Any]]:
        """Rerank using Jina AI reranking API."""
        api_key = provider.get("apiKey", "")
        model_name = provider.get("model", "jina-reranker")
        base_url = provider.get("baseURL", provider.get("baseUrl", "https://api.jina.ai"))

        url = f"{base_url.rstrip('/')}/rerank"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        data = {
            "model": model_name,
            "query": query,
            "top_n": top_n,
            "documents": documents,
            "return_documents": False,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=data)
            if response.status_code != 200:
                return results[:top_n]

            result = response.json()
            ranked_indices = [item["index"] for item in result.get("results", [])]

            reranked = []
            for idx in ranked_indices[:top_n]:
                if idx < len(results):
                    r = results[idx].copy()
                    r["score"] = 1.0 - (ranked_indices.index(idx) * 0.1)
                    reranked.append(r)

            return reranked

    @classmethod
    async def _rerank_vllm(
        cls,
        query: str,
        results: List[Dict[str, Any]],
        documents: List[str],
        top_n: int,
        provider: dict,
    ) -> List[Dict[str, Any]]:
        """Rerank using VLLM reranking API."""
        api_key = provider.get("apiKey", "dummy")
        model_name = provider.get("model", "reranker")
        base_url = provider.get("baseURL", provider.get("baseUrl", "http://127.0.0.1:8000"))

        url = f"{base_url.rstrip('/')}/rerank"

        headers = {"accept": "application/json", "Content-Type": "application/json"}

        data = {
            "model": model_name,
            "query": query,
            "top_n": top_n,
            "documents": documents,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=data)
            if response.status_code != 200:
                return results[:top_n]

            result = response.json()
            ranked_indices = [item["index"] for item in result.get("results", [])]

            reranked = []
            for idx in ranked_indices[:top_n]:
                if idx < len(results):
                    r = results[idx].copy()
                    r["score"] = 1.0 - (ranked_indices.index(idx) * 0.1)
                    reranked.append(r)

            return reranked
