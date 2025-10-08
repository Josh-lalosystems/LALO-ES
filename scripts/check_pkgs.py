import importlib
import sys
print('Python', sys.version)
for m in ('openai','anthropic'):
    try:
        importlib.import_module(m)
        print(m, 'installed')
    except Exception as e:
        print(m, 'NOT installed:', type(e).__name__, e)
