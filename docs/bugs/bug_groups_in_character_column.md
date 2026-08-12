# Groups Displayed in Character Column

## Status
Resolved

## Steps to reproduce
- Import complex_session_graph.md
- Navigate to Session Notes/Directory View
- Indigo Cult is showing up as both a group and person with identical text.

## Expected Result
- Indigo Cult should show up as a single node of a type group, and any identified members of it should show up as character connections. 

## Screenshots

This screenshot showcases the duplication issue where Indigo Cult is represented both as a group and an individual.

- [Groups Displayed in Characters Column](docs/bugs/screenshots/Indigo_cult_duplication.png)

## Fix Summary
Session-note entity extraction now lets explicit group-pattern extraction win before generic capitalized-phrase extraction. When a phrase such as `Indigo Cult` is already canonicalized as a group, the extractor no longer emits a duplicate character candidate for the same canonical key.

## Test Evidence
- `tests/unit/graph/test_combined_character_graph.py::test_session_note_entity_extraction_keeps_cult_names_out_of_character_candidates`
- `tests/unit/graph/test_context_aware_edges.py::test_group_mentions_do_not_create_duplicate_character_nodes_for_the_same_name`
- `tests/unit/rendering/test_graphviz_rendering.py::test_session_note_group_heading_and_entity_are_not_rendered_as_duplicate_nodes`
