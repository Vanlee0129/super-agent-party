"""Document indexing logic for knowledge base."""

import asyncio
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever

from py.know_base import (
    chunk_documents,
    build_vector_store,
    MyOpenAICompatibleEmbeddings,
    clean_text,
)
from py.get_setting import KB_DIR


class DocumentIndexer:
    """Handles document indexing operations."""

    def __init__(self, kb_id: str, config: Dict[str, Any]):
        self.kb_id = kb_id
        self.config = config
        self.kb_dir = Path(KB_DIR) / str(kb_id)
        self.kb_dir.mkdir(parents=True, exist_ok=True)

    async def index_document(
        self,
        file_content: str,
        file_name: str,
        file_path: str,
        title: str = None,
    ) -> Dict[str, Any]:
        """
        Index a document into the knowledge base.

        Args:
            file_content: The text content of the document
            file_name: Original filename
            file_path: Path or URL to the file
            title: Optional title override

        Returns:
            Document metadata including id and chunk count
        """
        doc_id = str(uuid.uuid4())

        # Create document result format matching get_files_json output
        doc_result = {
            "file_path": file_path,
            "file_name": title or file_name,
            "content": file_content,
        }

        # Chunk the document
        chunks = chunk_documents([doc_result], self.config)

        # Build the vector store (BM25 + FAISS)
        await build_vector_store(
            chunks,
            self.kb_id,
            self.config,
            self._get_vendor(),
        )

        # Save document metadata
        import time
        metadata = {
            "id": doc_id,
            "title": title or file_name,
            "file_name": file_name,
            "file_path": file_path,
            "chunk_count": len(chunks),
            "created_at": time.time(),
        }

        await self._save_document_metadata(doc_id, metadata)

        return metadata

    async def _save_document_metadata(self, doc_id: str, metadata: Dict[str, Any]):
        """Save document metadata to disk."""
        metadata_file = self.kb_dir / "documents.json"

        docs = {}
        if metadata_file.exists():
            try:
                docs = json.loads(metadata_file.read_text(encoding="utf-8"))
            except Exception:
                docs = {}

        docs[doc_id] = metadata
        metadata_file.write_text(
            json.dumps(docs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    async def get_document(self, doc_id: str) -> Dict[str, Any]:
        """Retrieve document metadata."""
        metadata_file = self.kb_dir / "documents.json"
        if not metadata_file.exists():
            return None

        docs = json.loads(metadata_file.read_text(encoding="utf-8"))
        return docs.get(doc_id)

    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all indexed documents."""
        metadata_file = self.kb_dir / "documents.json"
        if not metadata_file.exists():
            return []

        docs = json.loads(metadata_file.read_text(encoding="utf-8"))
        return list(docs.values())

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the index."""
        metadata_file = self.kb_dir / "documents.json"
        if not metadata_file.exists():
            return False

        docs = json.loads(metadata_file.read_text(encoding="utf-8"))
        if doc_id not in docs:
            return False

        del docs[doc_id]
        metadata_file.write_text(
            json.dumps(docs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # Note: Actual chunk removal from FAISS/BM25 would require re-indexing
        # For now, we just remove the metadata
        return True

    def _get_vendor(self) -> str:
        """Get the vendor from config."""
        return self.config.get("vendor", "openai")
