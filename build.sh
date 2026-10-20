#!/usr/bin/env bash
# Baut dist/deckorator.ankiaddon für AnkiWeb aus addon/.
# Vor jedem Update: VERSION in addon/__init__.py erhöhen und CHANGELOG.md ergänzen.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/dist"
cd "$ROOT/addon"
rm -rf __pycache__
python -I - "$ROOT/dist/deckorator.ankiaddon" <<'PY'
import sys, zipfile
files = ["__init__.py", "theme.py", "dialog.py", "preview.py", "ui.py", "desktop.py", "system.py", "log.py",
         "config.json", "config.md", "user_files/README.txt", "assets/chevron-light.svg", "assets/chevron-dark.svg"]
with zipfile.ZipFile(sys.argv[1], "w", zipfile.ZIP_DEFLATED) as z:
    for f in files:
        z.write(f)
print(f"{sys.argv[1]}: {len(files)} Dateien")
PY
grep -o 'VERSION = "[^"]*"' __init__.py
