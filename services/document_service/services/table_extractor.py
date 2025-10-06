"""
Simple table extractor for Word and Excel documents.

Provides helpers to convert table objects to CSV-like text and return as chunk dicts
compatible with the chunker output shape.
"""
from typing import List, Dict, Any
import csv
import hashlib
from io import StringIO
from .token_utils import count_tokens


def _rows_to_csv_text(rows: List[List[Any]]) -> str:
    buf = StringIO()
    writer = csv.writer(buf)
    for r in rows:
        # Ensure all cells are strings
        writer.writerow([str(c) if c is not None else "" for c in r])
    return buf.getvalue()


def word_table_to_chunks(tables, doc_id: str, start_id: int = 0) -> List[Dict]:
    chunks = []
    table_id = start_id
    for t in tables:
        table_id += 1
        rows = []
        for r in t.rows:
            cells = [c.text for c in r.cells]
            rows.append(cells)

        text = _rows_to_csv_text(rows)
        h = hashlib.sha256()
        h.update(f"{doc_id}|table|{table_id}|".encode('utf-8'))
        h.update(text.encode('utf-8'))
        chunks.append({
            'chunk_id': h.hexdigest(),
            'doc_id': doc_id,
            'level': 'table',
            'text': text,
            'token_count': count_tokens(text),
            'start_char': None,
            'end_char': None,
            'table_rows': len(rows),
            'table_columns': max((len(r) for r in rows), default=0)
        })

    return chunks


def excel_tables_to_chunks(workbook, doc_id: str, start_id: int = 0) -> List[Dict]:
    chunks = []
    table_id = start_id
    for sheet_name in workbook.sheetnames:
        ws = workbook[sheet_name]
        # Attempt to detect region with data
        rows = []
        for row in ws.iter_rows(values_only=True):
            # Stop if empty row? keep best-effort
            rows.append(list(row))

        if not rows:
            continue

        table_id += 1
        text = _rows_to_csv_text(rows)
        h = hashlib.sha256()
        h.update(f"{doc_id}|sheet|{sheet_name}|{table_id}|".encode('utf-8'))
        h.update(text.encode('utf-8'))
        chunks.append({
            'chunk_id': h.hexdigest(),
            'doc_id': doc_id,
            'level': 'table',
            'text': text,
            'token_count': count_tokens(text),
            'start_char': None,
            'end_char': None,
            'sheet_name': sheet_name,
            'table_rows': len(rows),
            'table_columns': max((len(r) for r in rows), default=0)
        })

    return chunks
