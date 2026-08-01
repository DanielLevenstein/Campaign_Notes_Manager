# Testing
- Get unit tests passing before implementing new changes.
- I see that the test texture directory has a directory called "graph_views"; These helper files don't seem to be generated in the full app.
- Added new test fixture for session notes `session_notes_graph_lore_import.json`
- No test uses the fixtures under graph_views, so I can't wire it into an existing test.

##  Change log
The changelog has been moved to the bottom of CHANGELOG.md
Create a changelog for CHANGELOG.md summarizing previous work. Then delete these entities from the TODO file. 

Use the following Markdown levels
H1 Branch 
H2 Date
H3 Feature Implementation

## Observations
- in lore_source_file_options If I remove `node.node_type != "source_document"` custom session notes show up in the dropdown again but when the option is selected an error saying no session notes connections were found.
- Session Notes metadata is only stored when imported through the "Import Testing Lore" workflow
- Session Notes metadata is currently being saved to `world_building/meta_data/character_graoh/session_note__Session_Notes.graph.json`
- In `world_building/meta_data/character_graoh/session_note__Session_Notes.graph.json` character named "Session Notes" is a case of mistaken identity. 
  - "Session Notes" should be saved as a document heading, not a character.

## Current Behavior

- Session Notes metadata is only stored when imported through the "Import Testing Lore" workflow
- Session Notes metadata is currently being saved to `world_building/meta_data/character_graph/session_note__Session_Notes.graph.json`
- In `world_building/meta_data/character_graph/session_note__Session_Notes.graph.json` character named "Session Notes" is a case of mistaken identity.
  - "Session Notes" should be saved as a document heading, not a character.
- In graphviz_rendering.py `is_session_note_node` and , `is_place_lore_path` are determining a node type by string values in file names rather than absolute directory paths. 
