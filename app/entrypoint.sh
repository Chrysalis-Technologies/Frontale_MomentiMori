#!/usr/bin/env bash
set -euo pipefail
: "${MEDIA_DIR:=/data/media}"
: "${SITE_DIR:=/app/site}"
python /app/build_gallery.py
exec python -m http.server 8080 -d "$SITE_DIR"