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

load_dotenv()

def check_encryption_key():
    """Check if encryption key is set, generate if missing"""
    encryption_key = os.getenv("ENCRYPTION_KEY")

    if not encryption_key:
        print("WARNING: ENCRYPTION_KEY not set in environment")
        print("   Generating a new key for this session...")
        print("   WARNING: THIS KEY WILL NOT PERSIST - Add it to .env for production!")
        new_key = Fernet.generate_key().decode()
        print(f"\n   Add this to your .env file:")
        print(f"   ENCRYPTION_KEY={new_key}\n")
        os.environ["ENCRYPTION_KEY"] = new_key
        return False
    else:
        print("[OK] ENCRYPTION_KEY is set")
        return True

def init_database():
    """Initialize database schema"""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] All tables created successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
        return False

def create_demo_user():
    """Create demo user for development"""
    print("Creating demo user...")
    db = SessionLocal()

    try:
        # Check if demo user already exists
        demo_user = db.query(User).filter(User.email == "demo-user@example.com").first()

        if demo_user:
            print("[INFO] Demo user already exists (demo-user@example.com)")
            return True

        # Create new demo user
        demo_user = User(
            id="demo-user-id",
            email="demo-user@example.com"
        )
        db.add(demo_user)
        db.commit()
        print("[OK] Demo user created: demo-user@example.com")
        return True

    except Exception as e:
        print(f"[ERROR] Error creating demo user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def verify_database():
    """Verify database is properly set up"""
    print("Verifying database setup...")
    db = SessionLocal()

    try:
        # Check tables exist by querying
        user_count = db.query(User).count()
        print(f"[OK] Database verified: {user_count} user(s) found")
        return True
    except Exception as e:
        print(f"[ERROR] Database verification failed: {e}")
        return False
    finally:
        db.close()

def main():
    """Main initialization function"""
    print("="* 60)
    print("LALO AI - Database Initialization")
    print("="* 60)
    print()

    # Check encryption key
    encryption_key_exists = check_encryption_key()
    print()

    # Initialize database
    if not init_database():
        print("\n[FAILED] Database initialization failed")
        sys.exit(1)
    print()

    # Create demo user
    if not create_demo_user():
        print("\n[FAILED] Demo user creation failed")
        sys.exit(1)
    print()

    # Verify setup
    if not verify_database():
        print("\n[FAILED] Database verification failed")
        sys.exit(1)
    print()

    print("="* 60)
    print("[SUCCESS] Database initialization complete!")
    print("="* 60)
    print()
    print("Next steps:")
    print("1. If ENCRYPTION_KEY was generated, add it to your .env file")
    print("2. Start the application: python app.py")
    print("3. Access http://localhost:8000 and login with demo token")
    print()

    if not encryption_key_exists:
        print("IMPORTANT: Don't forget to save the ENCRYPTION_KEY to .env!")
        print()

if __name__ == "__main__":
    main()
