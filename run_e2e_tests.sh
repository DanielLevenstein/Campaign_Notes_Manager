#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ "$#" -eq 0 ]; then
    set -- tests/e2e
fi

PYTHONPATH=. .venv/bin/python -m pytest -q --maxfail=1 "$@"
