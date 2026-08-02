# TODO

## Phase 2-3 Remaining Work

- Move file-list, heading-list, and file/heading subgraph helpers out of `graphviz_rendering.py` and behind projection APIs.
- Make graph UI controls consume projection option objects instead of inspecting `node_type`, `source_file`, and Markdown heading IDs directly.
- Add projection versioning or etags so Streamlit can cache graph views and refresh only when source graph data changes.
- Add an event/update flow so graph regeneration can notify the UI when files, headings, or projections change.
- Migrate one additional graph view through the presentation layer after Party View, preferably a file/heading view that exercises source and heading selection.
- Keep legacy Graphviz rendering available until the migrated view has parity tests and a stable screenshot or contract test.

## Graph View Improvements

- Ensure Graphviz views do not change behavior based on which top-level tab they are displayed under.
- Standardize graph view inputs as `View Name`, `Source File`, and `Heading Selected`.
- Keep source-file filtering in Streamlit/projection option selection and heading filtering in the graph projection layer.
- Display heading filters as a separate dropdown from source-file filters.
- Preserve Characters, Places, Session Notes, and Full Structured Graph semantics while moving common rendering through one shared presentation pipeline.

## Graph Parity For Later Release

- Add the Characters Graph views with Single Character and Party View and preserve the three-column layout.
- Add the Places Graph views with Location View and Heading View and support document/heading grouping.
- Add the Session Notes Graph views with Location View and Directory File View and align them with the same projection behavior.
- Implement the Full Structured Graph view with straight-line routing, stable columns, and the family-name trapezoid shape.

## Review Workflow For Later Release

- Add a Character Deduplication view that groups likely duplicate characters and supports canonical/alias decisions.
- Add a Place Deduplication view that groups likely duplicate places and supports canonical/alias decisions.
- Add a Node Removal view for low-confidence nodes that should be hidden from rendered graphs while preserving evidence.
- Store review decisions separately from generated graph JSON so they can be reapplied during regeneration.

## Testing And Rollout

- Add integration tests covering ingestion -> canonical store -> projection -> UI rendering for session-note imports.
- Add UI contract tests and a small e2e flow for deduplication and graph rendering.
- Add screenshot or DOM-level coverage for the first presentation-layer graph view.
- Roll out the new projection path behind a feature flag if later view migrations need staged release control.

## Completed

- Implemented Phase 1.1 character name metadata improvements with `Character Name`, `Player Name`, read-only aliases, derived first/family names, and content-driven alias metadata.
- Implemented Phase 1.2 persistence hashing so unchanged Markdown skips graph regeneration and unchanged lore folders skip automatic latest-backup rewrites.
