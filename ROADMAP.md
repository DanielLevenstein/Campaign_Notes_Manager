# v1.3.0 Graph View Rewrite
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

## Phase 2 - Standardize Graph Design

### Phase 2.1 Projection And Presentation Layer
- [x] Established the first projection read model for combined graph rendering, including lore graph loading, source scanning, place source rows, derived lore relationships, character-sheet graph filtering, and root-node selection outside the Streamlit entry point.
- [x] Added projection tests that verify combined graph contracts, character-sheet filtering, graph loading through the projection layer, and guardrails that prevent `streamlit_app.py` from reintroducing direct graph assembly calls.
- [x] Introduced a render-ready presentation contract for relationship graph views and routed Party View through it as the first working end-to-end presentation-layer graph view.
- [x] Kept legacy Graphviz tab behavior in place for non-Party views while creating a stable vertical slice for the new architecture, so later work can migrate one view at a time instead of rewriting every tab at once.
- [x] Preserved tab-specific behavior for the current UI while narrowing the intended Phase 3 finish line to a single stable view backed by projection and presentation data.

### Phase 2.2 Graph Artifact
- [x] Add e2e test coverage for the directory and heading view.
- [x] Add artifact to valid graph-edge types.
- [x] Ensure that artifacts show up in test fixture e2e tests.

### Phase 2.3 Update Connection Types
- [x] Split compound connection types such as `Investigate Cult` into a target node named `Cult` and an `Investigate` edge.
- [x] Moved graph node and edge allow-lists into split config files under `config/nodes` and `config/edges`.
- [x] Derived lore edge values from the combined evidence block for the two connected nodes, while preserving configured and dominant relationship labels.
- [x] Fix bugs in node deduplication
- [x] Fix artifact edge direction bug

# Phase 3 - Standardize Graph Views
### Phase 3.1 – Decouple UI rendering from graph internals
- [x] Replace direct graph reads in graphviz_rendering.py and streamlit_app.py with projection API calls.
- [x] Make the UI consume projection results rather than infer behavior from internal node-type heuristics.
- [x] Unify the rendering behavior for Characters Graph, Places Graph, Session Notes Graph, and Full Structured Graph so they share the same layout and routing rules.

### Phase 3.2 Graph UI Improvements
- [x] Graphviz views must not change depending on what tab they are displayed under.
- [x] Views should take two parameters ("View Name", "Source File", "Heading Selected") Streamlit should handle code determining what files are present in dropdowns.
- [x] Streamlit should handle filtering based on files while graph projection should handle filtering based on heading. Only nodes from the selected source file should be sent to projection module.
- [x] In streamlit heading filters should be displayed as a separate dropdown from the "Source File" dropdown.

### Phase 3.3 Implement the tab parity work
- [x] Add the Characters Graph views with Single Character and Party View and preserve the three-column layout.
- [x] Add the Places Graph views with Location View and Heading View and support document/heading grouping.
- [x] Add the Session Notes Graph views with Location View and Directory File View and align them with the same projection behavior.
- [x] Implement the Full Structured Graph view with straight-line routing, stable columns, and the family-name trapezoid shape.


# v1.4.0 Context Aware Edges

1) A extraction model which extracts likely nodes. 
2) A classification model which can be used to determine node type based on the information in normalization.json
3) A second classification model which can be used to determine edge connection type when heading elements are removed from visible graphs. 

## Phase 0 Knowledge View Definition Migration
- [x] Create a design doc for knowledge view definition migration.
- [ ] Add typed dataclasses for knowledge view definitions.
- [ ] Add a config loader with inheritance and validation.
- [ ] Add app-facing config files for Location View and Session View.
- [ ] Migrate directory views to loaded definitions while keeping existing projection functions.
- [ ] Verify source-file filters, heading filters, hide-source controls, hide-heading controls, graph rendering, and connection tables.

## Phase 1.1 Context Aware Edges
- [x] Create a design doc for context-aware edges
- [ ] Move session-note derived relationships onto the occurrence model
- [ ] Persist occurrence metadata in canonical graph edges.
- [ ] Replace hidden-heading bridge creation with visible-anchor selection from occurrence metadata.

## Phase 1.2 Context Aware Node Type Detection
- [ ] Build classification labels from normalization.json.
- [ ] Add classifier-backed node type enrichment for existing nodes.
- [ ] Preserve deterministic node typing as override/fallback.
- [ ] Persist node classification metadata: predicted type, score, model, schema version, evidence.
- [ ] Promote classifier type only when confidence and test fixtures pass.

## Phase 1.3 Context Aware Edge Type Detection
- [ ] Derive candidate semantic edges from existing heading-mediated paths.
- [ ] Use evidence + heading context + node types to classify edge connection type.
- [ ] Persist semantic relation metadata separately from render-only helper edges.
- [ ] Use classified edge metadata when headings are hidden from visible graphs.

## Phase 1.4 GLiNER Node Extraction
- [ ] Add GLiNER extraction behind a feature flag.
- [ ] Compare GLiNER candidates against current non-heading extraction.
- [ ] Persist GLiNER confidence and evidence metadata.
- [ ] Replace current non-heading extraction only after fixture/e2e parity is proven.
- 
## Phase 2 Deduplication review workflow
- [ ] Add a Character Deduplication view that groups likely duplicate characters and supports canonical/alias decisions.
- [ ] Add a Place Deduplication view that groups likely duplicate places and supports canonical/alias decisions.
- [ ] Add a Node Removal view for low-confidence nodes that should be hidden from rendered graphs while preserving evidence.
- [ ] Store review decisions separately from generated graph JSON so they can be reapplied during regeneration.

## Phase 3 Creation of Stub Characters & Places & Artifacts
- [ ] Add UI for creating artifacts through the gui
- [ ] Update UI which can generate place character and artifact markdown files from evidence from the knowledge graph
- [ ] Create a UI checkbox so that autogenerated characters can be marked as major or minor characters with them defaulting to minor characters.

## Phase 4 Testing, migration, and rollout

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

### File Path Fixes
- [ ] Move all code under the character_graph directory into the new source directory using modules extract, ingest, and deduplication.
- [ ] Move the world_building folder out of source code. Let user choose the local directory they want to save their project files.
- [ ] Change the import test lore UI to a proper file picker which defaults to the test fixtures directory.
