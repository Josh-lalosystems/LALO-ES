#!/usr/bin/env python3
"""
Second-pass fetch for missing license texts for specific packages.
Tries PyPI project URLs, common GitHub repo patterns, and a small fallback mapping.

Run from repo root: python scripts/fetch_missing_licenses.py
"""
import json
import os
import re
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

MISSING = ["fastapi", "intuit-oauth", "PyJWT", "pytest", "python-multipart"]
OUT_DIR = os.path.join(os.getcwd(), "licenses")

FALLBACK_GITHUB = {
    "fastapi": "tiangolo/fastapi",
    "intuit-oauth": "intuit/oauth-pythonclient",
    "PyJWT": "jpadilla/pyjwt",
    "pytest": "pytest-dev/pytest",
    "python-multipart": "Kludex/python-multipart",
}

COMMON_LICENSE_NAMES = ["LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING", "NOTICE"]


def query_pypi(pkg):
    url = f"https://pypi.org/pypi/{pkg}/json"
    req = Request(url, headers={"User-Agent": "LALO-License-Collector/1.0"})
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.load(resp)
            return data.get('info', {})
    except Exception as e:
        return {"error": str(e)}


def try_fetch(url):
    req = Request(url, headers={"User-Agent": "LALO-License-Collector/1.0"})
    try:
        with urlopen(req, timeout=15) as resp:
            content = resp.read()
            if len(content) > 200 * 1024:
                return None
            return content.decode('utf-8', errors='replace')
    except Exception:
        return None


def github_raw_urls(owner_repo):
    urls = []
    branches = ['main', 'master', 'develop']
    for br in branches:
        for name in COMMON_LICENSE_NAMES:
            urls.append(f"https://raw.githubusercontent.com/{owner_repo}/{br}/{name}")
    return urls


def write_license(name, text, source):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    path = os.path.join(OUT_DIR, f"{safe}-LICENSE.txt")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"Source: {source}\n\n")
        f.write(text)
    print(f"Wrote {path}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    summary = {"updated": [], "still_missing": []}
    for pkg in MISSING:
        print(f"Second-pass: {pkg}")
        info = query_pypi(pkg)
        candidates = []
        if isinstance(info, dict):
            home = info.get('home_page') or ''
            proj_urls = info.get('project_urls') or {}
            if proj_urls:
                for v in proj_urls.values():
                    if v:
                        candidates.append(v)
            if home:
                candidates.append(home)
        # Add fallback github path if present
        if pkg in FALLBACK_GITHUB:
            candidates.append(f"https://github.com/{FALLBACK_GITHUB[pkg]}")
        found = False
        tried = []
        # Try direct candidate URLs for GitHub raw
        for c in candidates:
            tried.append(c)
            gh_match = re.search(r"github\.com[:/]+([^/]+)/([^/]+)", c)
            if gh_match:
                owner_repo = f"{gh_match.group(1)}/{gh_match.group(2).rstrip('.git')}"
                for url in github_raw_urls(owner_repo):
                    text = try_fetch(url)
                    if text:
                        write_license(pkg, text, url)
                        summary['updated'].append(pkg)
                        found = True
                        break
            if found:
                break
        if found:
            continue
        # Try to fetch license from PyPI project's description page (simple heuristic)
        pypi_license_candidate = f"https://pypi.org/project/{pkg}/#license"
        tried.append(pypi_license_candidate)
        # As last resort, try fallback_github raw directly
        if pkg in FALLBACK_GITHUB:
            for url in github_raw_urls(FALLBACK_GITHUB[pkg]):
                text = try_fetch(url)
                if text:
                    write_license(pkg, text, url)
                    summary['updated'].append(pkg)
                    found = True
                    break
        if not found:
            # Write a placeholder note (append to existing placeholder)
            safe = re.sub(r"[^A-Za-z0-9_.-]", "_", pkg)
            path = os.path.join(OUT_DIR, f"{safe}-LICENSE.txt")
            with open(path, 'a', encoding='utf-8') as f:
                f.write("\n# SECOND PASS: License text not found automatically. Tried sources:\n")
                for t in tried:
                    f.write(f"# - {t}\n")
            summary['still_missing'].append(pkg)
    # Create README
    readme = os.path.join(OUT_DIR, 'README.md')
    with open(readme, 'w', encoding='utf-8') as f:
        f.write('# licenses/ README\n\n')
        f.write('This folder contains license texts collected for third-party packages referenced by the project.\n\n')
        f.write('Automated collection performed; verify each file before redistribution.\n\n')
        if summary['updated']:
            f.write('## Updated in second pass\n')
            for u in summary['updated']:
                f.write(f'- {u}\n')
            f.write('\n')
        if summary['still_missing']:
            f.write('## Still missing / needs manual retrieval\n')
            for m in summary['still_missing']:
                f.write(f'- {m}\n')
            f.write('\n')
        f.write('If a license file is missing, visit the package project page (PyPI or GitHub) and copy the license text into a file named <package>-LICENSE.txt.\n')
    print('\nSecond-pass summary:')
    print('Updated:', summary['updated'])
    print('Still missing:', summary['still_missing'])

if __name__ == '__main__':
    main()
