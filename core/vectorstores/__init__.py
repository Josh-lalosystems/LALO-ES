"""Vector store abstraction and factory.

Defines a minimal VectorStore interface and a helper to obtain a
configured backend implementation. Default backend is 'chroma'.
"""
from typing import Dict, List, Optional, Any
import os


class VectorStore:
    """Abstract vector store interface. Implementations should subclass this."""

    async def initialize(self) -> None:
        raise NotImplementedError()

    async def add_documents(self, documents: List[str], ids: List[str], metadatas: List[Dict[str, Any]]) -> None:
        raise NotImplementedError()

    async def query(self, query_text: str, top_k: int = 5, filter_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        raise NotImplementedError()

    async def count(self) -> int:
        raise NotImplementedError()

    async def get_sample(self, limit: int = 100) -> Dict[str, Any]:
        raise NotImplementedError()

    async def delete(self, ids: List[str]) -> None:
        raise NotImplementedError()


def get_vector_store() -> VectorStore:
    """Factory: return an instance of the configured vector store backend.

    Uses env var VECTOR_BACKEND (default 'chroma'). Additional backends
    should be registered here.
    """
    # Use a module-level cached instance for fast repeated access
    global _STORE_INSTANCE
    try:
        _STORE_INSTANCE
    except NameError:
        _STORE_INSTANCE = None

    if _STORE_INSTANCE is not None:
        return _STORE_INSTANCE

    backend = os.getenv("VECTOR_BACKEND", "chroma").lower()

    if backend == "chroma":
        try:
            from core.vectorstores.chroma_store import ChromaStore

            _STORE_INSTANCE = ChromaStore()
            return _STORE_INSTANCE
        except Exception:
            raise
    elif backend == "qdrant":
        try:
            from core.vectorstores.qdrant_store import QdrantStore

            _STORE_INSTANCE = QdrantStore()
            return _STORE_INSTANCE
        except Exception:
            raise
    else:
        raise ValueError(f"Unknown VECTOR_BACKEND: {backend}")


def reinit_vector_store(backend: Optional[str] = None, **kwargs) -> VectorStore:
    """Re-initialize the vector store singleton.

    Args:
        backend: optional backend name (overrides VECTOR_BACKEND env var)
        kwargs: optional backend-specific constructor args (e.g., persist_directory)

    Returns the new VectorStore instance.
    """
    global _STORE_INSTANCE
    # Clear existing instance
    _STORE_INSTANCE = None

    if backend:
        os.environ["VECTOR_BACKEND"] = backend

    # Create new instance using factory
    instance = get_vector_store()

    # If backend-specific kwargs are provided and the instance has attributes, set them
    try:
        # Common options
        if hasattr(instance, "_persist_directory") and "persist_directory" in kwargs:
            instance._persist_directory = kwargs["persist_directory"]
        if hasattr(instance, "_collection_name") and "collection_name" in kwargs:
            instance._collection_name = kwargs["collection_name"]
    except Exception:
        # Non-fatal - clients should call initialize() explicitly if needed
        pass

    return instance
