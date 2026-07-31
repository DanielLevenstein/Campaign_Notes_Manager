# Bugs Found
- Get unit tests passing before implementing new changes.
- Fix Session Notes import "Add Session Notes To Use File View."

Import Testing Lore calls `import_lore_directory(source_dir: Path, overwrite: bool = True)` in `lore_import.py`
Add Session Notes calls `render_session_import_heading_dialog` in `streamlit_app.py`

# Testing
- Get unit tests passing before implementing new changes.

## Completed - Full Structured Graph Restore - 2026-07-20 - feature/knowledge_graph2
- Removed root level nodes on from places view in the knowledge graph
- Removed all references to the full knowledge graph from code as the title had become misleading
- Removed Location view from session notes tab
