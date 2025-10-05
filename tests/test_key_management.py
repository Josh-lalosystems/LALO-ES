import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from core.services import key_management

@pytest.mark.asyncio
async def test_validate_keys_openai_success(monkeypatch):
    user_id = "demo-user@example.com"
    # Mock get_keys on KeyManager class to return an openai key
    monkeypatch.setattr(key_management.KeyManager, 'get_keys', lambda self, uid: {"openai": "sk-test"})

    # Mock AsyncOpenAI client
    class FakeClient:
        def __init__(self, api_key=None):
            pass
        class chat:
            class completions:
                @staticmethod
                async def create(*args, **kwargs):
                    return True

    with patch('core.services.key_management.AsyncOpenAI', FakeClient):
        status = await key_management.key_manager.validate_keys(user_id)
        assert status.get('openai') is True

@pytest.mark.asyncio
async def test_validate_keys_anthropic_failure(monkeypatch):
    user_id = "demo-user@example.com"
    # Mock get_keys to return an anthropic key
    # Mock get_keys on KeyManager class to return an anthropic key
    monkeypatch.setattr(key_management.KeyManager, 'get_keys', lambda self, uid: {"anthropic": "ak-test"})

    # Fake Anthropic client that raises
    class FakeAnthropic:
        def __init__(self, api_key=None):
            pass
        class messages:
            @staticmethod
            async def create(*args, **kwargs):
                raise Exception('organization disabled')

    with patch('core.services.key_management.AsyncAnthropic', FakeAnthropic):
        # Ensure AsyncOpenAI is None so only Anthropic branch is exercised
        with patch('core.services.key_management.AsyncOpenAI', None):
            status = await key_management.key_manager.validate_keys(user_id)
            # anthropic should not be True (either False or missing) due to simulated failure
            assert not status.get('anthropic')
