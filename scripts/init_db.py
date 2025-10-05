#!/usr/bin/env python
"""
Database Initialization Script

This script initializes the LALO AI database with:
1. All required tables
2. Demo user for development/testing
3. Validates encryption keys

Usage:
    python scripts/init_db.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import Base, engine, SessionLocal, User
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger("lalo.scripts.init_db")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

def check_encryption_key():
    """Check if encryption key is set, generate if missing"""
    encryption_key = os.getenv("ENCRYPTION_KEY")

    if not encryption_key:
        logger.warning("ENCRYPTION_KEY not set in environment")
        logger.info("Generating a new key for this session...")
        logger.warning("WARNING: THIS KEY WILL NOT PERSIST - Add it to .env for production!")
        new_key = Fernet.generate_key().decode()
        logger.info("Add this to your .env file:")
        logger.info("ENCRYPTION_KEY=%s", new_key)
        os.environ["ENCRYPTION_KEY"] = new_key
        return False
    else:
        logger.info("[OK] ENCRYPTION_KEY is set")
        return True

def init_database():
    """Initialize database schema"""
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("[OK] All tables created successfully")
        return True
    except Exception as e:
        logger.exception("[ERROR] Error creating tables: %s", e)
        return False

def create_demo_user():
    """Create demo user for development"""
    logger.info("Creating demo user...")
    db = SessionLocal()

    try:
        # Check if demo user already exists
        demo_user = db.query(User).filter(User.email == "demo-user@example.com").first()

        if demo_user:
            logger.info("[INFO] Demo user already exists (demo-user@example.com)")
            return True

        # Create new demo user
        demo_user = User(
            id="demo-user-id",
            email="demo-user@example.com"
        )
        db.add(demo_user)
    db.commit()
    logger.info("[OK] Demo user created: demo-user@example.com")
        return True

    except Exception as e:
    logger.exception("[ERROR] Error creating demo user: %s", e)
        db.rollback()
        return False
    finally:
        db.close()

def verify_database():
    """Verify database is properly set up"""
    logger.info("Verifying database setup...")
    db = SessionLocal()

    try:
        # Check tables exist by querying
        user_count = db.query(User).count()
        logger.info("[OK] Database verified: %d user(s) found", user_count)
        return True
    except Exception as e:
        logger.exception("[ERROR] Database verification failed: %s", e)
        return False
    finally:
        db.close()

def main():
    """Main initialization function"""
    logger.info("%s", "=" * 60)
    logger.info("LALO AI - Database Initialization")
    logger.info("%s", "=" * 60)
    logger.info("")

    # Check encryption key
    encryption_key_exists = check_encryption_key()
    logger.info("")

    # Initialize database
    if not init_database():
        logger.error("Database initialization failed")
        sys.exit(1)
    logger.info("")

    # Create demo user
    if not create_demo_user():
        logger.error("Demo user creation failed")
        sys.exit(1)
    logger.info("")

    # Verify setup
    if not verify_database():
        logger.error("Database verification failed")
        sys.exit(1)
    logger.info("")

    logger.info("%s", "=" * 60)
    logger.info("[SUCCESS] Database initialization complete!")
    logger.info("%s", "=" * 60)
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. If ENCRYPTION_KEY was generated, add it to your .env file")
    logger.info("2. Start the application: python app.py")
    logger.info("3. Access http://localhost:8000 and login with demo token")
    logger.info("")

    if not encryption_key_exists:
        logger.warning("IMPORTANT: Don't forget to save the ENCRYPTION_KEY to .env!")
        logger.info("")

if __name__ == "__main__":
    main()
