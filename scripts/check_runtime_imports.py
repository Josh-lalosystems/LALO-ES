"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import importlib
import sys
import traceback

mods = [
    'core.services.agent_runtime',
    'core.services.workflow_state',
    'core.routes.agent_routes',
]

def main():
    for m in mods:
        try:
            importlib.import_module(m)
            print(f'Imported {m} OK')
        except Exception:
            print(f'FAILED to import {m}')
            traceback.print_exc()
            sys.exit(1)
    print('All imports OK')

if __name__ == '__main__':
    main()
