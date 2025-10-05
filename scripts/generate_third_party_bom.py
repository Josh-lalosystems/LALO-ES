#!/usr/bin/env python3
"""
Generate a third-party dependency inventory (THIRD_PARTY_DEPENDENCIES.md)
Scans requirements.txt and requirements-ml.txt, queries PyPI for metadata,
and writes a markdown table with Package, Requirement line, Latest PyPI version,
License, and Home page.

Run from repo root: python scripts/generate_third_party_bom.py
"""
import json
import os
import re
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

REQ_FILES = ["requirements.txt", "requirements-ml.txt"]
OUTPUT = "THIRD_PARTY_DEPENDENCIES.md"


def parse_requirements(path):
    pkgs = []
    if not os.path.exists(path):
        return pkgs
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Remove inline comments
            line = re.sub(r"\s+#.*$", "", line)
            spec = line
            # Remove extras like pkg[extra]
            name = re.sub(r"\[.*?\]", "", spec)
            # Extract name before any version specifier
            name = re.split(r"[><=~!\\]", name)[0].strip()
            if name:
                pkgs.append((name, spec))
    return pkgs


def query_pypi(pkg):
    url = f"https://pypi.org/pypi/{pkg}/json"
    req = Request(url, headers={"User-Agent": "LALO-BOM-Scanner/1.0"})
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.load(resp)
            info = data.get("info", {})
            license_field = info.get("license") or ""
            classifiers = info.get("classifiers") or []
            if not license_field:
                license_field = "; ".join([c for c in classifiers if 'License' in c])
            homepage = info.get("home_page") or ""
            if not homepage:
                urls = info.get("project_urls") or {}
                homepage = urls.get("Homepage") or urls.get("home") or urls.get("Home") or ""
            version = info.get("version") or ""
            return {"version": version, "license": license_field, "home": homepage}
    except HTTPError as e:
        return {"version": "HTTP %s" % e.code, "license": "UNKNOWN", "home": ""}
    except URLError as e:
        return {"version": "URLERR", "license": "UNKNOWN", "home": ""}
    except Exception:
        return {"version": "ERROR", "license": "UNKNOWN", "home": ""}


def main():
    repo_root = os.getcwd()
    all_pkgs = {}
    for f in REQ_FILES:
        path = os.path.join(repo_root, f)
        pkgs = parse_requirements(path)
        for name, spec in pkgs:
            if name not in all_pkgs:
                all_pkgs[name] = {"specs": [], "meta": None}
            all_pkgs[name]["specs"].append(spec)

    results = []
    for name in sorted(all_pkgs.keys(), key=str.lower):
        print(f"Querying PyPI for {name}...", flush=True)
        meta = query_pypi(name)
        all_pkgs[name]["meta"] = meta
        results.append((name, all_pkgs[name]["specs"], meta))

    md_lines = []
    md_lines.append("# Third-party dependency inventory")
    md_lines.append("")
    md_lines.append("Generated: {}".format(__import__('datetime').datetime.utcnow().isoformat() + 'Z'))
    md_lines.append("")
    md_lines.append("This file lists packages referenced in requirements files and the license information as reported by PyPI. Verify each license text before redistribution or bundling.")
    md_lines.append("")
    md_lines.append("| Package | Requirement lines | Latest PyPI version | License | Home page |")
    md_lines.append("|---|---|---:|---|---|")

    for name, specs, meta in results:
        spec_text = "<br>".join(specs)
        version = meta.get("version", "")
        license_field = meta.get("license", "") or "UNKNOWN"
        home = meta.get("home", "") or ""
        md_lines.append(f"| {name} | {spec_text} | {version} | {license_field} | {home} |")

    out_path = os.path.join(repo_root, OUTPUT)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"Wrote {out_path}")


if __name__ == '__main__':
    main()
