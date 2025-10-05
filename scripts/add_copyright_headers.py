#!/usr/bin/env python3
"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

Script to add copyright headers to all source files.
"""

import os
from pathlib import Path

COPYRIGHT_PYTHON = '''"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

'''

COPYRIGHT_TYPESCRIPT = '''/*
 * Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
 *
 * PROPRIETARY AND CONFIDENTIAL
 *
 * This file is part of LALO AI Platform and is protected by copyright law.
 * Unauthorized copying, modification, distribution, or use of this software,
 * via any medium, is strictly prohibited without the express written permission
 * of LALO AI SYSTEMS, LLC.
 */

'''

COPYRIGHT_JAVASCRIPT = COPYRIGHT_TYPESCRIPT  # Same format

# Simplified copyright for config files
COPYRIGHT_JSON_COMMENT = '''# Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
# This file is proprietary and confidential.

'''

# Generic headers for other formats
COPYRIGHT_HASH = '''# Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This file is part of LALO AI Platform and is protected by copyright law.
# Unauthorized copying, modification, distribution, or use of this software,
# via any medium, is strictly prohibited without the express written permission
# of LALO AI SYSTEMS, LLC.
#

'''

COPYRIGHT_HTML = '''<!--
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
-->

'''

COPYRIGHT_XML = COPYRIGHT_HTML

def has_copyright(content: str) -> bool:
    """Check if file already has copyright notice."""
    return "LALO AI SYSTEMS, LLC" in content or "Copyright (c) 2025" in content

def add_python_copyright(file_path: Path):
    """Add copyright to Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if has_copyright(content):
        print(f"  [SKIP] {file_path} - already has copyright")
        return False

    # Handle shebang
    if content.startswith('#!'):
        lines = content.split('\n', 1)
        new_content = lines[0] + '\n' + COPYRIGHT_PYTHON + (lines[1] if len(lines) > 1 else '')
    else:
        new_content = COPYRIGHT_PYTHON + content

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  [ADD] {file_path}")
    return True

def add_typescript_copyright(file_path: Path):
    """Add copyright to TypeScript/JavaScript file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if has_copyright(content):
        print(f"  [SKIP] {file_path} - already has copyright")
        return False

    new_content = COPYRIGHT_TYPESCRIPT + content

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  [ADD] {file_path}")
    return True

def process_directory(directory: Path, extensions: list, handler):
    """Process all files with given extensions in directory."""
    count = 0
    for ext in extensions:
        for file_path in directory.rglob(f"*{ext}"):
            # Skip certain directories
            skip_dirs = ['node_modules', 'venv', '__pycache__', 'dist', 'build', '.git', 'models']
            if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                continue

            # Skip test files and migrations for now (can add later)
            if 'test_' in file_path.name or 'migration' in file_path.name:
                continue

            try:
                if handler(file_path):
                    count += 1
            except Exception as e:
                print(f"  [ERROR] {file_path}: {e}")

    return count


def is_binary_file(file_path: Path) -> bool:
    """Try to detect binary files by reading a small chunk and checking for null bytes."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\x00' in chunk:
                return True
            # Heuristic: if many non-text bytes, consider binary
            text_chars = b"\n\r\t\b\f" + bytes(range(32, 127))
            nontext = sum(1 for c in chunk if c not in text_chars)
            if len(chunk) == 0:
                return False
            if nontext / len(chunk) > 0.3:
                return True
            return False
    except Exception:
        return True


def choose_header_for_extension(ext: str) -> str:
    """Return appropriate header text for a given file extension."""
    if ext in {'.py', '.sh', '.ps1'}:
        return COPYRIGHT_PYTHON
    if ext in {'.ts', '.tsx', '.js', '.jsx'}:
        return COPYRIGHT_TYPESCRIPT
    if ext in {'.css', '.scss'}:
        return COPYRIGHT_TYPESCRIPT
    if ext in {'.md', '.rst', '.txt'}:
        return COPYRIGHT_HASH
    if ext in {'.html', '.htm'}:
        return COPYRIGHT_HTML
    if ext in {'.xml'}:
        return COPYRIGHT_XML
    if ext in {'.yml', '.yaml', '.ini', '.cfg', '.toml'}:
        return COPYRIGHT_HASH
    # Default to hash-style
    return COPYRIGHT_HASH


def process_all_sources(root: Path):
    """Walk the tree and add headers to all textual source files, skipping JSON and binaries."""
    skip_dirs = {'node_modules', 'venv', '__pycache__', 'dist', 'build', '.git', 'models'}
    updated = 0
    for file_path in root.rglob('*'):
        if file_path.is_dir():
            continue
        if any(part in skip_dirs for part in file_path.parts):
            continue

        # Skip certain file types that must not have headers
        if file_path.suffix.lower() == '.json':
            continue

        # Skip binary files
        if is_binary_file(file_path):
            continue

        # Skip migrations (name based)
        if 'migration' in file_path.name.lower():
            continue

        # Read content and decide
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue

        if has_copyright(content):
            # already covered
            continue

        ext = file_path.suffix.lower()
        header = choose_header_for_extension(ext)

        # Special case: handle shebang for scripts
        if content.startswith('#!') and ext in {'.py', '.sh'}:
            lines = content.split('\n', 1)
            new_content = lines[0] + '\n' + header + (lines[1] if len(lines) > 1 else '')
        else:
            new_content = header + content

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  [ADD] {file_path}")
            updated += 1
        except Exception as e:
            print(f"  [ERROR] writing {file_path}: {e}")

    return updated

def main():
    """Main execution."""
    print("="*80)
    print("Adding Copyright Headers to LALO AI Platform")
    print("="*80)
    print()

    root_dir = Path(__file__).parent.parent
    print("Processing all source files (textual) and skipping JSON/binaries...")
    updated = process_all_sources(root_dir)

    print("="*80)
    print(f"Total files updated: {updated}")
    print("="*80)

if __name__ == "__main__":
    main()
