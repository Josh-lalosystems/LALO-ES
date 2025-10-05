import asyncio

from core.tools.rag_tool import RAGTool


class FakeStore:
    def __init__(self):
        self.docs = []
        self.ids = []
        self.metadatas = []

    async def initialize(self):
        return

    async def add_documents(self, documents, ids, metadatas):
        self.docs.extend(documents)
        self.ids.extend(ids)
        self.metadatas.extend(metadatas)

    async def query(self, query_text, top_k=5, filter_metadata=None):
        # simple substring match ranking
        matches = []
        distances = []
        for i, d in enumerate(self.docs):
            if query_text.lower() in d.lower():
                matches.append(i)
                distances.append(0.0)

        # format like chroma query results
        if not matches:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        ids = [[self.ids[i] for i in matches[:top_k]]]
        documents = [[self.docs[i] for i in matches[:top_k]]]
        metadatas = [[self.metadatas[i] for i in matches[:top_k]]]
        distances = [[distances[i] for i in range(len(matches[:top_k]))]]

        return {"ids": ids, "documents": documents, "metadatas": metadatas, "distances": distances}

    async def count(self):
        return len(self.docs)

    async def get_sample(self, limit=100):
        return {"metadatas": self.metadatas[:limit]}

    async def delete(self, ids):
        # naive deletion
        for idd in ids:
            if idd in self.ids:
                idx = self.ids.index(idd)
                self.ids.pop(idx)
                self.docs.pop(idx)
                self.metadatas.pop(idx)


def _run_index_query():
    tool = RAGTool()
    # inject fake store
    tool._store = FakeStore()
    tool._initialized = True

    docs = [{"content": "Hello world from LALO", "title": "greeting"}, {"content": "Another doc about AI", "title": "ai"}]

    res = asyncio.run(tool._index_documents({"documents": docs}))
    assert res.success

    q = asyncio.run(tool._query_documents({"query": "lalo"}))
    assert q.success
    assert q.output["count"] == 1

    # delete
    ids = [d.get("id") for d in tool._store.metadatas]
    asyncio.run(tool._delete_documents({"document_ids": ids}))
    c = asyncio.run(tool._list_documents({}))
    assert c.success


def test_rag_tool_index_and_query():
    _run_index_query()
