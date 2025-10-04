# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
RAG (Retrieval-Augmented Generation) Tool

Provides document indexing and semantic search capabilities:
- Index documents from various sources
- Semantic search using embeddings
- ChromaDB vector database
- Automatic chunking and embedding
"""

import os
import hashlib
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

from .base import BaseTool, ToolDefinition, ToolParameter, ToolExecutionResult


class RAGTool(BaseTool):
    """RAG tool for document indexing and semantic search"""

    def __init__(self):
        self._chroma_client = None
        self._collection = None
        self._embedding_function = None
        self._initialized = False

        # Configuration
        self._persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
        self._collection_name = os.getenv("CHROMA_COLLECTION", "lalo_documents")
        self._chunk_size = int(os.getenv("RAG_CHUNK_SIZE", "512"))
        self._chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))

    async def _initialize(self):
        """Lazy initialization of ChromaDB"""
        if self._initialized:
            return

        try:
            import chromadb
            from chromadb.utils import embedding_functions
        except ImportError:
            raise ValueError(
                "chromadb package not installed. "
                "Run: pip install chromadb"
            )

        # Initialize ChromaDB client
        self._chroma_client = chromadb.PersistentClient(path=self._persist_directory)

        # Use sentence transformers for embeddings (free, local)
        try:
            self._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"  # Fast, efficient model
            )
        except Exception as e:
            # Fallback to default embedding function
            print(f"Warning: Could not load sentence-transformers model: {e}")
            self._embedding_function = embedding_functions.DefaultEmbeddingFunction()

        # Get or create collection
        try:
            self._collection = self._chroma_client.get_collection(
                name=self._collection_name,
                embedding_function=self._embedding_function
            )
        except Exception:
            # Collection doesn't exist, create it
            self._collection = self._chroma_client.create_collection(
                name=self._collection_name,
                embedding_function=self._embedding_function,
                metadata={"description": "LALO AI document collection"}
            )

        self._initialized = True

    @property
    def tool_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="rag_query",
            description="Search indexed documents using semantic search. Can index new documents and query existing ones.",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="Action to perform: 'query' to search documents, 'index' to add new documents, 'list' to list indexed documents",
                    required=True,
                    enum=["query", "index", "list", "delete"]
                ),
                ToolParameter(
                    name="query",
                    type="string",
                    description="Search query (required for 'query' action)",
                    required=False
                ),
                ToolParameter(
                    name="documents",
                    type="array",
                    description="List of documents to index (required for 'index' action). Each document should have 'content', 'title', and optional 'metadata'",
                    required=False
                ),
                ToolParameter(
                    name="top_k",
                    type="integer",
                    description="Number of results to return (default: 5)",
                    required=False
                ),
                ToolParameter(
                    name="filter_metadata",
                    type="object",
                    description="Metadata filters to apply to search (optional)",
                    required=False
                ),
                ToolParameter(
                    name="document_ids",
                    type="array",
                    description="List of document IDs to delete (required for 'delete' action)",
                    required=False
                )
            ],
            returns={
                "type": "object",
                "description": "RAG operation results - query results with documents or indexing confirmation"
            }
        )

    async def execute(self, **kwargs) -> ToolExecutionResult:
        """Execute RAG operation (query, index, list, or delete)"""
        action = kwargs.get("action")

        try:
            # Initialize ChromaDB if needed
            await self._initialize()

            if action == "query":
                return await self._query_documents(kwargs)
            elif action == "index":
                return await self._index_documents(kwargs)
            elif action == "list":
                return await self._list_documents(kwargs)
            elif action == "delete":
                return await self._delete_documents(kwargs)
            else:
                return ToolExecutionResult(
                    success=False,
                    error=f"Unknown action: {action}. Use 'query', 'index', 'list', or 'delete'"
                )

        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f"RAG operation failed: {str(e)}"
            )

    async def _query_documents(self, kwargs: Dict) -> ToolExecutionResult:
        """Query indexed documents"""
        query = kwargs.get("query")
        if not query:
            return ToolExecutionResult(
                success=False,
                error="Query text is required for 'query' action"
            )

        top_k = kwargs.get("top_k", 5)
        filter_metadata = kwargs.get("filter_metadata")

        # Perform semantic search
        results = self._collection.query(
            query_texts=[query],
            n_results=top_k,
            where=filter_metadata if filter_metadata else None
        )

        # Format results
        documents = []
        if results["ids"] and len(results["ids"]) > 0:
            for i in range(len(results["ids"][0])):
                documents.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                    "relevance_score": 1.0 - (results["distances"][0][i] if results.get("distances") else 0.5)
                })

        return ToolExecutionResult(
            success=True,
            output={
                "query": query,
                "documents": documents,
                "count": len(documents),
                "timestamp": datetime.utcnow().isoformat()
            },
            metadata={
                "top_k": top_k,
                "collection": self._collection_name
            }
        )

    async def _index_documents(self, kwargs: Dict) -> ToolExecutionResult:
        """Index new documents"""
        documents = kwargs.get("documents")
        if not documents or not isinstance(documents, list):
            return ToolExecutionResult(
                success=False,
                error="Documents list is required for 'index' action"
            )

        # Process and chunk documents
        chunks = []
        chunk_ids = []
        chunk_metadatas = []

        for doc_idx, doc in enumerate(documents):
            if not isinstance(doc, dict) or "content" not in doc:
                continue

            content = doc["content"]
            title = doc.get("title", f"Document {doc_idx}")
            metadata = doc.get("metadata", {})
            metadata["title"] = title
            metadata["indexed_at"] = datetime.utcnow().isoformat()

            # Chunk document
            doc_chunks = self._chunk_text(content)

            for chunk_idx, chunk in enumerate(doc_chunks):
                chunk_id = hashlib.md5(
                    f"{title}_{chunk_idx}_{chunk[:50]}".encode()
                ).hexdigest()

                chunks.append(chunk)
                chunk_ids.append(chunk_id)
                chunk_metadatas.append({
                    **metadata,
                    "chunk_index": chunk_idx,
                    "total_chunks": len(doc_chunks)
                })

        if not chunks:
            return ToolExecutionResult(
                success=False,
                error="No valid documents to index"
            )

        # Add to ChromaDB
        self._collection.add(
            documents=chunks,
            ids=chunk_ids,
            metadatas=chunk_metadatas
        )

        return ToolExecutionResult(
            success=True,
            output={
                "action": "index",
                "documents_indexed": len(documents),
                "chunks_created": len(chunks),
                "collection": self._collection_name,
                "timestamp": datetime.utcnow().isoformat()
            },
            metadata={
                "chunk_size": self._chunk_size,
                "chunk_overlap": self._chunk_overlap
            }
        )

    async def _list_documents(self, kwargs: Dict) -> ToolExecutionResult:
        """List all indexed documents"""
        # Get collection stats
        count = self._collection.count()

        # Get sample of documents (ChromaDB limitation - can't easily get all unique titles)
        sample_results = self._collection.get(
            limit=min(100, count),
            include=["metadatas"]
        )

        # Extract unique titles
        titles = set()
        for metadata in sample_results.get("metadatas", []):
            if metadata and "title" in metadata:
                titles.add(metadata["title"])

        return ToolExecutionResult(
            success=True,
            output={
                "action": "list",
                "total_chunks": count,
                "sample_titles": list(titles),
                "collection": self._collection_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    async def _delete_documents(self, kwargs: Dict) -> ToolExecutionResult:
        """Delete documents by IDs"""
        document_ids = kwargs.get("document_ids")
        if not document_ids or not isinstance(document_ids, list):
            return ToolExecutionResult(
                success=False,
                error="Document IDs list is required for 'delete' action"
            )

        # Delete from ChromaDB
        self._collection.delete(ids=document_ids)

        return ToolExecutionResult(
            success=True,
            output={
                "action": "delete",
                "deleted_count": len(document_ids),
                "collection": self._collection_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            # Get chunk
            end = min(start + self._chunk_size, text_length)
            chunk = text[start:end]

            # Try to break on sentence boundary
            if end < text_length:
                # Look for sentence endings
                last_period = chunk.rfind(". ")
                last_newline = chunk.rfind("\n")
                break_point = max(last_period, last_newline)

                if break_point > self._chunk_size // 2:  # Only break if we're past halfway
                    end = start + break_point + 1
                    chunk = text[start:end]

            chunks.append(chunk.strip())

            # Move start position with overlap
            start = end - self._chunk_overlap
            if start >= text_length:
                break

        return chunks

    def is_enabled(self) -> bool:
        """Tool is always enabled (ChromaDB is local)"""
        return True


# Create singleton instance
rag_tool = RAGTool()
