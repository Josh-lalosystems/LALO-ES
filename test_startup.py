#!/usr/bin/env python
"""Test startup validation without running the full server"""

import os
import sys
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger('test_startup')

# Load environment
load_dotenv()

def test_startup_validation():
    """Run the same validation checks as app.py startup"""
    logger.info("%s", "="*60)
    logger.info("LALO AI System - Startup Validation Test")
    logger.info("%s", "="*60)

    warnings = []
    errors = []

    # Environment config
    APP_ENV = os.getenv("APP_ENV", "development")
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

    # Check JWT secret key
    jwt_secret = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    if jwt_secret == "your-secret-key-here":
        if APP_ENV == "production":
            errors.append("JWT_SECRET_KEY must be changed from default in production")
        else:
            warnings.append("JWT_SECRET_KEY is using default value (OK for development)")
    else:
        logger.info("[OK] JWT_SECRET_KEY is configured")

    # Check encryption key
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if not encryption_key:
        warnings.append("ENCRYPTION_KEY not set - API keys will not be encrypted properly")
    else:
        try:
            Fernet(encryption_key.encode())
            logger.info("[OK] ENCRYPTION_KEY is valid")
        except Exception as e:
            errors.append(f"ENCRYPTION_KEY is invalid: {e}")

    # Check demo mode
    if DEMO_MODE:
        warnings.append("DEMO_MODE is enabled - authentication is bypassed!")
        logger.warning("Running in DEMO MODE - authentication bypassed")
    else:
        logger.info("DEMO_MODE is disabled")

    # Check database exists
    db_path = "lalo.db"
    if not os.path.exists(db_path):
        warnings.append(f"Database not found at {db_path}")
    else:
        logger.info("[OK] Database found at %s", db_path)

    # Environment info
    logger.info("[INFO] Environment: %s", APP_ENV)

    # Check CORS origins based on environment
    if APP_ENV == "production":
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
        if not allowed_origins or allowed_origins == [""]:
            allowed_origins = ["https://your-production-domain.com"]
    else:
        allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

    logger.info("[INFO] CORS Origins: %s", ', '.join(allowed_origins))

    # Print warnings
    if warnings:
        logger.info('\n' + '='*60)
        logger.info('WARNINGS:')
        for warning in warnings:
            logger.warning('  [!] %s', warning)

    # Print errors
    if errors:
        logger.error('\n' + '='*60)
        logger.error('ERRORS:')
        for error in errors:
            logger.error('  [X] %s', error)
        logger.error('%s', '='*60)
        return False

    logger.info('%s', '='*60)
    logger.info('[SUCCESS] Startup validation complete')
    logger.info('%s', '='*60)
    return True

if __name__ == "__main__":
    success = test_startup_validation()
    sys.exit(0 if success else 1)
