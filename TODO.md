# Change log

The changelog has been moved to the bottom of CHANGELOG.md
Create a changelog for CHANGELOG.md summarizing previous work. Then delete these entities from the TODO file.

Use the following Markdown levels
H1 Branch
H2 Date
H3 Feature Implementation

## Knowledge Graph bugs

- Session Notes show up as a character in the Session_Notes.md directory view.
- ![Session Note Character](docs/screenshots/session_note_character.png)
  - I believe this is because the session notes import is using the same character ingestion function as the character sheet one.
  - This node should be converted from a character type to a header type

## Document View Improvement

- An extra option should be added to the heading selector to view all elements in the file. Relevant for "Session_Notes_Fixture.md" file which has multiple h1 headings.
- UI buttons should be added to the Directory view to hide elements headings H1 - H3 with a checkbox for each item we support hiding. 
- When heading elements are hidden, new graph connections should be created from the hidden node to all its children with h1-h3 being the initial connection label.

![Directory View Busy](docs/screenshots/Session_Notes_Busy.png)
**In the figure above "Tharevon" is connected to the "Pixi Kingdom" through "Session 4" but in current ui it's almost impossible to see**


## Graph View Improvements

- Graphviz views must not change depending on what tab they are displayed under.
- Views should take two parameters ("View Name", "Source File", "Heading Selected") Streamlit should handle code determining what files are present in dropdowns.
- Streamlit should handle filtering based on files while graph projection should handle filtering based on heading. Only nodes from the selected source file should be sent to projection module.
- In streamlit heading filters should be displayed as a separate dropdown from the "Source File" dropdown.

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
