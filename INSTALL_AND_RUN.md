INSTALL_AND_RUN.md

````
# Copyright (c) 2025 LALO AI LLC. All rights reserved.

# INSTALL_AND_RUN.md
## LALO Demo — Local Install & Run (Non-technical + Engineer-friendly)

This document explains how to run the LALO demo scaffold on a local laptop (recommended: 16GB RAM, CPU-only) or using Docker Compose. Follow the platform section that matches your OS. If you are non-technical, follow the step-by-step commands exactly; if you are an engineer, the notes include extra details for extension.

---

## Quick summary (one-line)
1. Create a Python 3.11 venv → 2. `pip install -r requirements.txt` → 3. Copy `.env.example` → 4. Start services (see below) → 5. Open `http://localhost:8000`.

---

## Prerequisites (install once)

- **Python 3.11 (or later)** — confirm with:
  ```bash
  python --version
````

* **pip** (comes with Python)
* **Git** (optional, for cloning)
* **(Optional)** Docker & Docker Compose — for containerized runs
* **(Optional)** Node.js — only if you plan extra frontend tooling (not required for demo)

Notes:

* If you don't have admin rights, you can still run the demo in a Python venv.
* The demo is intentionally lightweight; local model usage (GPT-OSS, HRM) is optional and will require additional downloads and hardware.

---

## File checklist (make sure these exist in the project root)

* `requirements.txt`
* `.env.example`
* `core/`, `rtinterpreter/`, `mcp/`, `creation/`, `connectors/`
* `demo_start.sh` (Unix convenience script)
* `docker-compose.yml` (optional Docker run)
* `README.md`, `ROADMAP.md`, `LICENSE.txt`

---

## Step A — Create & activate Python virtual environment

### macOS / Linux

```bash
cd /path/to/project
python -m venv venv
source venv/bin/activate
```

### Windows (PowerShell)

```powershell
cd C:\path\to\project
python -m venv venv
venv\Scripts\Activate.ps1
# or using cmd:
# venv\Scripts\activate
```

You should see `(venv)` in your shell prompt when active.

---

## Step B — Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Playwright**: the project uses `playwright` for RPA/web-UI demos (optional). After pip installing requirements, run:

```bash
playwright install
```

This installs browser binaries Playwright needs.

---

## Step C — Configure environment variables

Copy the example env file and edit any values you need:

```bash
cp .env.example .env        # macOS / Linux
copy .env.example .env      # Windows (cmd)
```

Defaults in `.env.example` point at local mock connectors (for demo). If you later have real endpoints (S/4HANA trial, Workday trial, SharePoint), update:

* `S4_MOCK_URL` → real S4/OData endpoint
* `WORKDAY_MOCK_URL` → real Workday endpoint
* `SHAREPOINT_MOCK_URL` → Graph/SharePoint endpoint
* `USE_LOCAL_MODELS=true` if you will use local GPT-OSS/HRM (read model notes below)

**Important:** Do NOT commit real API keys into git. Use `.env` for local testing only; keep keys private.

---

## Step D — How to run services locally (recommended for first run)

Open separate terminals (or use `tmux`, `screen`, or separate windows). Start services in this order:

1. RTI (Recursive Task Interpreter)

```bash
uvicorn rtinterpreter.main:app --port 8101 --reload
```

2. MCP (Model Alignment Protocol — planner & executor)

```bash
uvicorn mcp.main:app --port 8102 --reload
```

3. Creation (CPS)

```bash
uvicorn creation.main:app --port 8103 --reload
```

4. Connectors (mocks)

```bash
uvicorn connectors.mock_s4.mock_s4:app --port 8201 --reload
uvicorn connectors.mock_workday.mock_workday:app --port 8202 --reload
uvicorn connectors.mock_sharepoint.mock_sharepoint:app --port 8203 --reload
```

5. Core Runtime (web UI)

```bash
uvicorn core.main:app --port 8000 --reload
```

After starting Core, open a browser at:

```
http://localhost:8000
```

Use the built-in form to submit the sample request and step through: Interpret → Approve → Plan → Approve → Execute.

---

## Convenience: single-script start (Unix)

The project includes a `demo_start.sh` (editable). You can run:

```bash
chmod +x demo_start.sh
./demo_start.sh
# NOTE: this starts background processes; use it for demos but prefer explicit uvicorn commands during development.
```

**Windows**: if you want a one-liner, create a `demo_start.bat` to run the corresponding `venv\Scripts\activate` then `uvicorn ...` commands (the repo does not ship a .bat by default).

---

## Step E — Running tests

A few basic pytest tests are included. Run them after starting services (some tests expect services running):

```bash
pytest -q
```

---

## Docker Compose (alternative)

If you prefer containers, ensure Docker & Compose are installed, then:

```bash
docker compose up --build
```

This builds images and binds ports described in `docker-compose.yml`. After startup, visit:

```
http://localhost:8000
```

To stop:

```bash
docker compose down
```

---

## Enabling local models (optional, advanced)

If you want to try local models (GPT-OSS or Sapient HRM), set:

```
USE_LOCAL_MODELS=true
```

in `.env`. **Note**:

* Local LLMs can be large. On a 16GB laptop you'll be limited to smaller quantized models. Expect longer load times and higher CPU usage.
* For production/demo cloud runs, deploy models on a VPC with GPUs for best performance.
* Model integration is provided by plugin hooks — additional install steps and model weights are required (these are not included in the scaffold).

---

## Vector memory (local, demo)

A lightweight TF-IDF/NearestNeighbors store is included (`vector_store.py`). It:

* Persists to `vector_store.pkl` in the project root.
* Is automatically updated by demonstration code hooks (you can call `.add()` to insert template docs).
* For a production-like vector DB, use FAISS/Chroma/Weaviate — see `ROADMAP.md`.

---

## Microsoft SSO (Azure AD) — demo notes

* The scaffold contains a mock SSO endpoint for demoing the UX.
* To enable real Azure AD SSO, you must:

  1. Register an app in Azure AD (Tenant admin required).
  2. Configure Redirect URI to `http://localhost:8000/` (or the auth route you implement).
  3. Add client id & secret to `.env` and implement `authlib`/OAuth flows in the Core service.
* If you want, we can provide a step-by-step "Azure AD app registration" guide and add sample code.

---

## Playwright & RPA demos (optional)

If you plan to demo legacy UI automation:

1. Install Playwright (already in `requirements.txt`): `pip install playwright`
2. Install browsers: `playwright install`
3. Example Playwright scripts live in `connectors/` and can be executed as Python scripts. They are included as templates and require a visible browser or headless mode configured.

---

## Troubleshooting & common issues

* **"port already in use"**: Some service failed to start because the port is taken. Kill existing process or change port in `.env` and corresponding service files.
* **ImportError / Module not found**: Ensure `venv` is activated and `pip install -r requirements.txt` completed without errors.
* **Playwright errors**: Run `playwright install` after installing Python packages.
* **CORS / Browser errors**: If you call services directly from browser JS, ensure services accept cross-origin or use the Core UI endpoints which proxy server-to-server calls.
* **Slow performance**: Local models are CPU-bound; consider running on a VPC with more resources for demos that involve large models.

---

## Where logs and data live

* SQLite demo DB files (if created) default to `/tmp/` on Linux/Mac or project root on Windows depending on code defaults.
* Vector store persistence: `vector_store.pkl` in project root.

---

## Next steps (optional enhancements)

1. Replace mock connectors with real S/4HANA & Workday trial connectors (update `.env`).
2. Add real Azure AD SSO flow and documentation.
3. Replace TF-IDF memory with FAISS or Chroma and add `sentence-transformers` embeddings.
4. Harden CPS sandboxing with containerized runner for generated artifacts.

---

## Contact & support

If you encounter an issue you cannot resolve, capture:

* Terminal stderr output
* The `.env` contents (don't share secrets; redact API keys)
  and provide them to the engineering lead for troubleshooting.

---

## End of file

```
