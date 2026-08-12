# Bug Fix ROADMAP

This roadmap covers every bug currently documented in `docs/bugs`. The order is intentional: stabilize tests and UI decisions first, then fix canonical node typing and deduplication before changing heading-context routing and Graphviz layout.

## Bug Inventory

- [x] `docs/bugs/bug_session_note_upload_e2e_flaky_staged_file.md` - session-note upload e2e can lose the staged file.
- [x] `docs/bugs/bug_session_note_hide_h1_unreachable.md` - H1 hide-heading action cannot be reached from the session-note editor.
- [x] `docs/bugs/node_type_bugs.md` - `Moon Gate` is inferred as a character instead of a place.
- [x] `docs/bugs/bug_groups_in_character_column.md` - `Indigo Cult` renders as both a group and a character.
- [ ] `docs/bugs/bug_group_connection_context_transfer.md` - groups lose correct visible heading context when headings are hidden.

## Test Harness And Baseline Evidence

- [x] Move session-note upload source files for e2e tests outside watched lore/session-note directories.
- [x] Add a dedicated unwatched temporary upload fixture path for session-note upload tests.
- [x] Remove or simplify retry/reload workarounds once file staging is deterministic.
- [ ] Keep `test_ui_creates_loads_and_undoes_character_changes` active as the regression for the resolved character undo bug.
- [ ] Capture fresh baseline screenshots only after the upload test harness is stable.

### Acceptance Criteria

- Full `tests/e2e/test_session_notes_ui.py` runs without intermittent `Choose A Markdown Or Text File Before Uploading.` failures.
- Character undo e2e continues to prove the visible editor textbox refreshes after undo.

## Resolve Session Note Editor H1 Decision

- [x] Decide the product behavior for `Hide Heading` in the session-note editor:
  - H1 headings selectable for hide actions, or
  - hide-heading applies to H2/H3 sections too, or
  - hide-heading is removed from this editor surface.
- [x] Update `session_note_select_options` and the section action UI to match the decision.
- [x] Unskip or replace the skipped H1 hide-heading e2e test.
- [x] Document the selected behavior in the relevant design/spec notes if it affects searchable heading workflow.

### Acceptance Criteria

- No unreachable `Hide Heading` UI path remains.
- The session-note editor e2e covers the chosen heading-hide behavior.

## Canonical Node Type And Identity Fixes

- [x] Add fixture-backed unit tests proving `Moon Gate` is a place before projection.
- [x] Review node type inference for place-like names extracted from session notes.
- [x] Ensure `Indigo Cult` is canonicalized as one group node, not a duplicate character plus group.
- [x] Add regression coverage showing group members render as character connections, while the group remains in the group column.
- [x] Confirm canonical identity decisions happen before projection, layout, and deduplication.

### Acceptance Criteria

- `Moon Gate` appears as a place in session-note and location graph projections.
- `Indigo Cult` appears once as a group, with member/related characters connected separately.

### Test Evidence

- `tests/unit/graph/test_combined_character_graph.py::test_session_note_entity_extraction_keeps_cult_names_out_of_character_candidates`
- `tests/unit/graph/test_combined_character_graph.py::test_session_note_entity_extraction_treats_gate_names_as_places`
- `tests/unit/graph/test_context_aware_edges.py::test_moon_gate_is_typed_as_a_place_before_projection`
- `tests/unit/graph/test_context_aware_edges.py::test_group_mentions_do_not_create_duplicate_character_nodes_for_the_same_name`
- `tests/unit/graph/test_node_normalization.py`
- `tests/unit/rendering/test_graphviz_rendering.py::test_session_note_group_heading_and_entity_are_not_rendered_as_duplicate_nodes`

## Heading And Source Deduplication

- [x] Add projection tests for duplicate `Session 4` and `Family Tree` heading nodes.
- [x] Normalize heading IDs from source document, line, level, and compact heading text consistently across place and session-note projections.
- [x] Merge semantic Markdown headings with matching canonical entities without creating competing visible nodes.
- [x] Ensure source-document roots and same-label H1 headings deduplicate predictably.
- [x] Re-run screenshot coverage for `session_notes_duplicate_header_bug.png` scenarios.

### Acceptance Criteria

- [x] `Session 4` renders once in Session Notes Location/Session View.
- [x] `Family Tree` renders once in Session Notes directory-style views.
- [x] Empty or unassociated duplicate headings are pruned without losing evidence rows.

### Test Evidence

- `tests/unit/rendering/test_graphviz_rendering.py::test_session_note_lore_graph_uses_headings_groups_characters_and_places`
- `tests/unit/rendering/test_graphviz_rendering.py::test_session_note_directory_projection_deduplicates_family_tree_h1_from_extracted_entities`
- `tests/unit/rendering/test_graphviz_rendering.py::test_duplicate_source_document_nodes_are_collapsed_in_rendered_lore_graph`
- `tests/e2e/test_session_notes_ui.py::test_ui_removes_duplicate_headings_on_session_notes_load`

## Hidden Heading Context Routing

- [ ] Introduce or emulate the source-backed occurrence model described in `bug_group_connection_context_transfer.md`.
- [ ] Track source document, source file, evidence line, nearest H1/H2/H3 stack, semantic target id, and target type for each extracted relationship occurrence.
- [ ] Apply visibility rules from occurrence context instead of bridging hidden source/heading nodes opportunistically.
- [ ] Make generic source-document labels lose to more specific heading labels when both describe the same evidence path.
- [ ] Add regressions for group evidence under multiple visible months.

### Acceptance Criteria

- With file name hidden and lower session headings hidden, `Ignis Cult` or `Indigo Cult` remains connected to each visible month heading that contains evidence.
- No stale generic `Session Notes` edge connects group nodes directly to characters when a specific heading context exists.
- Hiding all heading levels still preserves useful group-to-character/place context edges.

## Location View Heading-Level Layout

- [ ] Add a graph projection test proving place nodes retain the heading level where they appeared in `Atlantia_Lore.md`.
- [ ] Fix Location View projection so place heading entities carry their original Markdown heading level into rendering.
- [ ] Update Graphviz column assignment so H1/H2/H3-derived place nodes remain split across the intended columns.
- [ ] Regenerate or compare against the `place_column_collapse` and `Places_Graph_Location_View` screenshot scenarios.

### Acceptance Criteria

- Place icons in Location View are split by original source heading level.
- `Atlantia_Lore.md` no longer collapses all place nodes into one column.

## Cross-Bug Regression Pass

- [ ] Run targeted unit tests for graph projection, node typing, deduplication, and edge direction.
- [ ] Run targeted e2e tests for session-note upload, session-note editor heading actions, and knowledge graph views.
- [ ] Regenerate screenshot artifacts only after the behavior is confirmed stable.
- [ ] Update `CHANGELOG.md` with the completed bug-fix phases.
- [ ] Mark each resolved `docs/bugs/*.md` file with status, fix summary, and test evidence.

### Suggested Verification Commands

- [ ] `.venv/bin/python -m pytest tests/unit/rendering/test_graphviz_rendering.py -q`
- [ ] `.venv/bin/python -m pytest tests/unit/graph -q`
- [ ] `.venv/bin/python -m pytest tests/e2e/test_session_notes_ui.py -q`
- [ ] `.venv/bin/python -m pytest tests/e2e/test_character_sheet_roundtrip_ui.py -q`
