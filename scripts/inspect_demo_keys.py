import sys
import asyncio
from pprint import pprint
# Ensure repo root on path
sys.path.insert(0, r"c:\IT\LALOai-main")

from core.services.key_management import key_manager

user = 'demo-user@example.com'
print('Inspecting keys for', user)
keys = key_manager.get_keys(user)
print('get_keys ->')
pprint(keys)

print('\nRunning validate_keys (may attempt network calls)')
try:
    status = asyncio.run(key_manager.validate_keys(user))
    print('validate_keys ->')
    pprint(status)
except Exception as e:
    print('validate_keys raised:', type(e).__name__, e)
