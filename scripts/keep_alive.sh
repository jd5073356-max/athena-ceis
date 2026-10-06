#!/usr/bin/env bash
# Athena Keep-Alive Runner
set -e
CDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$CDIR"
source .venv/bin/activate
export DB_ENGINE=postgres
python scripts/keep_alive.py >> "$CDIR/scripts/keep_alive.log" 2>&1
