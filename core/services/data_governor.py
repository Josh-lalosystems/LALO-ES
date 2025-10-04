from typing import Dict, Any, List
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.governance_policy import GovernancePolicy


class DataGovernor:
    def get_session(self) -> Session:
        return SessionLocal()

    def ensure_policy(self, name: str, rules: Dict[str, Any], description: str = "") -> str:
        s = self.get_session()
        try:
            p = s.query(GovernancePolicy).filter(GovernancePolicy.name == name).first()
            now = datetime.now(timezone.utc)
            if p:
                p.rules = rules
                p.updated_at = now
                s.commit()
                return p.id
            p = GovernancePolicy(id=str(uuid4()), name=name, rules=rules, description=description)
            s.add(p)
            s.commit()
            return p.id
        finally:
            s.close()

    def list_policies(self) -> List[Dict[str, Any]]:
        s = self.get_session()
        try:
            rows = s.query(GovernancePolicy).all()
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "enabled": r.enabled,
                    "rules": r.rules or {},
                }
                for r in rows
            ]
        finally:
            s.close()

    def evaluate(self, user_permissions: List[str], tool_category: str, tool_name: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Evaluate if the action is allowed under current policies."""
        s = self.get_session()
        try:
            policies = s.query(GovernancePolicy).filter(GovernancePolicy.enabled == True).all()  # noqa: E712
            decision = {"allowed": True, "reasons": []}
            for p in policies:
                rules = p.rules or {}
                deny_categories = set(rules.get("deny_categories", []))
                if tool_category in deny_categories:
                    decision["allowed"] = False
                    decision["reasons"].append(f"Category '{tool_category}' denied by policy {p.name}")

                require_perms = rules.get("require_perms", {})
                for perm, needed in require_perms.items():
                    if needed and perm not in user_permissions:
                        decision["allowed"] = False
                        decision["reasons"].append(f"Missing required permission '{perm}' per policy {p.name}")
            return decision
        finally:
            s.close()


data_governor = DataGovernor()
