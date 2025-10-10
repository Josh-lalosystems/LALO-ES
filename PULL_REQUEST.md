Title: Align repository with Milestone 1 — cleanup, telemetry persistence, UI surface

Description:
This PR aligns the repo with the Milestone 1 objectives by:

- Adding per-request persistence for `fallback_attempts` (new JSON column on `requests` table and DatabaseService helper)
- Persisting fallback telemetry to `AuditLog` (existing) and attaching attempts to `requests` rows
- Introducing `core/milestone_progress.md` and an updater utility for team progress tracking
- Cleaning up temporary files and adding `.gitignore` rules for models, logs and backups
- Small frontend change to surface a compact fallback summary in `App.js`

Checklist before merge:
- [ ] Confirm database migrations (add `fallback_attempts` JSON column) are applied in target environment
- [ ] Run integration test that exercises fallback flow and verifies `requests.fallback_attempts`
- [ ] Optional: run `.\scripts\perform_cleanup.ps1 -Remove` to relocate temp files to backups
- [ ] Ensure no sensitive files are staged (env, keys, tokens)

Notes for reviewer:
- The `attach_fallbacks_to_request` helper is in `core/services/database_service.py`.
- To test locally: start server, send a chat request that triggers fallback, and inspect DB or use `scripts/force_fallback_test.py`.
