#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PYTHONPATH=. .venv/bin/python -m pytest -q tests/unit "$@"
