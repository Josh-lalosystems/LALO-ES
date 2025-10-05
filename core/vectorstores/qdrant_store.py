"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""Qdrant adapter for the VectorStore interface."""
from typing import Dict, List, Any, Optional
import logging
import os
import asyncio

logger = logging.getLogger(__name__)


class QdrantStore:
    def __init__(self, url: Optional[str] = None, collection_name: Optional[str] = None):
        self._url = url or os.getenv("QDRANT_URL", "http://localhost:6333")
        self._collection_name = collection_name or os.getenv("QDRANT_COLLECTION", "lalo_documents")
        self._client = None
        self._model = None
        self._vector_size = None
        self._initialized = False

    async def _ensure_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as e:
            logger.exception("sentence-transformers not installed: %s", e)
            raise

        # Load small efficient model
        self._model = SentenceTransformer("all-MiniLM-L6-v2")
        # Determine vector size
        self._vector_size = self._model.get_sentence_embedding_dimension()

    async def initialize(self) -> None:
        if self._initialized:
            return

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models as qmodels
        except Exception as e:
            logger.exception("qdrant-client not installed: %s", e)
            raise

        # ensure model for embeddings
        await self._ensure_model()

        # Create client (sync client; use to_thread for blocking calls)
        self._client = QdrantClient(url=self._url)

        # Create collection if not exists
        def _create_collection():
            try:
                existing = self._client.get_collection(self._collection_name)
                return
            except Exception:
                from qdrant_client.http.models import VectorParams
                self._client.recreate_collection(
                    collection_name=self._collection_name,
                    vectors=VectorParams(size=self._vector_size, distance="Cosine")
                )

        await asyncio.to_thread(_create_collection)

        self._initialized = True

    async def add_documents(self, documents: List[str], ids: List[str], metadatas: List[Dict[str, Any]]) -> None:
        if not self._initialized:
            await self.initialize()

        # Compute embeddings
        await self._ensure_model()
        vectors = await asyncio.to_thread(self._model.encode, documents, convert_to_numpy=True)

        # Prepare payloads: store original text with metadata
        payloads = []
        for d_meta, doc in zip(metadatas, documents):
            payload = {**(d_meta or {}), "text": doc}
            payloads.append(payload)

        # Upsert points
        def _upsert():
            from qdrant_client.http import models as qmodels
            points = []
            for pid, vector, payload in zip(ids, vectors, payloads):
                points.append(qmodels.PointStruct(id=pid, vector=vector.tolist(), payload=payload))
            self._client.upsert(collection_name=self._collection_name, points=points)

        await asyncio.to_thread(_upsert)

    async def query(self, query_text: str, top_k: int = 5, filter_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        await self._ensure_model()
        q_vector = await asyncio.to_thread(self._model.encode, [query_text], convert_to_numpy=True)
        qv = q_vector[0].tolist()

        # Convert filter_metadata into Qdrant Filter if provided (simple exact match only)
        q_filter = None
        if filter_metadata:
            try:
                from qdrant_client.http import models as qmodels
                must_conditions = []
                for k, v in (filter_metadata or {}).items():
                    must_conditions.append(qmodels.FieldCondition(key=k, match=qmodels.MatchValue(value=v)))
                q_filter = qmodels.Filter(must=must_conditions)
            except Exception:
                q_filter = None

        def _search():
            return self._client.search(collection_name=self._collection_name, query_vector=qv, limit=top_k, filter=q_filter, with_payload=True, with_vectors=False)

        results = await asyncio.to_thread(_search)

        # Format into chroma-like structure
        ids = [[r.id for r in results]]
        documents = [[r.payload.get("text") for r in results]]
        metadatas = [[{k: v for k, v in (r.payload.items() if r.payload else {})} for r in results]]
        distances = [[r.score for r in results]]

        return {"ids": ids, "documents": documents, "metadatas": metadatas, "distances": distances}

    async def count(self) -> int:
        if not self._initialized:
            await self.initialize()

        def _count():
            return self._client.count(self._collection_name).points_count

        return await asyncio.to_thread(_count)

    async def get_sample(self, limit: int = 100) -> Dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        def _scroll():
            return self._client.scroll(self._collection_name, limit=limit, with_payload=True)

        res = await asyncio.to_thread(_scroll)
        metadatas = [p.payload for p in res] if res else []
        return {"metadatas": metadatas}

    async def delete(self, ids: List[str]) -> None:
        if not self._initialized:
            await self.initialize()

        def _delete():
            self._client.delete(collection_name=self._collection_name, points_selector={'ids': ids})

        await asyncio.to_thread(_delete)
