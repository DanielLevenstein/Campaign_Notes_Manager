# Bugs Found

- Fix Session Notes import "Add Session Notes To Use File View."

Import Testing Lore calls `import_lore_directory(source_dir: Path, overwrite: bool = True)` in `lore_import.py`
Add Session Notes calls `render_session_import_heading_dialog` in `streamlit_app.py`

in lore_source_file_options If I remove `node.node_type != "source_document"` custom session notes show up in the dropdown again but when the option is selected an error saying no session notes connections were found.


# Testing

- Get unit tests passing before implementing new changes.
- I see that the test texture directory has a directory called "graph_views"; These helper files don't seem to be generated in the full app.
- Added new test fixture for session notes `session_notes_graph_lore_import.json`
- No test uses the fixtures under graph_views, so I can't wire it into an existing test.

## Current Behavior

- Session Notes metadata is only stored when imported through the "Import Testing Lore" workflow
- Session Notes metadata is currently being saved to `world_building/meta_data/character_graph/session_note__Session_Notes.graph.json`
- In `world_building/meta_data/character_graph/session_note__Session_Notes.graph.json` character named "Session Notes" is a case of mistaken identity.
  - "Session Notes" should be saved as a document heading, not a character.
- In graphviz_rendering.py `is_session_note_node` and , `is_place_lore_path` are determining a node type by string values in file names rather than absolute directory paths. 
