"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""ChromaDB adapter for the VectorStore interface."""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)


class ChromaStore:
    def __init__(self, persist_directory: Optional[str] = None, collection_name: Optional[str] = None):
        self._persist_directory = persist_directory or os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
        self._collection_name = collection_name or os.getenv("CHROMA_COLLECTION", "lalo_documents")
        self._client = None
        self._collection = None
        self._embedding_function = None
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return

        try:
            import chromadb
            from chromadb.utils import embedding_functions
        except ImportError as e:
            logger.exception("chromadb not installed: %s", e)
            raise

        # Create or connect to persistent client
        self._client = chromadb.PersistentClient(path=self._persist_directory)

        # Attempt sentence-transformers embedding function
        try:
            self._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        except Exception:
            logger.warning("SentenceTransformer embedding not available, using default")
            self._embedding_function = embedding_functions.DefaultEmbeddingFunction()

        try:
            self._collection = self._client.get_collection(
                name=self._collection_name,
                embedding_function=self._embedding_function
            )
        except Exception:
            self._collection = self._client.create_collection(
                name=self._collection_name,
                embedding_function=self._embedding_function,
                metadata={"description": "LALO AI document collection"}
            )

        self._initialized = True

    async def add_documents(self, documents: List[str], ids: List[str], metadatas: List[Dict[str, Any]]) -> None:
        if not self._initialized:
            await self.initialize()

        # chroma expects documents, ids, metadatas
        self._collection.add(documents=documents, ids=ids, metadatas=metadatas)

    async def query(self, query_text: str, top_k: int = 5, filter_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        results = self._collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=filter_metadata if filter_metadata else None
        )

        return results

    async def count(self) -> int:
        if not self._initialized:
            await self.initialize()
        return self._collection.count()

    async def get_sample(self, limit: int = 100) -> Dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        sample_results = self._collection.get(limit=limit, include=["metadatas"])
        return sample_results

    async def delete(self, ids: List[str]) -> None:
        if not self._initialized:
            await self.initialize()
        self._collection.delete(ids=ids)
