#!/usr/bin/env bash
set -euo pipefail
# Activate the WSL venv created for this project and run arbitrary commands.
# Usage:
#   ./scripts/wsl_activate_and_run.sh <command...>
# Example:
#   ./scripts/wsl_activate_and_run.sh python -c "import llama_cpp; print(llama_cpp.__version__)"

REPO_ROOT="/mnt/c/IT/LALOai-main"
VENV="$REPO_ROOT/.venv-wsl"

if [ ! -d "$VENV" ]; then
  echo "WSL venv not found at $VENV"
  echo "Create it with: python3 -m venv .venv-wsl" >&2
  exit 2
fi

if [ $# -eq 0 ]; then
  echo "No command provided. Opening an interactive shell within the venv."
  exec bash -i -c "source $VENV/bin/activate && exec bash"
else
  cmd=("$@")
  echo "Running in WSL venv: ${cmd[*]}"
  bash -lc "source $VENV/bin/activate && ${cmd[*]}"
fi
