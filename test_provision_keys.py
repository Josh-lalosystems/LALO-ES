#!/usr/bin/env python
"""Test script to manually provision API keys for demo user"""

import os
import logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("lalo.test_provision_keys")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

from core.services.key_management import key_manager, APIKeyRequest
from pydantic import SecretStr

user_id = "demo-user@example.com"

# Get current keys
logger.info(f"Checking existing keys for {user_id}...")
existing_keys = key_manager.get_keys(user_id)
logger.info(f"Existing keys: {list(existing_keys.keys()) if existing_keys else 'None'}")

# Get keys from environment
demo_openai = os.getenv("DEMO_OPENAI_KEY", "")
demo_anthropic = os.getenv("DEMO_ANTHROPIC_KEY", "")

logger.info("\nEnvironment API keys:")
logger.info(f"  DEMO_OPENAI_KEY: {'Set (' + demo_openai[:20] + '...)' if demo_openai else 'Not set'}")
logger.info(f"  DEMO_ANTHROPIC_KEY: {'Set (' + demo_anthropic[:20] + '...)' if demo_anthropic else 'Not set'}")

# Provision keys
if demo_openai or demo_anthropic:
    logger.info("\nProvisioning API keys...")
    key_request = APIKeyRequest(
        openai_key=SecretStr(demo_openai) if demo_openai else None,
        anthropic_key=SecretStr(demo_anthropic) if demo_anthropic else None
    )
    key_manager.set_keys(user_id, key_request)
    logger.info(f"✓ Keys provisioned successfully")

    # Verify
    logger.info(f"\nVerifying keys...")
    updated_keys = key_manager.get_keys(user_id)
    logger.info(f"Updated keys: {list(updated_keys.keys()) if updated_keys else 'None'}")
else:
    logger.info("\nNo API keys found in environment")
