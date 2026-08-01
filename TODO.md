# Bugs Found
- Get unit tests passing before implementing new changes.
- Fix Session Notes import "Add Session Notes To Use File View."

Import Testing Lore calls `import_lore_directory(source_dir: Path, overwrite: bool = True)` in `lore_import.py`
Add Session Notes calls `render_session_import_heading_dialog` in `streamlit_app.py`


## Observations
- in lore_source_file_options If I remove `node.node_type != "source_document"` custom session notes show up in the dropdown again but when the option is selected an error saying no session notes connections were found.
- Session Notes metadata is only stored when imported through the "Import Testing Lore" workflow
- Session Notes metadata is currently being saved to `world_building/meta_data/character_graoh/session_note__Session_Notes.graph.json`
- In `world_building/meta_data/character_graoh/session_note__Session_Notes.graph.json` character named "Session Notes" is a case of mistaken identity. 
  - "Session Notes" should be saved as a document heading, not a character.

##  Change log
The changelog has been moved to the bottom of CHANGELOG.md
Create a changelog for CHANGELOG.md summarizing previous work. Then delete these entities from the TODO file. 

Use the following Markdown levels
H1 Branch 
H2 Date
H3 Feature Implementation
- Short description of what was changed. 
