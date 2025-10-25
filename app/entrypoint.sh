#!/usr/bin/env bash
set -euo pipefail
: "${MEDIA_DIR:=/data/media}"
: "${SITE_DIR:=/app/site}"
python /app/build_gallery.py
exec gunicorn --bind 0.0.0.0:8080 server:app
