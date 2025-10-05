#!/usr/bin/env python3
"""
Prepend a LALO provenance header to license files in ./licenses/ if not already present.
"""
import os
import re

OUT_DIR = os.path.join(os.getcwd(), "licenses")
HEADER = (
    "NOTICE: Collected and distributed by LALO AI SYSTEMS, LLC (2025).\n"
    "This file contains the original license text for the upstream project.\n"
    "The original copyright and license are preserved below and must not be altered.\n"
    "\n"
    "Included in distribution by: LALO AI SYSTEMS, LLC\n"
    "Inclusion year: 2025\n"
    "\n"
)


def should_skip(path):
    # skip README
    if os.path.basename(path).lower() == 'readme.md':
        return True
    return False


def already_has_header(text):
    return 'Included in distribution by: LALO AI SYSTEMS' in text or 'NOTICE: Collected and distributed by LALO AI SYSTEMS' in text


def process_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    if already_has_header(text):
        return False
    # Keep existing Source: lines if present after header - we will prepend our header
    new_text = HEADER + text
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_text)
    return True


def main():
    if not os.path.isdir(OUT_DIR):
        print('No licenses directory found.')
        return
    changed = []
    for fname in sorted(os.listdir(OUT_DIR)):
        path = os.path.join(OUT_DIR, fname)
        if not os.path.isfile(path):
            continue
        if should_skip(path):
            continue
        try:
            ok = process_file(path)
            if ok:
                changed.append(fname)
        except Exception as e:
            print('Error processing', fname, e)
    print('Updated files:', changed)

if __name__ == '__main__':
    main()
