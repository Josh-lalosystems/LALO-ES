"""Utility to append a timestamped entry to core/milestone_progress.md

Usage:
  python core/update_milestone_progress.py "Short note about progress"

This is safe to run from CI or locally; it creates the file if missing.
"""
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MD = ROOT / "milestone_progress.md"

def append_entry(text: str):
    now = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    header = f"\n- {now} — {text}\n"
    if not MD.exists():
        MD.write_text(f"## Milestone Progress Tracker\n\nCreated: {now}\n\n")
    with MD.open("a", encoding="utf-8") as f:
        f.write(header)
    print("Appended entry to", MD)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python core/update_milestone_progress.py \"Short note\"")
        sys.exit(1)
    append_entry(sys.argv[1])
