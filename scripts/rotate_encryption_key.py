"""
Utility to inspect and rotate ENCRYPTION_KEY for secrets stored in the DB.

Usage:
  # Dry-run: list rows that fail to decrypt with current ENCRYPTION_KEY
  python scripts/rotate_encryption_key.py --list-bad

  # Export encrypted rows to a JSON backup before rotating
  python scripts/rotate_encryption_key.py --export-backup backup.json

  # Rotate keys: provide OLD and NEW keys; this will attempt to decrypt with OLD and re-encrypt with NEW
  python scripts/rotate_encryption_key.py --rotate --old-key <old> --new-key <new> --backup backup.json

This script is intentionally conservative: it never mutates the DB unless --rotate is specified and a backup file is provided.
"""

import argparse
import json
import os
from cryptography.fernet import Fernet, InvalidToken
from datetime import datetime

# Import SQLAlchemy table access similar to secrets_manager
from core.services.secrets_manager import SecretsManager
from core.database import SessionLocal


def list_bad_rows():
    sm = SecretsManager()
    session = SessionLocal()
    try:
        rows = session.execute(sm._table.select()).fetchall()
        bad = []
        for r in rows:
            try:
                # Attempt decryption with current environment key via SecretsManager._decrypt
                val = sm._decrypt(r.value_encrypted)
                if val is None:
                    bad.append({
                        'id': r.id,
                        'name': r.name,
                        'user_id': r.user_id,
                        'version': r.version,
                        'created_at': str(r.created_at),
                        'updated_at': str(r.updated_at),
                    })
            except Exception as e:
                bad.append({'id': r.id, 'error': str(e)})
        return bad
    finally:
        session.close()


def export_backup(path: str):
    sm = SecretsManager()
    session = SessionLocal()
    try:
        rows = session.execute(sm._table.select()).fetchall()
        out = []
        for r in rows:
            out.append({
                'id': r.id,
                'name': r.name,
                'user_id': r.user_id,
                'value_encrypted': r.value_encrypted,
                'version': r.version,
                'created_at': str(r.created_at),
                'updated_at': str(r.updated_at),
            })
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'exported_at': datetime.utcnow().isoformat()+'Z', 'rows': out}, f, indent=2)
        return path
    finally:
        session.close()


def rotate_keys(old_key: str, new_key: str, backup_path: str = None):
    # Validate keys
    old_fernet = Fernet(old_key.encode() if isinstance(old_key, str) else old_key)
    new_fernet = Fernet(new_key.encode() if isinstance(new_key, str) else new_key)

    sm = SecretsManager()
    session = SessionLocal()
    try:
        rows = session.execute(sm._table.select()).fetchall()
        rotated = []
        for r in rows:
            try:
                plaintext = old_fernet.decrypt(r.value_encrypted.encode()).decode()
            except InvalidToken:
                continue  # skip rows that don't decrypt with old key
            # Re-encrypt with new key
            new_enc = new_fernet.encrypt(plaintext.encode()).decode()
            # Update row
            session.execute(
                sm._table.update().where(sm._table.c.id == r.id).values(value_encrypted=new_enc, updated_at=datetime.utcnow())
            )
            rotated.append(r.id)
        session.commit()
        return rotated
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list-bad', action='store_true', help='List rows that fail to decrypt with current ENCRYPTION_KEY')
    parser.add_argument('--export-backup', type=str, help='Export encrypted rows to a JSON backup file')
    parser.add_argument('--rotate', action='store_true', help='Rotate keys from OLD to NEW (requires --old-key and --new-key)')
    parser.add_argument('--old-key', type=str, help='Old ENCRYPTION_KEY (base64 Fernet key)')
    parser.add_argument('--new-key', type=str, help='New ENCRYPTION_KEY (base64 Fernet key)')
    parser.add_argument('--delete-bad', action='store_true', help='Export backup and delete rows that fail to decrypt with current key')

    args = parser.parse_args()

    if args.list_bad:
        bad = list_bad_rows()
        print(f"Found {len(bad)} bad rows (failed to decrypt with current ENCRYPTION_KEY):")
        for b in bad:
            print(json.dumps(b))
        return

    if args.export_backup:
        path = export_backup(args.export_backup)
        print(f"Exported backup to {path}")
        return

    if args.delete_bad:
        # Must provide a backup path for safety
        if not args.export_backup:
            print("--delete-bad requires --export-backup to be specified for safety")
            return
        print(f"Exporting backup to {args.export_backup} before deleting bad rows...")
        export_backup(args.export_backup)
        bad = list_bad_rows()
        if not bad:
            print("No bad rows found; nothing to delete.")
            return
        print(f"Deleting {len(bad)} bad rows: {[b['id'] for b in bad]}")
        sm = SecretsManager()
        session = SessionLocal()
        try:
            for b in bad:
                session.execute(sm._table.delete().where(sm._table.c.id == b['id']))
            session.commit()
            print("Deleted bad rows successfully. Keep the backup file safe.")
        finally:
            session.close()
        return

    if args.rotate:
        if not args.old_key or not args.new_key or not args.export_backup:
            print("--rotate requires --old-key, --new-key and --export-backup for safety")
            return
        # Create backup first
        export_backup(args.export_backup)
        rotated = rotate_keys(args.old_key, args.new_key, args.export_backup)
        print(f"Rotated {len(rotated)} rows. IDs: {rotated}")
        return

    parser.print_help()


if __name__ == '__main__':
    main()
