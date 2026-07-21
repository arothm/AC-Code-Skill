#!/usr/bin/env python3
"""Build ac-code-skill.skill deterministically and correctly.

The .skill file is a zip of skills/ac-code-skill/. Building it by hand (or with
PowerShell Compress-Archive on Windows) produced two validator failures: Windows
BACKSLASH path separators in the archive, and shipped __pycache__/*.pyc. This
builds it right — forward-slash arcnames, junk excluded — so desktop/Cowork
uploads validate without repackaging.

    python build.py            # writes ac-code-skill.skill
    python build.py --check    # verify an existing bundle, don't rebuild
"""
from __future__ import annotations
import os, sys, zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "skills", "ac-code-skill")
OUT = os.path.join(ROOT, "ac-code-skill.skill")
EXCLUDE_DIRS = {"__pycache__", ".git", ".pytest_cache", ".mypy_cache", "node_modules"}
EXCLUDE_EXT = {".pyc", ".pyo", ".pyd"}
EXCLUDE_NAMES = {".DS_Store", "Thumbs.db"}


def wanted(path):
    parts = path.replace("\\", "/").split("/")
    if any(p in EXCLUDE_DIRS for p in parts):
        return False
    name = parts[-1]
    if name in EXCLUDE_NAMES or os.path.splitext(name)[1] in EXCLUDE_EXT:
        return False
    return True


def files():
    for dirpath, dirnames, filenames in os.walk(SRC):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for f in filenames:
            full = os.path.join(dirpath, f)
            if wanted(full):
                yield full


def build():
    if os.path.exists(OUT):
        os.remove(OUT)
    n = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for full in sorted(files()):
            # arcname: forward slashes, rooted at the skill folder name
            rel = os.path.relpath(full, os.path.join(ROOT, "skills")).replace(os.sep, "/")
            z.write(full, rel)
            n += 1
    print(f"wrote {os.path.relpath(OUT, ROOT)} — {n} files, {os.path.getsize(OUT):,} bytes")
    return 0


def check(path=OUT):
    if not os.path.exists(path):
        print(f"no bundle at {path}")
        return 1
    problems = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if "\\" in name:
                problems.append(f"backslash path: {name}")
            if "__pycache__" in name or name.endswith((".pyc", ".pyo")):
                problems.append(f"python bytecode shipped: {name}")
            if name.rsplit("/", 1)[-1] in EXCLUDE_NAMES:
                problems.append(f"OS cruft shipped: {name}")
        count = len(z.namelist())
    if problems:
        print(f"{path}: {len(problems)} PROBLEM(S)")
        for p in problems:
            print("  " + p)
        return 1
    print(f"{path}: OK — {count} entries, forward-slash paths, no bytecode/cruft")
    return 0


if __name__ == "__main__":
    sys.exit(check() if "--check" in sys.argv[1:] else (build() or check()))
