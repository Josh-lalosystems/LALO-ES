"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from typing import List, Set
from uuid import uuid4
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.rbac import Role, Permission, UserRole, RolePermission


class RBACService:
    def __init__(self):
        pass

    def get_session(self) -> Session:
        return SessionLocal()

    def ensure_permission(self, name: str) -> Permission:
        s = self.get_session()
        try:
            p = s.query(Permission).filter(Permission.name == name).first()
            if p:
                return p
            p = Permission(id=str(uuid4()), name=name)
            s.add(p)
            s.commit()
            s.refresh(p)
            return p
        finally:
            s.close()

    def ensure_role(self, name: str) -> Role:
        s = self.get_session()
        try:
            r = s.query(Role).filter(Role.name == name).first()
            if r:
                return r
            r = Role(id=str(uuid4()), name=name)
            s.add(r)
            s.commit()
            s.refresh(r)
            return r
        finally:
            s.close()

    def grant_permission_to_role(self, role_name: str, perm_name: str):
        s = self.get_session()
        try:
            role = s.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(id=str(uuid4()), name=role_name)
                s.add(role)
                s.commit()
                s.refresh(role)
            perm = s.query(Permission).filter(Permission.name == perm_name).first()
            if not perm:
                perm = Permission(id=str(uuid4()), name=perm_name)
                s.add(perm)
                s.commit()
                s.refresh(perm)
            exists = s.query(RolePermission).filter(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == perm.id
            ).first()
            if not exists:
                rp = RolePermission(id=str(uuid4()), role_id=role.id, permission_id=perm.id)
                s.add(rp)
                s.commit()
        finally:
            s.close()

    def assign_role_to_user(self, user_id: str, role_name: str):
        s = self.get_session()
        try:
            role = s.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(id=str(uuid4()), name=role_name)
                s.add(role)
                s.commit()
                s.refresh(role)
            exists = s.query(UserRole).filter(UserRole.user_id == user_id, UserRole.role_id == role.id).first()
            if not exists:
                ur = UserRole(id=str(uuid4()), user_id=user_id, role_id=role.id)
                s.add(ur)
                s.commit()
        finally:
            s.close()

    def get_user_permissions(self, user_id: str) -> Set[str]:
        s = self.get_session()
        try:
            perms: Set[str] = set()
            roles = s.query(UserRole).filter(UserRole.user_id == user_id).all()
            for ur in roles:
                rps = s.query(RolePermission).filter(RolePermission.role_id == ur.role_id).all()
                for rp in rps:
                    p = s.query(Permission).filter(Permission.id == rp.permission_id).first()
                    if p:
                        perms.add(p.name)
            return perms
        finally:
            s.close()


rbac_service = RBACService()
