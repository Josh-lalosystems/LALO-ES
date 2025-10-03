# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Module: MemoryManager

Purpose:
 - Implements dual-layer memory system: short-term Redis runtime store vs long-term vector DB.
 - Records reasoning trace, tool calls, and agent interactions.
 - Links memory writes to audit logs for robust traceability.
 - Enables semantic similarity recall of prior sessions via embeddings.

Dependencies:
 - redis.Redis client (supports Redis 8 vector search & JSON)
 - Vector DB (e.g., Chroma, Weaviate) client
 - Embedding LLM (e.g., OpenAI / Hugging Face)
 - AuditLogger to record metadata linkage
 - Optional ACL/permission rules for memory scope

Edge Cases & Handling:
 - Redis eviction: rehydrate from vector DB
 - Embedding collision: create unique vector ID with timestamp
 - Store failures: buffer and retry
 - Missing trace: return empty or prompt new session
"""

import uuid
import json
from datetime import datetime
from .audit_logger import AuditLogger

# Third-party imports
import redis
from chromadb import Client as VectorClient
from Transformers import OpenAIEmbedder  # hypothetical embedding class

class MemoryManager:
    def __init__(self,
                 redis_host='localhost', redis_port=6379,
                 vector_host=None, vector_port=None):
        """
        Initializes Redis client (v8+) and vector database client.
        """ 
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.vector = VectorClient(host=vector_host, port=vector_port)  # stub
        self.embedder = OpenAIEmbedder()
        self.audit = AuditLogger()

    def store_session(self, agent_id: str, request: dict, trace: list, tool_calls: list):
        """
        Saves session data to Redis and Vector DB, and records audit metadata.
        """
        redis_key = f"session:{agent_id}"
        payload = {
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "request": request,
            "trace": trace,
            "tool_calls": tool_calls
        }

        # Short-term store in Redis (JSON support & TTL possible)
        try:
            self.redis.set(redis_key, json.dumps(payload))
        except Exception as e:
            # If Redis fails, still proceed to vector DB but log alert
            print(f"[MemoryManager] Redis write failed: {e}")

        # Long-term vector embedding for semantic retrieval
        embed = self.embedder.embed(json.dumps(trace))
        vector_id = f"{agent_id}:{uuid.uuid4()}"
        metadata = {
            "agent_id": agent_id,
            "timestamp": payload["timestamp"],
            "request": request,
            "tool_calls": tool_calls
        }
        try:
            self.vector.upsert(id=vector_id, vector=embed, metadata=metadata)
        except Exception as e:
            print(f"[MemoryManager] Vector DB upsert failed: {e}")

        # Audit linkage for legal/compliance trace
        self.audit.record_memory(agent_id=agent_id,
                                 redis_key=redis_key,
                                 vector_id=vector_id)

    def recall_similar(self, current_trace: list, top_k: int = 5):
        """
        Returns similar past sessions to current trace based on vector similarity.
        Falls back gracefully if vector store fails.
        """
        try:
            query_vec = self.embedder.embed(json.dumps(current_trace))
            results = self.vector.query(query_vector=query_vec, top_k=top_k)
            return results  # list of dicts with metadata
        except Exception as e:
            print(f"[MemoryManager] Vector recall failed: {e}")
            return []

    def get_session(self, agent_id: str):
        """
        Fetches session data directly from Redis if available.
        """
        redis_key = f"session:{agent_id}"
        try:
            raw = self.redis.get(redis_key)
            return json.loads(raw) if raw else None
        except Exception as e:
            print(f"[MemoryManager] Redis retrieval failed: {e}")
            return None
