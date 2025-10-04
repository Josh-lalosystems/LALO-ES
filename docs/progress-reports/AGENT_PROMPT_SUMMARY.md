# Quick Agent Prompt - Steps 17-20

Copy and paste this prompt to your GitHub Copilot coding agent:

---

**CRITICAL: Read the complete instructions in `CODING_AGENT_INSTRUCTIONS_STEPS_17-20.md` first!**

## Task Summary

Implement Steps 17-20 of the LALO AI roadmap:
- Step 17: Role-Based Access Control (RBAC)
- Step 18: Audit Logging
- Step 19: Data Governance Policies
- Step 20: Secrets Management

## MANDATORY RULES

### Git Operations (ABSOLUTELY NO EXCEPTIONS):
1. ⚠️ **DO NOT create ANY new branches**
2. ⚠️ **DO NOT checkout ANY branches**
3. ⚠️ **DO NOT switch branches**
4. ⚠️ **DO NOT create new git remotes**
5. ✅ **STAY ON:** `cf/phase3-frontend-ux` (current branch)
6. ✅ **ONLY use:** `git add` and `git commit` (no branch operations)

### Before Starting:
```bash
# 1. Verify current branch
git branch --show-current
# Must show: cf/phase3-frontend-ux

# 2. Verify tools exist
ls core/tools/*.py | wc -l
# Must show: 10

# 3. Verify imports work
python -c "from core.tools import tool_registry; print(len(tool_registry.get_all_tools()))"
# Must show: 7
```

## Implementation Order

1. **Step 20 FIRST** - Secrets Management (1-2 hours)
2. **Step 17** - RBAC (2-3 hours)
3. **Step 18** - Audit Logging (1-2 hours)
4. **Step 19** - Data Governance (2-3 hours)

**Total Time:** 6-10 hours

## Files to Create

### Step 20 - Secrets Management
- `core/services/secrets_manager.py`
- `tests/test_secrets_manager.py`
- Update `core/services/key_management.py`

### Step 17 - RBAC
- `core/models/rbac.py`
- `core/services/rbac.py`
- `core/middleware/auth_middleware.py`
- `lalo-frontend/src/components/admin/UserRoles.tsx`
- `tests/test_rbac.py`

### Step 18 - Audit Logging
- `core/services/audit_logger.py`
- `lalo-frontend/src/components/admin/AuditLogs.tsx`
- `tests/test_audit_logger.py`

### Step 19 - Data Governance
- `core/models/governance_policy.py`
- `core/services/data_governor.py`
- `tests/test_data_governor.py`

## After Completion

Run database migration:
```bash
alembic revision --autogenerate -m "Add RBAC, audit logs, and governance tables"
alembic upgrade head
```

Run tests:
```bash
python -m pytest tests/ -v
```

## DO NOT Modify These Files:
- ❌ Any files in `core/tools/` (except adding imports to `__init__.py`)
- ❌ Any existing workflow files
- ❌ Any git configuration

## If You Encounter Issues:
1. **STOP immediately**
2. **DO NOT try to fix with branch operations**
3. **Document the error**
4. **Report and wait for guidance**

---

**Read the full instructions in:** `CODING_AGENT_INSTRUCTIONS_STEPS_17-20.md`

Start implementation now with Step 20 (Secrets Management).
