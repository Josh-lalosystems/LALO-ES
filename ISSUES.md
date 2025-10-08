# Issues & Bugs - running tally

This file tracks issues discovered while testing the local dev environment and UI. Add short entries with status and minimal reproduction steps.

- [ ] Feedback widget submit button appears to do nothing in the UI
  - Status: WIP - frontend posts to `/api/ai/feedback` but backend workflow canonical endpoint is `/api/workflow/{session_id}/feedback`.
  - Action taken: Added a low-risk compatibility alias `POST /api/ai/feedback` (in `core/routes/ai_routes.py`) that will attempt to forward to the workflow orchestrator when `response_id` looks like a session id; otherwise it returns an acknowledgement so the UI receives success.
  - Next steps:
    1. (Preferred) Update frontend to call `/api/workflow/{session_id}/feedback` with the correct `session_id` for workflow feedback buttons (requires wiring response->session mapping in the UI).
    2. (Alternative) Improve alias to persist feedback into the feedback table and link to sessions via response->session lookup.

- [ ] Demo mode is enabled and causing heuristic (demo) responses instead of real inference
  - Status: Observed. `.env` contains `DEMO_MODE=true`.
  - Action taken: Confirmed demo behavior and provided instructions to set `DEMO_MODE=false` and restart backend. `scripts/inspect_demo_keys.py` shows OpenAI key validates.
  - Next steps: Restart backend with DEMO_MODE disabled and re-test AI requests.

- [ ] Port 8000 binding / zombie uvicorn process
  - Status: Observed earlier. PID 21564/4432 was using port 8000.
  - Action taken: Diagnostics performed. Use `Stop-Process -Id <pid> -Force` to free the port if needed.

Notes:
- This file is intended as a short, actionable checklist. Please add more issues as you find them.
