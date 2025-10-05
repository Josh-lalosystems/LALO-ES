"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Session Management Service

Provides secure session management with:
- Session timeouts
- Concurrent session limits
- Remember me functionality
- Session monitoring and forced logout
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
from uuid import uuid4
import hashlib
import secrets


class UserSession:
    """Represents a user session"""

    def __init__(
        self,
        session_id: str,
        user_id: str,
        created_at: datetime,
        expires_at: datetime,
        ip_address: str,
        user_agent: str,
        remember_me: bool = False
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = created_at
        self.expires_at = expires_at
        self.last_activity = created_at
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.remember_me = remember_me
        self.is_valid = True

    def is_expired(self) -> bool:
        """Check if session has expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now(timezone.utc)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "remember_me": self.remember_me,
            "is_valid": self.is_valid
        }


class SessionManager:
    """
    Manages user sessions with security features
    """

    def __init__(self):
        # In-memory session store (use Redis in production)
        self.sessions: Dict[str, UserSession] = {}

        # Configuration
        self.default_timeout_minutes = 30
        self.remember_me_days = 30
        self.max_concurrent_sessions = 3

    def create_session(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        remember_me: bool = False
    ) -> UserSession:
        """
        Create a new session for user

        Args:
            user_id: User identifier
            ip_address: Client IP address
            user_agent: Client user agent
            remember_me: Whether to extend session duration

        Returns:
            UserSession object
        """
        # Check concurrent session limit
        self._enforce_concurrent_limit(user_id)

        # Generate session ID
        session_id = self._generate_session_id(user_id)

        # Calculate expiration
        now = datetime.now(timezone.utc)
        if remember_me:
            expires_at = now + timedelta(days=self.remember_me_days)
        else:
            expires_at = now + timedelta(minutes=self.default_timeout_minutes)

        # Create session
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            remember_me=remember_me
        )

        # Store session
        self.sessions[session_id] = session

        return session

    def get_session(self, session_id: str) -> Optional[UserSession]:
        """
        Get session by ID

        Returns None if session not found or expired
        """
        session = self.sessions.get(session_id)

        if not session:
            return None

        # Check if expired
        if session.is_expired():
            self.invalidate_session(session_id)
            return None

        # Check if invalidated
        if not session.is_valid:
            return None

        # Update activity
        session.update_activity()

        # Extend expiration for remember_me sessions
        if session.remember_me:
            session.expires_at = datetime.now(timezone.utc) + timedelta(days=self.remember_me_days)

        return session

    def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate a session (logout)

        Returns:
            True if session was invalidated, False if not found
        """
        if session_id in self.sessions:
            self.sessions[session_id].is_valid = False
            del self.sessions[session_id]
            return True
        return False

    def invalidate_user_sessions(self, user_id: str) -> int:
        """
        Invalidate all sessions for a user (force logout all devices)

        Returns:
            Number of sessions invalidated
        """
        count = 0
        sessions_to_remove = []

        for session_id, session in self.sessions.items():
            if session.user_id == user_id:
                session.is_valid = False
                sessions_to_remove.append(session_id)
                count += 1

        for session_id in sessions_to_remove:
            del self.sessions[session_id]

        return count

    def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """
        Get all active sessions for a user

        Returns:
            List of UserSession objects
        """
        user_sessions = []

        for session in self.sessions.values():
            if session.user_id == user_id and session.is_valid and not session.is_expired():
                user_sessions.append(session)

        return user_sessions

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions

        Returns:
            Number of sessions cleaned up
        """
        count = 0
        expired_ids = []

        for session_id, session in self.sessions.items():
            if session.is_expired():
                expired_ids.append(session_id)
                count += 1

        for session_id in expired_ids:
            del self.sessions[session_id]

        return count

    def get_session_info(self, user_id: str) -> Dict:
        """
        Get session information for a user

        Returns:
            Dictionary with session stats
        """
        sessions = self.get_user_sessions(user_id)

        return {
            "active_sessions": len(sessions),
            "max_concurrent_sessions": self.max_concurrent_sessions,
            "sessions": [session.to_dict() for session in sessions]
        }

    def _generate_session_id(self, user_id: str) -> str:
        """
        Generate a secure session ID

        Args:
            user_id: User identifier

        Returns:
            Session ID string
        """
        # Generate random token
        random_token = secrets.token_urlsafe(32)

        # Create hash
        session_data = f"{user_id}:{random_token}:{datetime.now(timezone.utc).isoformat()}"
        session_id = hashlib.sha256(session_data.encode()).hexdigest()

        return session_id

    def _enforce_concurrent_limit(self, user_id: str):
        """
        Enforce concurrent session limit

        Removes oldest session if limit exceeded
        """
        user_sessions = self.get_user_sessions(user_id)

        if len(user_sessions) >= self.max_concurrent_sessions:
            # Sort by creation time
            user_sessions.sort(key=lambda s: s.created_at)

            # Remove oldest session
            oldest_session = user_sessions[0]
            self.invalidate_session(oldest_session.session_id)


# Singleton instance
session_manager = SessionManager()
