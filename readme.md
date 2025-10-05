# LALO AI Platform

![CI](https://github.com/Josh-lalosystems/LALO-ES/actions/workflows/python-tests.yml/badge.svg)

## Overview
LALO is a workflow automation and chat platform for professional agents, investors, and end users. It features:
- **100% Local AI Inference** - No cloud dependencies, runs on CPU/GPU
- **Router-Based Architecture** - Intelligent request routing for optimal performance
- Professional chat UI (see `lalo-frontend/src/components/Chat/`)
- Data connectors (SharePoint, Cloud, Database)
- Workflow automation with multi-model orchestration
- Confidence validation and quality scoring
- Demo data and scripts

## Quick Start - Local Inference

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download AI Models (Required)
Download open-source models to run locally (no API keys needed):
```bash
python scripts/download_models.py
```

This downloads:
- **TinyLlama 1.1B** (669 MB) - General chat
- **Liquid Tool 1.2B** (752 MB) - Function calling & routing
- **Qwen 0.5B** (352 MB) - Confidence validation

Total: ~1.8 GB

### 3. Start the Server
```bash
python app.py
```

Navigate to http://localhost:8000

### 4. Use Local Models
- Select "Auto (Router Decides)" for intelligent routing
- Or manually select TinyLlama, Liquid Tool, or Qwen models
- No API keys required - 100% local inference

### Optional: Add Cloud Models
Go to Settings → Add OpenAI or Anthropic API keys for cloud fallback.

---

## Full Documentation
- See [`docs/USER_MANUAL.md`](docs/USER_MANUAL.md) for detailed instructions
- See [`docs/DEPLOYMENT_GUIDE.md`](docs/DEPLOYMENT_GUIDE.md) for production deployment
- Seed demo data: `python scripts/seed_demo_data.py`

## Demo & Documentation
- Demo walkthrough: [`docs/demo/DEMO_SCRIPT.md`](docs/demo/DEMO_SCRIPT.md)
- Use cases: [`docs/demo/USE_CASES.md`](docs/demo/USE_CASES.md)
- Investor pitch: [`docs/demo/INVESTOR_PITCH.md`](docs/demo/INVESTOR_PITCH.md)

## API Reference
- See [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md)

## Parallel Work Completion
This codebase implements Steps 27–43 in parallel:
- Backend: Data connectors, feedback, learning engine, API endpoints
- Frontend: Professional chat UI, streaming, workflow visualization, demo scripts

All documentation and demo scripts are included for rapid onboarding and testing.
# Copyright (c) 2025 LALO AI LLC. All rights reserved.

# LALO Demo MVP — Repository Overview

This repository is a complete demo scaffold for the LALO (Local Alignment Legacy Overlay) MVP.
It demonstrates the multi-step alignment workflow (RTI → MCP → CPS → Execution) using a set of
FastAPI microservices, mock connectors (S/4HANA, Workday, SharePoint), a simple vector memory
example, and a small Core UI to drive the flow.

The demo is intended to be run locally on a mid-tier laptop (16GB RAM, CPU) or in a VPC for more
compute. The scaffold is model-agnostic and includes hooks for local models (GPT-OSS, Sapient HRM)
or external APIs.

## Contents

- `core/` — Core runtime service + frontend (user interaction).
- `rtinterpreter/` — Recursive Task Interpreter (RTI) service for intent parsing & confidence.
- `mcp/` — Model Alignment Protocol (Action Planner + Executor).
- `creation/` — Creation Protocol Server (CPS) for auto-generating connectors/artifacts.
- `connectors/` — Mock connectors for S/4HANA, Workday, and SharePoint (live endpoints for demo).
- `vector_store.py` — Lightweight TF-IDF vector memory for retrieval-augmented planning.
- `utils/` — Small helper modules, including a mock SSO endpoint.
- `tests/` — Basic pytest smoke tests.
- `INSTALL_AND_RUN.md` — Non-technical setup and run instructions.
- `INSTALL_DOCKER.md` — Docker Compose instructions.
- `ROADMAP.md` — Engineering roadmap and next steps.

## Quick pointers


## Running tests (developer)

For local development and CI, we provide a small dev requirements file for test tooling. Install dev deps into your virtualenv:

```powershell
python -m pip install -r requirements-dev.txt
```

Then run the pytest suite:

```powershell
# From repository root
python -m pytest -q
```

Notes:
- Tests use fixtures in `tests/conftest.py` to mock authentication and AI providers so they don't require real API keys.
- If you prefer to run the app in demo mode for manual frontend testing, set `DEMO_MODE=true` in `.env`. Demo mode bypasses auth and auto-provisions demo keys for quick experimentation (do NOT enable in production).


## Demo flow (high level)

1. User logs in (mock SSO for demo or configure Azure AD for production flows).
2. User submits an English request via the Core UI.
3. RTI semantically interprets the request, extracts entities, returns a confidence score.
4. After user approval, MCP generates a stepwise Action Plan and returns plan confidence.
5. After plan approval, MCP executes the plan by calling connectors (mock or real).
6. Creation server can generate/connect new connectors if MCP detects missing tooling (mocked).
7. Results are returned to the user along with a full audit trace and confidence scores.
8. Vector store stores successful plan templates and helps future retrievals.

## License & Copyright

This demo scaffold and its source files are proprietary to **LALO AI LLC**.
Do not distribute without express permission.

---

If you're ready, tell me to provide the **next file** (I will output its exact content and the filename). We will go file-by-file so you can paste each into Notepad and save them manually.
