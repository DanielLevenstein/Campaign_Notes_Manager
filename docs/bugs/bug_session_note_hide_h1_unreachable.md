# Session Note H1 Hide Heading Control Is Unreachable

## Status
Resolved

## Summary
The session note editor can hide a heading only when the selected markdown section is level 1, but the session note dropdown intentionally skips H1 headings. As a result, the UI path for hiding an H1 heading is not reachable through the current selection workflow.

## Evidence
- `session_note_select_options` skips `section.level == 1` entries.
- The session note edit form renders `Hide Heading` only when `selected_section.level == 1`; otherwise section actions render as delete/remove controls.
- The previous e2e test for hiding an H1 heading could not select the H1 option and is now skipped until the workflow is redesigned.

## Expected Decision
Decide whether H1 headings should be selectable for this action, whether Hide Heading should support lower-level headings, or whether the hide-heading feature should be removed from this screen.

## Decision
The hide-heading feature was removed from the session-note editor surface. H1 headings remain intentionally absent from the session-note dropdown, and selectable H2/H3 sections now expose delete/remove actions only.

## Test Evidence
- `tests/e2e/test_session_notes_ui.py::test_ui_does_not_expose_unreachable_hide_heading_action`
