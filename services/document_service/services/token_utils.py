"""Token utilities: try to use a real tokenizer for accurate token counts,
fall back to word-splitting if tokenizer libraries are unavailable.
"""
from typing import Optional
import logging
logger = logging.getLogger(__name__)


def _try_tiktoken_count(text: str) -> Optional[int]:
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return None


def _try_transformers_count(text: str, model_name: str = "all-MiniLM-L6-v2") -> Optional[int]:
    try:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(model_name)
        toks = tok(text, return_length=True)
        # return_length may be in returned dict for some tokenizers; fallback
        if isinstance(toks, dict) and "input_ids" in toks:
            return len(toks["input_ids"])
        return None
    except Exception:
        return None


def count_tokens(text: str) -> int:
    """Return a token count for text. Tries tiktoken, then transformers, then words."""
    if not text:
        return 0

    # Try fast accurate encoders first
    n = _try_tiktoken_count(text)
    if n is not None:
        return n

    n = _try_transformers_count(text)
    if n is not None:
        return n

    # Fallback: approximate by splitting on whitespace
    try:
        return len(text.split())
    except Exception:
        return max(0, len(text) // 4)
