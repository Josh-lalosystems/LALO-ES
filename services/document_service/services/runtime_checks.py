"""Runtime checks for optional dependencies used by the document service.

Usage:
  from services.document_service.services.runtime_checks import check_optional_features
  print(check_optional_features())

Or run from CLI to print JSON:
  python -m services.document_service.services.runtime_checks
"""
from __future__ import annotations
import os
import json
import asyncio
import threading
from typing import Dict, Any


def _import_ok(name: str):
    try:
        __import__(name)
        return True, None
    except Exception as e:
        return False, str(e)


def _run_coroutine_sync(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    result = {}
    def runner():
        try:
            result['value'] = asyncio.run(coro)
        except Exception as exc:
            result['error'] = exc
    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()
    if 'error' in result:
        raise result['error']
    return result.get('value')


async def _check_aioredis(redis_url: str) -> Dict[str, Any]:
    try:
        import aioredis
        client = aioredis.from_url(redis_url)
        # try a quick ping
        try:
            pong = await client.ping()
            try:
                await client.close()
            except Exception:
                pass
            return {"available": True, "ping": bool(pong)}
        except Exception as e:
            try:
                await client.close()
            except Exception:
                pass
            return {"available": True, "ping": False, "error": str(e)}
    except Exception as e:
        return {"available": False, "error": str(e)}


def check_optional_features() -> Dict[str, Any]:
    """Return a dict summarizing optional runtime features and their availability.

    Keys include: llama_cpp, tiktoken, transformers, aioredis, redis_connection (if REDIS_URL set),
    llama_model_path (if LLAMA_MODEL_PATH set) with file existence.
    """
    features: Dict[str, Any] = {}

    ok, err = _import_ok('llama_cpp')
    features['llama_cpp'] = {'installed': ok}
    if err:
        features['llama_cpp']['error'] = err

    ok, err = _import_ok('tiktoken')
    features['tiktoken'] = {'installed': ok}
    if err:
        features['tiktoken']['error'] = err

    ok, err = _import_ok('transformers')
    features['transformers'] = {'installed': ok}
    if err:
        features['transformers']['error'] = err

    ok, err = _import_ok('aioredis')
    features['aioredis'] = {'installed': ok}
    if err:
        features['aioredis']['error'] = err

    # Check REDIS_URL connectivity if set
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        try:
            result = _run_coroutine_sync(_check_aioredis(redis_url))
            features['redis_connection'] = result
        except Exception as e:
            features['redis_connection'] = {'available': False, 'error': str(e)}
    else:
        features['redis_connection'] = {'configured': False}

    # Check for local Llama model path (optional environment var)
    llama_model_path = os.getenv('LLAMA_MODEL_PATH')
    if llama_model_path:
        features['llama_model_path'] = {
            'path': llama_model_path,
            'exists': os.path.exists(llama_model_path)
        }
    else:
        features['llama_model_path'] = {'configured': False}

    return features


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Check optional runtime features')
    parser.add_argument('--json', action='store_true', help='Print JSON output')
    args = parser.parse_args()

    out = check_optional_features()
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        for k, v in out.items():
            print(f"{k}: {v}")
