"""
Simple hierarchical chunker: document -> paragraph -> sentence.

This is intentionally minimal: paragraph splitting on double-newline, sentence
splitting via a naive regex. Returns list of chunk dicts with metadata.
"""
from typing import List, Dict
import re
import hashlib
from .token_utils import count_tokens


SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _deterministic_chunk_id(doc_id: str, level: str, text: str) -> str:
    h = hashlib.sha256()
    h.update(f"{doc_id}|{level}|".encode('utf-8'))
    h.update(text.encode('utf-8'))
    return f"{doc_id}:{h.hexdigest()}"


def chunk_text_hierarchical(text: str, doc_id: str = "", max_tokens: int = 400) -> List[Dict]:
    """Return chunks at paragraph and sentence levels.

    Each chunk is a dict: {chunk_id, doc_id, level, text, token_count, start_char, end_char}
    Token count is approximated by word count.
    """
    if not text:
        return []

    chunks: List[Dict] = []
    pos = 0
    para_id = 0
    for para in text.split('\n\n'):
        para = para.strip()
        if not para:
            pos += 2
            continue
        para_start = pos
        para_end = para_start + len(para)
        para_id += 1
        # paragraph-level chunk
        tok_count = count_tokens(para)
        chunk = {
            'chunk_id': _deterministic_chunk_id(doc_id, 'paragraph', para),
            'doc_id': doc_id,
            'level': 'paragraph',
            'text': para,
            'token_count': tok_count,
            'start_char': para_start,
            'end_char': para_end
        }
        chunks.append(chunk)

        # sentence-level chunks
        sentences = SENT_SPLIT_RE.split(para)
        sent_pos = para_start
        sent_id = 0
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            sent_id += 1
            s_start = text.find(s, sent_pos)
            s_end = s_start + len(s) if s_start != -1 else sent_pos + len(s)
            chunks.append({
                'chunk_id': _deterministic_chunk_id(doc_id, 'sentence', s),
                'doc_id': doc_id,
                'level': 'sentence',
                'text': s,
                'token_count': count_tokens(s),
                'start_char': s_start,
                'end_char': s_end
            })
            sent_pos = s_end

        pos = para_end + 2

    return chunks
