#!/usr/bin/env bash
# Builds dist/deckorator.ankiaddon for AnkiWeb from addon/.
# Before each release: bump VERSION in addon/__init__.py and update CHANGELOG.md.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/dist"
cd "$ROOT/addon"
rm -rf __pycache__
python -I - "$ROOT/dist/deckorator.ankiaddon" <<'PY'
import sys, zipfile
import glob
# all source files automatically; never personal settings (meta.json) or images from user_files
files = sorted(glob.glob("*.py") + glob.glob("assets/*") + glob.glob("wallpapers/*")) + ["config.json", "config.md", "user_files/README.txt"]
with zipfile.ZipFile(sys.argv[1], "w", zipfile.ZIP_DEFLATED) as z:
    for f in files:
        z.write(f)
print(f"{sys.argv[1]}: {len(files)} Dateien")
PY
grep -o 'VERSION = "[^"]*"' __init__.py
