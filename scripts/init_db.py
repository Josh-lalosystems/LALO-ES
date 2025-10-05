#!/usr/bin/env python
"""
LALO AI - Database Initialization Script

This script performs minimal DB initialization for developer/testing machines:
- creates tables
- creates a demo user
- validates (and optionally generates) an encryption key for local testing

It is designed to run on developer machines and CI; for production, run with
appropriate environment variables and secure key management.
"""

import os
import sys
from pathlib import Path
import logging

# ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import Base, engine, SessionLocal, User
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("lalo.scripts.init_db")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


def check_encryption_key() -> bool:
    """Return True if ENCRYPTION_KEY already present, otherwise generate one and
    return False (caller should persist it for future runs if desired).
    """
    key = os.getenv("ENCRYPTION_KEY")
    if key:
        logger.info("[OK] ENCRYPTION_KEY is set")
        return True
    logger.warning("ENCRYPTION_KEY not set; generating a temporary key for this run")
    new_key = Fernet.generate_key().decode()
    logger.info("Temporary ENCRYPTION_KEY (persist to .env for reuse): %s", new_key)
    os.environ["ENCRYPTION_KEY"] = new_key
    return False


def init_database() -> bool:
    """Create DB tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("[OK] Database tables created or already exist")
        return True
    except Exception as exc:
        logger.exception("[ERROR] Failed to create tables: %s", exc)
        return False


def create_demo_user() -> bool:
    """Create demo user if missing."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "demo-user@example.com").first()
        if user:
            logger.info("[INFO] Demo user already present")
            return True
        u = User(id="demo-user-id", email="demo-user@example.com")
        db.add(u)
        db.commit()
        logger.info("[OK] Demo user created")
        return True
    except Exception:
        logger.exception("[ERROR] Could not create demo user")
        try:
            db.rollback()
        except Exception:
            pass
        return False
    finally:
        db.close()


def verify_database() -> bool:
    db = SessionLocal()
    try:
        cnt = db.query(User).count()
        logger.info("[OK] DB verification: %d users", cnt)
        return True
    except Exception:
        logger.exception("[ERROR] DB verification failed")
        return False
    finally:
        db.close()


def main() -> None:
    logger.info("%s", "=" * 60)
    logger.info("LALO AI - Database Initialization")
    logger.info("%s", "=" * 60)

    key_exists = check_encryption_key()
    if not init_database():
        logger.error("Database init failed")
        sys.exit(1)
    if not create_demo_user():
        logger.error("Demo user creation failed")
        sys.exit(1)
    if not verify_database():
        logger.error("Database verification failed")
        sys.exit(1)

    logger.info("[SUCCESS] Init complete")
    if not key_exists:
        logger.warning("Remember to persist ENCRYPTION_KEY to .env for future runs")


if __name__ == "__main__":
    main()
