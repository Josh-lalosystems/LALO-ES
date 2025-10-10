"""
Quick integration test to force fallback attempts by monkeypatching the local services.
This script will:
- Temporarily replace local_llm_service.generate and confidence_model.score to simulate low confidence
- Call unified_request_handler.handle_request
- Print the response metadata including fallback_attempts

Run inside the repo venv:
python scripts/force_fallback_test.py
"""
import asyncio
import importlib
import os

# Ensure latest code is loaded
importlib.invalidate_caches()

from core.services.unified_request_handler import unified_request_handler
from core.services.local_llm_service import local_llm_service
from core.services.confidence_model import confidence_model
from core.services import database_service
import core.database as cdb

# Save originals
orig_generate = local_llm_service.generate
orig_score = confidence_model.score

async def fake_generate(self, prompt, model_name="tinyllama", **kwargs):
    # Return a plausible but poor-quality output that will get low confidence
    return "This is a low quality generic response. I don't know."

async def fake_score(self, output, original_request, sources=None, context=None, model_used=None):
    # Simulate low confidence for tinyllama, high for qwen
    if model_used and 'tinyllama' in model_used:
        return {"confidence": 0.2, "scores": {}, "recommendation": "human_review"}
    if model_used and 'qwen' in model_used:
        return {"confidence": 0.85, "scores": {}, "recommendation": "accept"}
    return {"confidence": 0.5, "scores": {}, "recommendation": "retry"}

async def run_test():
    try:
        # Monkeypatch
        # Bind functions as methods on instances
        local_llm_service.generate = fake_generate.__get__(local_llm_service, local_llm_service.__class__)
        confidence_model.score = fake_score.__get__(confidence_model, confidence_model.__class__)

        # Use a simple math prompt so router selects the simple path (tinyllama primary)
        res = await unified_request_handler.handle_request(
            user_request='What is 2 + 2?',
            user_id='integration-test',
            available_models=['tinyllama','qwen-0.5b'],
            context=None,
            stream=False
        )

        print('Response model:', res.get('model'))
        print('Top-level metadata.fallback_attempts:', res.get('metadata', {}).get('fallback_attempts'))
        print('Full metadata:', res.get('metadata'))
        # Verify audit log persisted
        session = cdb.SessionLocal()
        try:
            last = session.query(cdb.AuditLog).order_by(cdb.AuditLog.timestamp.desc()).first()
            if last and last.event_type == 'fallback_attempts':
                print('AuditLog persisted:', {'id': last.id, 'user_id': last.user_id, 'details': last.details})
            else:
                print('No fallback audit log found (or last event not fallback_attempts)')
        finally:
            session.close()

    finally:
        # Restore originals
        local_llm_service.generate = orig_generate
        confidence_model.score = orig_score

if __name__ == '__main__':
    asyncio.run(run_test())
