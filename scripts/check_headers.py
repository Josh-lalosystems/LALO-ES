#!/usr/bin/env python3
"""
Check which textual files in the repo lack the LALO copyright header.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SKIP_DIRS = {'node_modules', 'venv', '__pycache__', 'dist', 'build', '.git', 'models'}

def is_binary(p: Path) -> bool:
    try:
        with open(p, 'rb') as f:
            chunk = f.read(1024)
            if b'\x00' in chunk:
                return True
            text_chars = b"\n\r\t\b\f" + bytes(range(32, 127))
            nontext = sum(1 for c in chunk if c not in text_chars)
            if len(chunk) == 0:
                return False
            return (nontext / len(chunk)) > 0.3
    except Exception:
        return True


def has_header(text: str) -> bool:
    return ('LALO AI SYSTEMS, LLC' in text) or ('Copyright (c) 2025' in text)

missing = []
scanned = 0
for p in ROOT.rglob('*'):
    if p.is_dir():
        continue
    if any(part in SKIP_DIRS for part in p.parts):
        continue
    if p.suffix.lower() == '.json':
        continue
    if is_binary(p):
        continue
    # read textual
    try:
        text = p.read_text(encoding='utf-8')
    except Exception:
        continue
    scanned += 1
    if not has_header(text):
        missing.append(str(p))

print(f"Scanned textual files: {scanned}")
print(f"Files missing header: {len(missing)}")
if missing:
    print("\n".join(missing))
    sys.exit(2)
else:
    print("All textual files (excluding JSON/binaries) contain the header.")
    sys.exit(0)
