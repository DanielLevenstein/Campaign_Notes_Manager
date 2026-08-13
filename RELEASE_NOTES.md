# Release Notes

| Version | Summary                                                                                    |
|---------|--------------------------------------------------------------------------------------------|
| v1.3.0 | Route all graph views through single configurable code pathway                             |
| v1.2.0  | Add local character rewrite tuning, rewrite quality reports, summary and backstory rewrite |
| v1.1.1  | Enable knowledge graph feature and partial code cleanup                                    |
| v1.1.0  | Implemented distinct knowledge graph views for character, place and session tab            |
| v1.0.0  | This release adds a dedicated Knowledge Graph UI using graphviz.                           |
| v0.1.0  | Packaged as a Streamlit app for local character sheets, campaign lore management.          |

## v1.3.0 - Graph View Rewrite

## Phase 0 — Persistence Layer
- Ensure all IO operations are handled through a single persistence module
- Ensure that any time a Markdown file is saved or updated, the persisted version of the graph edges is also updated.

## Phase 1 – Establish a canonical graph layer
- Implement a canonical graph service as the single source of truth for nodes, edges, and metadata.
- Add canonicalization and adapter logic so legacy node types and session-note metadata can be mapped into the new model.
- Normalize source-file paths with a deterministic helper, so file and heading projections use consistent identifiers.
- Add persistence for canonical graph data with a lightweight embedded store and support for versioned updates.
- And an update to a md file should trigger an update to the corresponding graph data file.
- All interactions with the graph database should go through the new persistence layer.
- Synthetic edges should not be stored to the persisted graph structure.

## Phase 2 - Standardize Graph Design

### Phase 2.1 Projection And Presentation Layer
- Established the first projection-read model for combined graph rendering, including lore graph loading, source scanning, place source rows, derived lore relationships, character-sheet graph filtering, and root-node selection outside the Streamlit entry point.
- Added projection tests that verify combined graph contracts, character-sheet filtering, graph loading through the projection layer, and guardrails that prevent `streamlit_app.py` from reintroducing direct graph assembly calls.
- Introduced a render-ready presentation contract for relationship graph views and routed Party View through it as the first working end-to-end presentation-layer graph view.
- Kept legacy Graphviz tab behavior in place for non-Party views while creating a stable vertical slice for the new architecture, so later work can migrate one view at a time instead of rewriting every tab at once.
- Preserved tab-specific behavior for the current UI while narrowing the intended Phase 3 finish line to a single stable view backed by projection and presentation data.

### Phase 2.3 Update Connection Types
- Split compound connection types such as `Investigate Cult` into a target node named `Cult` and an `Investigate` edge.
- Moved graph node and edge allowlists into split config files under `config/nodes` and `config/edges`.
- Derived lore-edge values from the combined evidence block for the two connected nodes, while preserving configured and dominant relationship labels.

# Phase 3 Standardize Graph Views
### Phase 3.1 – Decouple UI rendering from graph internals
- Make the UI consume projection results rather than infer behavior from internal node-type heuristics.
- Unify the rendering behavior for Characters Graph, Places Graph, Session Notes Graph, and Full Structured Graph so they share the same layout and routing rules.

### Phase 3.2 Graph UI Improvements
- Graphviz views must not change depending on what tab they are displayed under.
- Views should take two parameters ("View Name", "Source File", "Heading Selected") Streamlit should handle code determining what files are present in dropdowns.
- Streamlit should handle filtering based on files while graph projection should handle filtering based on heading. Only nodes from the selected source file should be sent to projection module.
- In streamlit heading filters should be displayed as a separate dropdown from the "Source File" dropdown.

### Phase 3.3 Implement the tab parity work
- Add the Character Graph views with Single Character and Party View and preserve the three-column layout.
- Add the Place Graph views with Location View and Heading View and support document/heading grouping.
- Add the Session Notes Graph views with Location View and Directory File View and align them with the same projection behavior.
- Implement the Full Structured Graph view with straight-line routing, stable columns, and the family-name trapezoid shape.

## v1.2.0 - Character Rewrite Tuning

This release focuses on the local character rewrite workflow: generated graph-backed summaries and backstories, measured rewrite quality, and safe promotion of accepted generated text into character Markdown.
The selected rewrite model is `qwen2.5-0.5b-instruct-q4_k_m`.

### Highlights

- Switched character rewrites to the local `llama` CLI model path with deterministic graph rewrites kept as the fallback path.
- Added graph-backed summary and backstory rewrite controls in the character editor, with reviewable generated text after save and rerun.
- Added normalized quality reports for single-character and multi-character summary and backstory evaluation.
- Added sentence-structure charting for the single-character rewrite flow, including sentence category distributions and KDE overlays.
- Tuned the rewrite path around the smaller Qwen 0.5B local model candidate and removed retry-loop behavior so model tuning can focus on the output itself.
- Fixed `Replace Original` so accepted generated summary and backstory text is promoted into the main Markdown and stale generated/original markers are removed.

### Quality

- Added focused Streamlit e2e coverage for character rewrite controls and generated text review.
- Added model-level contract tests for summary and backstory rewrite behavior.
- Added regression coverage for accepting generated character sections and preserving promoted text in Markdown and profile metadata.
- Regenerated the single-character and multi-character rewrite reports during the tuning pass.

## v1.1.1
Enabled knowledge graph in UI without an env variable
Removed the hidden full graph view from code as the name is no longer accurate. 
Plan to consolidate views across all main tabs for a future release. 

## Knowledge Graph Views
Main Tab [Characters, Places, Session Notes]
- Characters: [Character View, Party View]
- Places: [Party View, Location View, Heading View, Directory File View]
- Session Notes: [Party View, Location View, Directory File View]

## v1.1.0 - Knowledge Graph Views

In this release separate knowledge graph tabs were added for every main level tab for the app. 
Places and Groups were given dedicated icons and given priority placement in the graph.

## Knowledge Graph Views
Main Tab [Characters, Places, Session Notes]
- Characters: [Single Character, Party View]
- Places: [Location View, Heading View]
- Session Notes: [Location View, Directory File View]

Detailed design notes are located below:
- [Knowledge Graph Views](docs/specs/KNOWLEDGE_GRAPH_DESIGN4.md): Multi View Knowledge Graphs

## v1.0.0 - Knowledge Graph Tab

This release adds a dedicated Knowledge Graph tab (v1.0.0) that surfaces combined graph data from characters, places, and session notes directly in the Streamlit UI.

Supported Views:
**Character View**, **Party View**

### Knowledge Graph Columns 
Column 0: Family Names
Column 1: Main Characters
Column 2: Secondary Characters & places

### Highlights

- Added Knowledge Graph tab `v1.0.0` with an interactive graph view and node/edge detail panels.
- Combined character/place/session knowledge graph aggregation and normalization.
- Export graph as JSON and Graphviz-compatible formats for downstream tooling.
- Evidence links in node/edge panels point back to source markdown files.
- Stable UI selectors added to support Playwright end-to-end tests.

### Notes

- Design docs: see [docs/specs](docs/specs) for graph and UI specifications.
- Backwards-compatible: generated graph JSON continues to be stored under `world_building/meta_data`.

## v0.1.0 - First Local Release

This first release packages the local roleplaying character creator as a Streamlit app for managing private campaign lore on disk. The app treats markdown files in `world_building/lore` as the source of truth, stages raw imports under `world_building/import`, keeps runtime metadata under `world_building/meta_data`, and provides UI workflows for characters, places, session notes, and derived knowledge graphs.

### Highlights

- Import session notes from raw text or markdown file.
- Extract the knowledge graph from the character backstory.
- Suggest wording updates for character summary and backstory to improve writing legibility. 

### Lore Storage

- Authored campaign files live under `world_building/lore`, which git ignores so private campaign material stays local.
- Raw import files are staged under `world_building/import`.
- Generated characters are written to `world_building/lore/character_sheets` when the player saves them.
- Runtime profile metadata, memory notes, chat logs, and generated graph JSON live under `world_building/meta_data`.
- Character sheets can include a `Character Connections` table using either `Table/Item/Value/Evidence` or `Source/Relationship/Name/Evidence` columns.

### Model And Graph Notes

- Removed bundled external model configuration from the release path.
- Added semantic rewrite design notes and a semantic improvement report for the current graph-backed rewrite engine.
- Normalized generated graph/UI values so underscores and legacy `Autogenerated` markers do not leak into normal display names.

### Upcoming Features
- Combined knowledge graph which identifies connections between characters and places from different data sources.
- Knowledge graphs for session note and place entities.

### Quality

- Added unit coverage for character parsing, graph extraction, graph storage, rewrite behavior, place creation, `Character Connections` import/export, and deletion cleanup.
- Added end-to-end Streamlit coverage for creating, loading, undoing, and deleting characters, places, and session notes.
- Added end-to-end coverage for failed-create validation preserving entered fields.
- Added coverage for creating a character from the gated combined knowledge graph workflow.
