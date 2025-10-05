# Changelog

## 2025-10-04 — Phase 3 frontend/ux branch updates

### Fixed
- Converted many ad-hoc print() calls across tests and scripts to structured logging (logger.info/warning/exception).
- Fixed import-time crash caused by orphaned except blocks in `core/routes/ai_routes.py` and hardened tool initialization to avoid import failures.
- Restored demo-mode flows so frontend no longer redirects to login on request submission when provider API keys are missing or invalid.

### Improved
- Added demo-mode tolerant AI route fallbacks and a lightweight demo image placeholder.
- Centralized logging configuration in `app.py` and added module-level loggers across scripts/tests.
- Added pytest tests for demo flows and key validation; made tests robust with provider mocks.
- Added GitHub Actions workflow to run tests on push/PR (`.github/workflows/python-tests.yml`).

### CI/DevOps
- Updated repository README with CI badge.
- Added CI workflow improvements: matrix builds, pip caching, and test artifact upload (pytest results & coverage).

### Notes
- Some legacy scripts still reference prints in documentation files; documentation commands (markdown) left unchanged.
- Recommend running CI on main branch after merging to ensure badge becomes active.

