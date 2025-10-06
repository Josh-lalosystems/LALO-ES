"""
Background indexer: non-blocking upsert to vector store with retries and dead-letter handling.

Usage:
  from services.document_service.services.background_indexer import enqueue_index_job
  enqueue_index_job(chunks, ids, metadatas)

The worker will run in the event loop and process jobs asynchronously.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Optional Redis support
REDIS_URL = os.getenv("REDIS_URL")
_redis = None

# In-memory fallback
_QUEUE: asyncio.Queue = None
_WORKER_TASK: asyncio.Task = None
_DEAD_LETTER: List[Dict[str, Any]] = []

MAX_RETRIES = int(os.getenv("INDEXER_MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("INDEXER_RETRY_DELAY", "2"))  # seconds


def _ensure_queue():
    global _QUEUE, _WORKER_TASK
    if REDIS_URL:
        # lazy import
        try:
            import aioredis
            global _redis
            if _redis is None:
                _redis = aioredis.from_url(REDIS_URL)
        except Exception:
            logger.exception("Failed to initialize redis client; falling back to in-memory queue")
            if _QUEUE is None:
                _QUEUE = asyncio.Queue()
    else:
        if _QUEUE is None:
            _QUEUE = asyncio.Queue()

    if _WORKER_TASK is None or _WORKER_TASK.done():
        loop = asyncio.get_event_loop()
        _WORKER_TASK = loop.create_task(_worker())


async def _worker():
    from core.vectorstores import get_vector_store
    logger.info("Background indexer worker started")
    store = None
    # optional storage service to persist dead letters
    storage_service = None
    db_session_factory = None
    DeadLetterModel = None
    try:
        from services.document_service.services.storage import StorageService
        storage_service = StorageService()
    except Exception:
        storage_service = None
    try:
        # Try to import DB session and model
        from core.database import SessionLocal, DeadLetter
        db_session_factory = SessionLocal
        DeadLetterModel = DeadLetter
    except Exception:
        db_session_factory = None
        DeadLetterModel = None

    while True:
        try:
            # Attempt Redis pop if configured
            if _redis is not None:
                raw = await _redis.lpop('indexer_queue')
                if raw is None:
                    await asyncio.sleep(0.5)
                    continue
                import json
                job = json.loads(raw)
            else:
                job = await _QUEUE.get()

            if store is None:
                try:
                    store = get_vector_store()
                    await store.initialize()
                except Exception as e:
                    logger.exception("Failed to initialize vector store in indexer: %s", e)
                    # Put job to dead-letter
                    job['error'] = str(e)
                    job['failed_at'] = datetime.utcnow().isoformat()
                    _DEAD_LETTER.append(job)
                    # persist if possible
                    if storage_service is not None:
                        import hashlib, json
                        job_id = hashlib.sha256(json.dumps(job).encode()).hexdigest()
                        await storage_service.store_dead_letter(job_id, job)
                    if _redis is None:
                        _QUEUE.task_done()
                    continue

            attempts = job.get('attempts', 0)
            try:
                await store.add_documents(documents=job['documents'], ids=job['ids'], metadatas=job['metadatas'])
                logger.info("Indexed %d chunks for doc", len(job['documents']))
            except Exception as e:
                attempts += 1
                job['attempts'] = attempts
                logger.warning("Indexing job failed attempt %d: %s", attempts, e)
                if attempts >= MAX_RETRIES:
                    job['error'] = str(e)
                    job['failed_at'] = datetime.utcnow().isoformat()
                    _DEAD_LETTER.append(job)
                    # persist dead-letter to DB if available
                    try:
                        import hashlib, json
                        job_id = hashlib.sha256(json.dumps(job, sort_keys=True).encode()).hexdigest()
                        if db_session_factory is not None and DeadLetterModel is not None:
                            db = db_session_factory()
                            try:
                                dl = DeadLetterModel(
                                    id=job_id,
                                    job_hash=job_id,
                                    documents=job.get('documents'),
                                    ids=job.get('ids'),
                                    metadatas=job.get('metadatas'),
                                    attempts=job.get('attempts', 0),
                                    error=job.get('error'),
                                    enqueued_at=job.get('enqueued_at'),
                                    failed_at=job.get('failed_at')
                                )
                                db.add(dl)
                                db.commit()
                            finally:
                                db.close()
                        elif storage_service is not None:
                            job_id = hashlib.sha256(json.dumps(job).encode()).hexdigest()
                            await storage_service.store_dead_letter(job_id, job)
                    except Exception:
                        logger.exception("Failed to persist dead letter to DB or storage")
                else:
                    # Exponential backoff and re-enqueue
                    await asyncio.sleep(RETRY_DELAY * attempts)
                    if _redis is not None:
                        await _redis.rpush('indexer_queue', __import__('json').dumps(job))
                    else:
                        await _QUEUE.put(job)

            if _redis is None:
                _QUEUE.task_done()
        except asyncio.CancelledError:
            logger.info("Background indexer worker cancelled")
            break
        except Exception as e:
            logger.exception("Unexpected indexer error: %s", e)
            await asyncio.sleep(1)


def enqueue_index_job(documents: List[str], ids: List[str], metadatas: List[Dict[str, Any]]) -> None:
    """Enqueue an indexing job. Non-blocking. Starts worker lazily."""
    _ensure_queue()
    job = {
        'documents': documents,
        'ids': ids,
        'metadatas': metadatas,
        'attempts': 0,
        'enqueued_at': datetime.utcnow().isoformat()
    }
    try:
        if _redis is not None:
            import json
            # push as JSON to redis list
            asyncio.get_event_loop().create_task(_redis.rpush('indexer_queue', json.dumps(job)))
        else:
            _QUEUE.put_nowait(job)
    except Exception:
        # In rare cases, fallback to synchronous (best-effort)
        import asyncio
        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(lambda: _QUEUE.put_nowait(job))


def list_dead_letter() -> List[Dict[str, Any]]:
    return list(_DEAD_LETTER)
