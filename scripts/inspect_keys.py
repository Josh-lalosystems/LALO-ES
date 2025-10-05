from core.services.key_management import key_manager
import asyncio

user = 'demo-user@example.com'
import logging
logger = logging.getLogger('scripts.inspect_keys')
logger.info('Keys for %s: %s', user, key_manager.get_keys(user))
logger.info('Validating keys...')
result = asyncio.get_event_loop().run_until_complete(key_manager.validate_keys(user))
logger.info('Validation result: %s', result)
