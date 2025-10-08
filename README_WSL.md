WSL development helper
======================

This project includes helper scripts for working inside WSL (Ubuntu-22.04) using a dedicated venv at `/mnt/c/IT/LALOai-main/.venv-wsl`.

Quick setup (from WSL shell)
----------------------------

```bash
cd /mnt/c/IT/LALOai-main
# create venv (if not already created)
python3 -m venv .venv-wsl
source .venv-wsl/bin/activate
pip install --upgrade pip setuptools wheel scikit-build cmake
# install runtime/dev deps as needed
pip install -r requirements-dev.txt || true
```

Useful scripts
--------------

- `scripts/wsl_activate_and_run.sh <command...>` — activate the WSL venv and run the given command. If no args are provided, opens an interactive shell with the venv activated.
- `scripts/wsl_run_tests.sh` — activates the venv and runs the focused pytest suite used in development.

Examples
--------

Run runtime checks (from WSL):

```bash
./scripts/wsl_activate_and_run.sh python -m services.document_service.services.runtime_checks --json
```

Run the focused tests:

```bash
./scripts/wsl_run_tests.sh
```

Notes
-----
- The WSL venv sits on the Windows filesystem (`/mnt/c/...`) to share the same repo copy; for faster IO during native builds consider cloning into the WSL home directory and creating a native venv there.
- If you need the Llama.cpp Python bindings, build them in WSL (the venv above) — the environment here is already prepared for that (`pip install llama-cpp-python`).
