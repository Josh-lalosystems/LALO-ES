# VectorStore Adapters and Runtime Reinit

**Date:** October 5, 2025

## Overview

We added a small abstraction layer for vector/tensor stores used by the RAG tool and memory managers. The goal is to make switching backends (Chroma, Qdrant, Milvus, Pinecone) low-friction.

Files added/changed

- `core/vectorstores/__init__.py` - VectorStore interface, `get_vector_store()` factory, and `reinit_vector_store()` helper to switch backends at runtime.
- `core/vectorstores/chroma_store.py` - Chroma adapter implementing the async interface.
- `core/tools/rag_tool.py` - refactored to use the vectorstore interface instead of direct Chroma calls.

## How to switch backends

By default, the system uses Chroma. To switch to another backend (once an adapter is added), set the environment variable `VECTOR_BACKEND` to the backend name (e.g., `qdrant`) before starting the service.

You can also call `core.vectorstores.reinit_vector_store(backend='qdrant', persist_directory='/data/qdrant')` from code to reinitialize the singleton at runtime (useful for tests and dynamic config reloads). Note: `reinit_vector_store` is synchronous and returns the new instance; call `await instance.initialize()` if you need it initialized immediately.

## Recommended next steps

- Add a Qdrant adapter (`core/vectorstores/qdrant_store.py`) and a docker-compose test fixture for CI to validate integration.
- Add metrics and timeouts for vector queries in `rag_tool.py`.
- Document backend tradeoffs in `docs/` (Chroma for local, Qdrant/Milvus for scale, Pinecone for managed SaaS).

***

## CI integration

We added a GitHub Actions workflow `.github/workflows/qdrant-integration.yml` which spins up a Qdrant service and runs `tests/test_qdrant_integration.py` with the environment variable `RUN_QDRANT_INTEGRATION=1` set. The test is skipped by default locally; CI runs it in a job that exposes Qdrant on `http://localhost:6333`.

For local testing you can run the Qdrant container via Docker Compose file `tests/docker-compose.qdrant.yml` and then run the test with:

```powershell
$env:RUN_QDRANT_INTEGRATION = '1'
python -m pytest tests/test_qdrant_integration.py -q
```

***

