"""FastAPI routes for knowledge base management."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel

from py.knowledge.indexer import DocumentIndexer
from py.knowledge.retriever import KnowledgeRetriever
from py.get_setting import load_settings, KB_DIR
from py.load_files import get_file_content, ALLOWED_EXTENSIONS
import os


router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


# ============== Request/Response Models ==============

class Document(BaseModel):
    """Document model."""

    id: str
    title: str
    content: Optional[str] = None
    metadata: dict = {}
    chunk_count: int
    created_at: float


class SearchResult(BaseModel):
    """Search result model."""

    document_id: str
    chunk_id: Optional[str] = None
    content: str
    score: float
    metadata: dict = {}


class KnowledgeConfig(BaseModel):
    """Knowledge base configuration model."""

    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 5
    weight: float = 0.5


class KnowledgeConfigResponse(BaseModel):
    """Knowledge base configuration response."""

    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    weight: float


# ============== Helper Functions ==============

async def get_default_kb_config() -> dict:
    """Get default knowledge base configuration from settings."""
    settings = await load_settings()
    kb_settings = settings.get("KBSettings", {})

    return {
        "model": kb_settings.get("model", "text-embedding-3-small"),
        "api_key": kb_settings.get("api_key", ""),
        "base_url": kb_settings.get("base_url", "http://127.0.0.1:8000"),
        "chunk_size": kb_settings.get("chunk_size", 512),
        "chunk_overlap": kb_settings.get("chunk_overlap", 50),
        "chunk_k": kb_settings.get("top_k", 5),
        "weight": kb_settings.get("weight", 0.5),
        "vendor": kb_settings.get("vendor", "openai"),
    }


async def get_or_create_kb_id() -> str:
    """Get or create default knowledge base ID."""
    settings = await load_settings()
    kb_settings = settings.get("KBSettings", {})

    # Use existing KB id or create default
    kb_id = kb_settings.get("id")
    if not kb_id:
        kb_id = "default"
        kb_settings["id"] = kb_id

    return kb_id


# ============== API Endpoints ==============

@router.post("/documents", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
):
    """
    Upload and index a document.

    Args:
        file: The file to upload and index
        title: Optional title override

    Returns:
        Document metadata
    """
    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lstrip(".").lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file content
    content = await file.read()

    # Get knowledge base config
    config = await get_default_kb_config()
    kb_id = await get_or_create_kb_id()

    # Create indexer
    indexer = DocumentIndexer(kb_id, config)

    # Extract text content
    try:
        from io import BytesIO
        from py.load_files import decode_text

        # Handle text vs binary files
        if ext in ["txt", "md", "json", "csv", "tsv", "log", "conf", "ini", "env", "toml", "py", "js", "ts", "html", "css", "scss", "less", "vue", "svelte", "jsx", "tsx", "xml", "yml", "yaml", "sql", "sh", "java", "c", "cpp", "h", "hpp", "go", "rs", "swift", "kt", "dart", "rb", "php"]:
            file_content = content.decode("utf-8", errors="replace")
        else:
            # For binary files, use the decode_text utility
            file_content = decode_text(content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

    # Index the document
    try:
        metadata = await indexer.index_document(
            file_content=file_content,
            file_name=file.filename,
            file_path=f"uploaded://{file.filename}",
            title=title,
        )

        return Document(
            id=metadata["id"],
            title=metadata["title"],
            content=file_content[:1000] if file_content else None,  # Preview only
            metadata={
                "file_name": metadata["file_name"],
                "file_path": metadata["file_path"],
            },
            chunk_count=metadata["chunk_count"],
            created_at=metadata["created_at"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index document: {str(e)}")


@router.get("/documents", response_model=List[Document])
async def list_documents():
    """
    List all indexed documents.

    Returns:
        List of document metadata
    """
    config = await get_default_kb_config()
    kb_id = await get_or_create_kb_id()

    indexer = DocumentIndexer(kb_id, config)
    documents = await indexer.list_documents()

    return [
        Document(
            id=doc["id"],
            title=doc["title"],
            metadata={
                "file_name": doc.get("file_name", ""),
                "file_path": doc.get("file_path", ""),
            },
            chunk_count=doc["chunk_count"],
            created_at=doc["created_at"],
        )
        for doc in documents
    ]


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """
    Delete a document from the index.

    Args:
        doc_id: The document ID to delete

    Returns:
        Success message
    """
    config = await get_default_kb_config()
    kb_id = await get_or_create_kb_id()

    indexer = DocumentIndexer(kb_id, config)
    success = await indexer.delete_document(doc_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")

    return {"success": True, "message": f"Document {doc_id} deleted"}


@router.post("/search", response_model=List[SearchResult])
async def search_knowledge(
    query: str,
    top_k: int = Query(default=5, ge=1, le=20),
    rerank: bool = Query(default=True),
):
    """
    Search the knowledge base.

    Args:
        query: Search query string
        top_k: Number of results to return
        rerank: Whether to apply reranking

    Returns:
        List of search results
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    config = await get_default_kb_config()
    kb_id = await get_or_create_kb_id()

    retriever = KnowledgeRetriever(kb_id, config)

    try:
        results = await retriever.search(
            query=query.strip(),
            top_k=top_k,
            rerank=rerank,
        )

        return [
            SearchResult(
                document_id=r["metadata"].get("doc_id", ""),
                chunk_id=r["metadata"].get("doc_id"),
                content=r["content"],
                score=r["score"],
                metadata=r["metadata"],
            )
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/config", response_model=KnowledgeConfigResponse)
async def get_config():
    """
    Get current knowledge base configuration.

    Returns:
        Current configuration
    """
    config = await get_default_kb_config()

    return KnowledgeConfigResponse(
        embedding_model=config.get("model", "text-embedding-3-small"),
        chunk_size=config.get("chunk_size", 512),
        chunk_overlap=config.get("chunk_overlap", 50),
        top_k=config.get("chunk_k", 5),
        weight=config.get("weight", 0.5),
    )


@router.post("/config")
async def update_config(config_update: KnowledgeConfig):
    """
    Update knowledge base configuration.

    Args:
        config_update: New configuration values

    Returns:
        Success message
    """
    settings = await load_settings()

    # Update KBSettings
    if "KBSettings" not in settings:
        settings["KBSettings"] = {}

    kb_settings = settings["KBSettings"]
    kb_settings["model"] = config_update.embedding_model
    kb_settings["chunk_size"] = config_update.chunk_size
    kb_settings["chunk_overlap"] = config_update.chunk_overlap
    kb_settings["top_k"] = config_update.top_k
    kb_settings["weight"] = config_update.weight

    # Save settings
    from py.get_setting import save_settings
    await save_settings(settings)

    return {"success": True, "message": "Configuration updated"}
