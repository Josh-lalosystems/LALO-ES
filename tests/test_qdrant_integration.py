"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import os
import asyncio
import pytest

from core.vectorstores import reinit_vector_store, get_vector_store


RUN_INTEGRATION = os.getenv("RUN_QDRANT_INTEGRATION", "0") == "1"


@pytest.mark.skipif(not RUN_INTEGRATION, reason="Qdrant integration tests disabled. Set RUN_QDRANT_INTEGRATION=1 to enable.")
def test_qdrant_store_basic_flow():
    # Reinit factory to qdrant backend
    instance = reinit_vector_store(backend="qdrant")

    async def _run():
        await instance.initialize()

        docs = ["Hello Qdrant LALO"]
        ids = ["test-doc-1"]
        metadatas = [{"title": "test"}]

        await instance.add_documents(docs, ids, metadatas)

        res = await instance.query("Qdrant")
        assert isinstance(res, dict)
        assert res.get("ids")

        cnt = await instance.count()
        assert cnt >= 1

        await instance.delete(ids)

    asyncio.run(_run())
