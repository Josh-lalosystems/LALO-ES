#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="/mnt/c/IT/LALOai-main"
VENV="$REPO_ROOT/.venv-wsl"

if [ ! -d "$VENV" ]; then
  echo "WSL venv not found at $VENV" >&2
  exit 2
fi

echo "Activating WSL venv and running focused tests..."
bash -lc "cd $REPO_ROOT && source $VENV/bin/activate && python -m pytest -q tests/test_chunker.py tests/test_ingestion_quality_chunking.py tests/test_table_extractor.py -q"
