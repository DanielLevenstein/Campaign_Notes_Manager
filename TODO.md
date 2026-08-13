# TODO
- [ ] Backlog the hierarchical knowledge view definition migration described in `docs/design/KNOWLEDGE_VIEW_DEFINITION_MIGRATION.md`.
- [ ] Rename the graph schema root from `primary_character` to a type-neutral primary node after node-type normalization is stable, and migrate validation, persistence, projections, fixtures, and generated `.graph.json` files to the new field.
- [ ] Move constants out of session_entities.py
## Pre-Context-Aware Edge Bug Fixes
- [x] Confirm `bug_session_note_upload_e2e_flaky_staged_file.md` remains resolved and mirror that status in the known-bugs roadmap.
- [x] Fix `node_type_bugs.md` by typing place-like session-note names such as `Moon Gate` as places before projection.
- [x] Fix `bug_groups_in_character_column.md` by suppressing duplicate character candidates for canonical group names such as `Indigo Cult`.
- [ ] Verify `bug_location_view_heading_levels_lost.md` with fresh Location View screenshot evidence; unit coverage already proves heading-level column precedence.
- [ ] Defer `bug_group_connection_context_transfer.md` until context-aware edge occurrences are implemented.
