# TODO

## Knowledge Graph Implementation Roadmap
This roadmap is based on the architecture in docs/design/KNOWLEDGE_GRAPH_DESIGN4.md and the review workflow in docs/design/NODE_DEDUPLICATION_DESIGN.md.

## Phase 0 — Persistence Layer
- [x] Ensure all IO operations are handled through a single persistence module
- [x] Ensure that any time a Markdown file is saved or updated, the persisted version of the graph edges is also updated.

## Phase 1 – Establish a canonical graph layer
- [x] Implement a canonical graph service as the single source of truth for nodes, edges, and metadata.
- [x] Add canonicalization and adapter logic so legacy node types and session-note metadata can be mapped into the new model.
- [x] Normalize source-file paths with a deterministic helper, so file and heading projections use consistent identifiers.
- [x] Add persistence for canonical graph data with a lightweight embedded store and support for versioned updates.
- [x] And an update to a md file should trigger an update to the corresponding graph data file.
- [x] All interactions with the graph database should go through the new persistence layer.
- [x] Synthetic edges should not be stored to the persisted graph structure.

### Phase 1.1 Character Improvements
- [x] Show the following name fields on the character creation UI [Character Name, Player Name, Aliases]
- [x] Make First Name and Family Name derived metadata fields.
- [x] Add a content-driven Aliases field to the metadata, which is not user-editable. 

### Phase 1.2 Performance Improvements
- [x] Add file hashes persistence layer so that if no changes are made to markdown file no graph updates are done. 
- [x] And folder level hash code to back up lore files so that the app doesn't create backups when no changes were made. 

### Phase 2.1 Projection And Presentation Layer
- [x] Established the first projection read model for combined graph rendering, including lore graph loading, source scanning, place source rows, derived lore relationships, character-sheet graph filtering, and root-node selection outside the Streamlit entry point.
- [x] Added projection tests that verify combined graph contracts, character-sheet filtering, graph loading through the projection layer, and guardrails that prevent `streamlit_app.py` from reintroducing direct graph assembly calls.
- [x] Introduced a render-ready presentation contract for relationship graph views and routed Party View through it as the first working end-to-end presentation-layer graph view.
- [x] Kept legacy Graphviz tab behavior in place for non-Party views while creating a stable vertical slice for the new architecture, so later work can migrate one view at a time instead of rewriting every tab at once.
- [x] Preserved tab-specific behavior for the current UI while narrowing the intended Phase 3 finish line to a single stable view backed by projection and presentation data.

## Phase 3.1 – Decouple UI rendering from graph internals
- [x] Replace direct graph reads in graphviz_rendering.py and streamlit_app.py with projection API calls.
- [ ] Make the UI consume projection results rather than infer behavior from internal node-type heuristics.
- [ ] Unify the rendering behavior for Characters Graph, Places Graph, Session Notes Graph, and Full Structured Graph so they share the same layout and routing rules.
- [ ] Preserve the tab-specific view semantics while moving the common logic into a shared rendering pipeline.

### Phase 3.2 Graph UI Improvements
- [ ] Graphviz views must not change depending on what tab they are displayed under.
- [ ] Views should take two parameters ("View Name", "Source File", "Heading Selected") Streamlit should handle code determining what files are present in dropdowns.
- [ ] Streamlit should handle filtering based on files while graph projection should handle filtering based on heading. Only nodes from the selected source file should be sent to projection module.
- [ ] In streamlit heading filters should be displayed as a separate dropdown from the "Source File" dropdown.

## Phase 4 – Implement the tab parity work
- [ ] Add the Characters Graph views with Single Character and Party View and preserve the three-column layout.
- [ ] Add the Places Graph views with Location View and Heading View and support document/heading grouping.
- [ ] Add the Session Notes Graph views with Location View and Directory File View and align them with the same projection behavior.
- [ ] Implement the Full Structured Graph view with straight-line routing, stable columns, and the family-name trapezoid shape.

## Phase 5 – Add the deduplication review workflow
- [ ] Add a Character Deduplication view that groups likely duplicate characters and supports canonical/alias decisions.
- [ ] Add a Place Deduplication view that groups likely duplicate places and supports canonical/alias decisions.
- [ ] Add a Node Removal view for low-confidence nodes that should be hidden from rendered graphs while preserving evidence.
- [ ] Store review decisions separately from generated graph JSON so they can be reapplied during regeneration.

## Phase 6 – Testing, migration, and rollout
- [ ] Add unit tests for canonicalization adapters, projection results, and review-rule application.
- [ ] Add integration tests covering ingestion -> canonical store -> projection -> UI rendering for session-note imports.
- [ ] Add UI contract tests and a small e2e flow for deduplication and graph rendering.
- [ ] Roll out the new projection path behind a feature flag and migrate legacy graph data gradually.

# Descoped 
## Projection API and Event Flow 
- [ ] Add projection helpers for file lists, file headings, and file/heading-based subgraphs.
- [ ] Ensure projections can answer view requests without relying on fragile node-type string checks.
- [ ] Introduce an event-driven update path so graph ingestion can notify the UI when new files or projections are available.
- [ ] Add projection versioning or etags so the UI can cache results safely and refresh only when needed.
