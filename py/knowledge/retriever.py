"""Retrieval logic for knowledge base queries."""

import asyncio
from typing import List, Dict, Any, Optional

from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_classic.retrievers import EnsembleRetriever

from py.know_base import (
    query_vector_store,
    rerank_knowledge_base,
    MyOpenAICompatibleEmbeddings,
)
from py.get_setting import KB_DIR, load_settings


class KnowledgeRetriever:
    """Handles knowledge base retrieval operations."""

    def __init__(self, kb_id: str, config: Dict[str, Any]):
        self.kb_id = kb_id
        self.config = config

    async def search(
        self,
        query: str,
        top_k: int = 5,
        rerank: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base.

        Args:
            query: Search query string
            top_k: Number of results to return
            rerank: Whether to apply reranking

        Returns:
            List of search results with content, metadata, and scores
        """
        # Temporarily update config with top_k
        original_k = self.config.get("chunk_k", top_k)
        self.config["chunk_k"] = top_k

        try:
            # Perform hybrid search (BM25 + FAISS)
            results = await query_vector_store(
                query,
                self.kb_id,
                self.config,
                self.config.get("vendor", "openai"),
            )

            # Apply reranking if requested
            if rerank and results:
                results = await rerank_knowledge_base(query, results)
                # Limit to top_k after reranking
                results = results[:top_k]

            # Format results
            formatted_results = []
            for i, doc in enumerate(results):
                formatted_results.append(
                    {
                        "content": doc.get("content", ""),
                        "metadata": doc.get("metadata", {}),
                        "score": 1.0 - (i * 0.1),  # Placeholder score
                    }
                )

            return formatted_results

        finally:
            self.config["chunk_k"] = original_k

    async def get_relevant_chunks(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get relevant chunks for a query without reranking."""
        return await self.search(query, top_k=top_k, rerank=False)
