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
Security Middleware

Provides rate limiting, request validation, and security headers
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple
import time


class RateLimiter:
    """
    Simple in-memory rate limiter
    Production should use Redis or similar
    """

    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.limits = {
            'per_minute': 60,
            'per_hour': 1000,
            'per_day': 10000
        }

    def check_rate_limit(self, user_id: str) -> Tuple[bool, str]:
        """
        Check if user has exceeded rate limits

        Returns:
            (allowed: bool, limit_type: str)
        """
        now = time.time()

        # Clean old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < 86400  # Keep last 24 hours
        ]

        requests = self.requests[user_id]

        # Check per minute
        minute_ago = now - 60
        recent_requests = [r for r in requests if r > minute_ago]
        if len(recent_requests) >= self.limits['per_minute']:
            return False, "per_minute"

        # Check per hour
        hour_ago = now - 3600
        hourly_requests = [r for r in requests if r > hour_ago]
        if len(hourly_requests) >= self.limits['per_hour']:
            return False, "per_hour"

        # Check per day
        day_ago = now - 86400
        daily_requests = [r for r in requests if r > day_ago]
        if len(daily_requests) >= self.limits['per_day']:
            return False, "per_day"

        # Record this request
        self.requests[user_id].append(now)

        return True, ""

    def get_limit_info(self, user_id: str) -> Dict:
        """Get current rate limit status for user"""
        now = time.time()
        requests = self.requests.get(user_id, [])

        minute_ago = now - 60
        hour_ago = now - 3600
        day_ago = now - 86400

        return {
            "requests_last_minute": len([r for r in requests if r > minute_ago]),
            "limit_per_minute": self.limits['per_minute'],
            "requests_last_hour": len([r for r in requests if r > hour_ago]),
            "limit_per_hour": self.limits['per_hour'],
            "requests_last_day": len([r for r in requests if r > day_ago]),
            "limit_per_day": self.limits['per_day']
        }


# Global rate limiter instance
rate_limiter = RateLimiter()


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware for all requests
    """

    async def dispatch(self, request: Request, call_next):
        # Add security headers
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware
    """

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for certain paths
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/auth/demo-token"]
        if request.url.path in skip_paths:
            return await call_next(request)

        # Get user ID (from auth or IP address)
        user_id = getattr(request.state, 'user_id', None) or request.client.host

        # Check rate limit
        allowed, limit_type = rate_limiter.check_rate_limit(user_id)

        if not allowed:
            limit_info = rate_limiter.get_limit_info(user_id)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded: {limit_type}",
                    "limit_info": limit_info
                },
                headers={
                    "Retry-After": "60"  # Retry after 60 seconds
                }
            )

        response = await call_next(request)
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Validate and sanitize all incoming requests
    """

    async def dispatch(self, request: Request, call_next):
        # Check content length
        content_length = request.headers.get('content-length')
        if content_length:
            if int(content_length) > 10_000_000:  # 10MB limit
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Request body too large (max 10MB)"}
                )

        # Check content type for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get('content-type', '')
            allowed_types = ['application/json', 'application/x-www-form-urlencoded', 'multipart/form-data']

            if not any(ct in content_type for ct in allowed_types):
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={"detail": f"Unsupported content type: {content_type}"}
                )

        response = await call_next(request)
        return response
