# Bugs Found
- [ ] Header and file filters got lost in graphviz refactoring. 
- [ ] Fix bugs in node deduplication
- [ ] Fix the artifact edge direction bug

Identify other potential bugs from Phase 2.3 code changes. 

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
- Implemented Phase 2.1 Projection And Presentation Layer 
- Implemented Phase 2.2 Added Artifact connection type
- Started PHASE 2.3 Update Connection Types