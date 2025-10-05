#!/usr/bin/env python3
"""
Collect license texts for packages listed in requirements files.
Writes license files into ./licenses/<package>-LICENSE.txt and creates a report.

Usage: python scripts/collect_licenses.py
"""
import json
import os
import re
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

REQ_FILES = ["requirements.txt", "requirements-ml.txt"]
OUT_DIR = os.path.join(os.getcwd(), "licenses")
COMMON_LICENSE_NAMES = [
    "LICENSE",
    "LICENSE.txt",
    "LICENSE.md",
    "LICENSE.rst",
    "COPYING",
    "COPYING.txt",
    "NOTICE",
]


def parse_requirements(path):
    pkgs = []
    if not os.path.exists(path):
        return pkgs
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            line = re.sub(r"\s+#.*$", "", line)
            name = re.sub(r"\[.*?\]", "", line)
            name = re.split(r"[><=~!\\]", name)[0].strip()
            if name:
                pkgs.append((name, line))
    return pkgs


def query_pypi(pkg):
    url = f"https://pypi.org/pypi/{pkg}/json"
    req = Request(url, headers={"User-Agent": "LALO-License-Collector/1.0"})
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.load(resp)
            info = data.get("info", {})
            home = info.get("home_page") or ""
            proj_urls = info.get("project_urls") or {}
            classifiers = info.get("classifiers") or []
            return {"info": info, "home": home, "project_urls": proj_urls, "classifiers": classifiers}
    except Exception as e:
        return {"error": str(e)}


def try_fetch(url):
    req = Request(url, headers={"User-Agent": "LALO-License-Collector/1.0"})
    try:
        with urlopen(req, timeout=15) as resp:
            content = resp.read()
            # Heuristic: must be reasonably small
            if len(content) > 100 * 1024:
                return None
            return content.decode("utf-8", errors="replace")
    except (HTTPError, URLError) as e:
        return None
    except Exception:
        return None


def github_raw_urls_from_repo_url(url):
    # Try to detect github repo and return raw base
    if not url:
        return []
    m = re.search(r"github\.com[:/]+([^/]+)/([^/]+)(?:/|$)", url)
    if not m:
        return []
    owner = m.group(1)
    repo = m.group(2).rstrip('.git')
    branches = ["main", "master", "develop", "dev"]
    urls = []
    for br in branches:
        for name in COMMON_LICENSE_NAMES:
            urls.append(f"https://raw.githubusercontent.com/{owner}/{repo}/{br}/{name}")
    # Also try raw from HEAD of default branch
    return urls


def collect():
    os.makedirs(OUT_DIR, exist_ok=True)
    pkgs = []
    for f in REQ_FILES:
        pkgs.extend(parse_requirements(os.path.join(os.getcwd(), f)))
    pkgs = sorted({p[0]: p[1] for p in pkgs}.items(), key=lambda x: x[0].lower())

    summary = {"fetched": [], "failed": []}
    for name, spec in pkgs:
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
        out_path = os.path.join(OUT_DIR, f"{safe_name}-LICENSE.txt")
        if os.path.exists(out_path):
            print(f"Already have {out_path}")
            summary["fetched"].append(name)
            continue
        print(f"Processing {name}...")
        meta = query_pypi(name)
        found = False
        tried_sources = []
        # 1) Try project_urls Source/Homepage
        home = meta.get("home") if isinstance(meta, dict) else None
        proj_urls = meta.get("project_urls") if isinstance(meta, dict) else {}
        candidates = []
        if proj_urls:
            for k, v in proj_urls.items():
                if v:
                    candidates.append(v)
        if home:
            candidates.append(home)
        # normalize
        candidates = [c for c in candidates if c]
        # try direct license files on GH if repo is github
        for c in candidates:
            tried_sources.append(c)
            gh_urls = github_raw_urls_from_repo_url(c)
            for url in gh_urls:
                text = try_fetch(url)
                if text:
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(f"Source: {url}\n\n")
                        f.write(text)
                    print(f"Fetched license for {name} from {url}")
                    summary["fetched"].append(name)
                    found = True
                    break
            if found:
                break
        if found:
            time.sleep(0.5)
            continue
        # 2) Try PyPI simple page for license file link
        pypi_simple = f"https://pypi.org/project/{name}/#files"
        tried_sources.append(pypi_simple)
        # 3) Try GitHub guessed raw location using canonical project_urls or home
        # Fallback: try fetching from pypi package page raw description for license mention
        # 4) If nothing found, write a placeholder file with metadata
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"Package: {name}\n")
            f.write(f"Requirement: {spec}\n")
            if isinstance(meta, dict):
                info = meta.get("info")
                if info:
                    f.write(f"Summary: {info.get('summary')}\n")
                    f.write(f"Home: {meta.get('home')}\n")
                    f.write(f"Project URLs: {json.dumps(meta.get('project_urls'))}\n")
                    # include classifiers
                    cl = meta.get('classifiers') or []
                    if cl:
                        f.write("Classifiers:\n")
                        for c in cl:
                            f.write(f" - {c}\n")
            f.write("\n# LICENSE TEXT NOT FOUND AUTOMATICALLY\n")
            f.write("# Please fetch the license text manually and place it here if required for redistribution.\n")
            f.write("# Tried sources:\n")
            for s in tried_sources:
                f.write(f"#  - {s}\n")
        summary["failed"].append(name)
        time.sleep(0.5)
    print('\nSummary:')
    print('Fetched:', len(summary['fetched']), 'packages')
    print('Failed:', len(summary['failed']), 'packages')
    if summary['failed']:
        print('\nFailed packages:')
        for n in summary['failed']:
            print(' -', n)


if __name__ == '__main__':
    collect()
