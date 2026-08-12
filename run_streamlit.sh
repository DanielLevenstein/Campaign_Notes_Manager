#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
USE_STRUCTURED_GRAPH_FIXTURE=0

if [[ "${1:-}" == "--structured-graph-fixture" ]]; then
  USE_STRUCTURED_GRAPH_FIXTURE=1
  shift
fi

cd "$SCRIPT_DIR"

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return
  fi
  echo "Could not find python3 or python on PATH." >&2
  exit 1
}

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  PYTHON_BIN="$(find_python)"
  echo "Creating virtual environment in $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

VENV_PYTHON="$VENV_DIR/bin/python"
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r requirements.txt

if [[ "$USE_STRUCTURED_GRAPH_FIXTURE" == "1" ]]; then
  FIXTURE_WORLD_BUILDING_DIR="$SCRIPT_DIR/.tmp/structured_graph_fixture/world_building"
  FIXTURE_LORE_DIR="$FIXTURE_WORLD_BUILDING_DIR/lore"
  rm -rf "$FIXTURE_WORLD_BUILDING_DIR"
  mkdir -p "$FIXTURE_LORE_DIR/character_sheets" "$FIXTURE_LORE_DIR/places" "$FIXTURE_LORE_DIR/session_notes"
  cp "$SCRIPT_DIR"/tests/fixtures/character_sheets/*.md "$FIXTURE_LORE_DIR/character_sheets/"

  export LOCAL_CHATBOT_WORLD_BUILDING_DIR="$FIXTURE_WORLD_BUILDING_DIR"
  export LOCAL_CHATBOT_LORE_DIR="$FIXTURE_LORE_DIR"
  export LOCAL_CHATBOT_CHARACTERS_DIR="$FIXTURE_LORE_DIR/character_sheets"
  export LOCAL_CHATBOT_PLACES_DIR="$FIXTURE_LORE_DIR/places"
  export LOCAL_CHATBOT_SESSION_NOTES_DIR="$FIXTURE_LORE_DIR/session_notes"
  export LOCAL_CHATBOT_META_DATA_DIR="$FIXTURE_WORLD_BUILDING_DIR/meta_data"
  export LOCAL_CHATBOT_KNOWLEDGE_GRAPH_SOURCE_LABEL="Screenshot Fixture"
fi

echo "Starting Streamlit app..."
exec "$VENV_PYTHON" -m streamlit run streamlit_app.py "$@"
