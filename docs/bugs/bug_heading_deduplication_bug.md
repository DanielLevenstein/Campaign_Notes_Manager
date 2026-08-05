# Duplicate Heading Node Bug

## Reproduction Scenario

- Import `complex_session_graph.md`
- In the Session Notes -> Location view, the "Session 4" node shows up four times in the graph.

## Expected Behavior:

- The "Session 4" nodes should all be deduplicated into one.

This same bug also hapens on the Session Notes/Directory tab with element "Family Tree".

## Screenshots

- [Session Notes Duplicate Header Bug](docs/bugs/screenshots/session_notes_duplicate_header_bug.png)
- [Session Notes Graph Directory File View](tests/fixtures/screenshots/buggy/Session_Notes_Graph_Directory_File_View.png)
