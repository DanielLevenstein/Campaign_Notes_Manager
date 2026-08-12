
# feature/knowledge_graph3

## Context-Aware Edge Design
- Added failing graph-creation tests for context-aware edge occurrence metadata, direct co-mentioned entity edges, group context preservation under hidden headings, `Moon Gate` place typing, and `Indigo Cult` group deduplication.
- Added `docs/design/DESIGN_CONTEXT_AWARE_EDGES.md` to define the occurrence model, direct context edge derivation, projection behavior, implementation plan, and acceptance criteria for fixing heading-dependent graph edges.
- Fixed the pre-context-aware session-note extraction bugs for `Moon Gate` place typing and `Indigo Cult` group/character duplication, updated TODO/bug-roadmap tracking, and documented test evidence in the resolved bug notes.
- Moved session-note entity normalization constants, regex patterns, extraction limits, and typo maps out of `session_entities.py` and into `config/extraction/normalization.json`.

## Phase 0
- Added the Phase 0 persistence layer for mirrored graph metadata paths, centralized Markdown/JSON/bytes file writes, and graph serialization that excludes synthetic edges.
- Routed character, place, and session-note Markdown save/delete flows through the persistence helpers so lore edits update the corresponding graph JSON.
## Phase 1
- Implemented skipped Phase 1.1 and 1.2 work: character forms now use `Character Name`, `Player Name`, and read-only alias metadata; first/family names are derived; graph regeneration is skipped for unchanged Markdown hashes; and automatic lore backups no-op when the lore folder hash is unchanged.
- Copied the persistence module into the new `src/persistence` source root with matching `tests/persistence` coverage for mirrored paths, file helpers, deletes, and synthetic-edge filtering.
- Added `run_unit_tests.sh` and `run_e2e_tests.sh` wrappers for the top-level unit and e2e suites.
- Renamed the legacy `language_model.storage` domain module to `language_model.lore_documents`, removed the duplicate `character_graph.storage` module, and documented the path toward one canonical persistence implementation.
- Added the initial Phase 1 canonical graph layer with typed node/edge models, legacy combined-graph adapters, deterministic source-file normalization, and a lightweight SQLite-backed graph service with versioned upserts.
- Added a raw initial graph debug snapshot under character metadata so generated edges can be compared against the production persisted graph and inspected as native or derived.
- Routed Streamlit undo writes and graph-view loading through the persistence read model so UI changes update mirrored graph metadata and graph rendering reads persisted metadata files.
- Routed markdown graph regeneration through a single lore-graph persistence helper that writes mirrored graph JSON under `world_building/meta_data`, replaces the matching source slice in the canonical SQLite store, and keeps synthetic edges out of persisted graph structures.
- Added character-graph canonical adapters and source-scoped canonical graph replacement coverage so edited Markdown files cannot leave stale graph nodes or edges behind.
- Expanded Phase 1 regression coverage for metadata tree mirroring, synthetic-edge filtering in both JSON and canonical SQLite, source-scoped replacement, regeneration from missing graph metadata, and architectural guardrails that keep graph database access behind persistence.
- Fixed the default test lore import directory so it resolves to `tests/fixtures` from the project root instead of the `src` tree, with regression coverage for the path constant.

## Phase 2 Projection And Presentation Layer
- Established the first projection-read model for combined graph rendering, including lore graph loading, source scanning, place source rows, derived lore relationships, character-sheet graph filtering, and root-node selection outside the Streamlit entry point.
- Added projection tests that verify combined graph contracts, character-sheet filtering, graph loading through the projection layer, and guardrails that prevent `streamlit_app.py` from reintroducing direct graph assembly calls.
- Introduced a render-ready presentation contract for relationship graph views and routed Party View through it as the first working end-to-end presentation-layer graph view.
- Kept legacy Graphviz tab behavior in place for non-Party views while creating a stable vertical slice for the new architecture, so later work can migrate one view at a time instead of rewriting every tab at once.
- Preserved tab-specific behavior for the current UI while narrowing the intended Phase 3 finish line to a single stable view backed by projection and presentation data.
- Added artifact node styling to the Graphviz UI with a distinct hexagon border and matching heading-node support.
- Completed Phase 2.2 by adding artifact graph-edge configuration, artifact extraction/projection support, and Playwright coverage for artifact nodes in Places heading view and Session Notes directory view fixtures.
- Completed Phase 2.3 by moving graph node and edge allow-lists into split `config/nodes` and `config/edges` files, splitting compound connection labels into edge/node pairs, and deriving lore edge labels from combined evidence between connected nodes.

## Phase 3 Graph View Improvements
- Standardized Places and Session Notes Graphviz view inputs around `View Name`, `Source File`, and `Heading Selected`, moved source-file selection into the shared Streamlit rendering pipeline, kept heading filtering in the projection call, and added Session Notes Heading View to the visible graph views.
- Fixed Session Notes directory projection so extracted entities from `Family_Tree.md` are not treated as source documents, preventing duplicate `Family Tree` H1 nodes.
- Collapsed graph tabs to the supported `Character View`, `Party View`, and `Directory View` set, and restored Directory View header controls with source-file, heading, and H1/H2/H3 hide filters.
- Replaced the temporary Directory View tab with the final shared tab set: `Character View`, `Party View`, `Location View`, and `Session View` on every graph section. Location View and Session View now share the Directory View rendering pipeline through `config/graphviz/heading_view.json`.
- Split renderer configs from graph-view scenario fixtures: `config/graphviz` and `tests/fixtures/graphviz` now hold loadable Graphviz settings, while `tests/fixtures/graph_views` keeps source-fixture and screenshot metadata.

# experimental/knowledge_rewrite_phase3
## Phase 3 Descoped
- Began Phase 3 by introducing a pure combined-graph projection read model, moving lore graph loading and combined graph assembly out of `streamlit_app.py`, and adding guardrail tests so the Streamlit entry point consumes the projection API instead of direct graph internals.
- Added the first presentation-layer graph view by routing Party View through a render-ready presentation contract, keeping the Phase 3 target focused on one stable working view rather than perfecting every graph tab.
- Finished the manual source-root split by replacing stale `src.character_graph` imports with concrete `src.graph`, `src.extraction`, `src.ingest`, and `src.persistence` module imports, fixing Graphviz config path resolution after the move, and preserving hidden-heading evidence rows for character-only session sections.

# tag/v1.1.0

### Screenshot Fixture Cleanup And Deduplication Design
- Changed graph-view screenshot capture to use full-page screenshots at a larger viewport so e2e artifacts are not clipped.
- Removed committed `tests/fixtures/graph_views` JSON files so graph screenshot coverage is driven by the ingestion workflow and test-local view specs.
- Added a synthetic multi-session Discord-style session-note import fixture that starts at Session 1, and updated the e2e import test to use it instead of inline session data.
- Added `File View` and `Session View` to Place and Session Note lore graphs so users can filter by source file or Markdown heading, with File View fanning out root places/groups to linked characters.
- Removed unlisted `Place Lore` and `Session Lore` tabs from the visible Places and Session Notes graph views.
- Deprecated obsolete Place/Session graph screenshots that no longer map to active UI views.
- Added the node deduplication design for Character Deduplication, Place Deduplication, and Node Removal views.

### Session Note Evidence Cleanup
- Normalized session-note evidence table text into grammatical source-backed sentences, with an optional language-model polishing hook that rejects rewrites that drop required names or facts.

### Place Heading Semantics And Lore Notes
- Kept place and group Markdown headings in their authored heading-level columns while styling them with semantic place/group icons, fanned out derived place headings to character connections, and added non-graph lore summaries for descriptive headings such as `Town Overview`.

### Directory Graph View Variants
- Added parallel Directory File and Directory Session views for Places and Session Notes so the original graph views remain available while the directory-structured column layout can be compared in screenshots.

### Graph Tab And Table Cleanup
- Select favorite views from test views and tag as v1.1.0

# tag/v1.1.1
## 2026-07-20
### Full Structured Graph Restore 
- Enabled Knowledge Graph in UI without an env variable 
- Removed root level nodes on from places view in the knowledge graph
- Removed all references to the full knowledge graph from code as the title had become misleading

# feature/knowledge_graph2
## 2026-07-20
- Remove duplicate Family Tree nodes from the place graph.
- Move lore_graph_fixture.json to a hidden directory until node deduplication is implemented.

# feature/character_rewrite
## 2026-07-20

### Local Character Rewrite Evaluation
- Switched character rewrites to the local `llama` CLI model path, compared generated backstories against existing generated and original prose, and updated semantic scoring to include sentence-quality penalties for run-on, comma-heavy, repeated, and truncated output.

### Streamlit Rewrite Review UI
- Removed the local rewrite feature gate, kept the character editor visible after summary and backstory rewrite actions, and added focused Streamlit e2e coverage so generated text remains reviewable after save/rerun.

### Multi-Character Rewrite Comparison
- Added a second rewrite report generator for Orin Nightbloom, Jory Ravenmark, and Neal Lovington that scores source material, generated summaries, and generated backstories; Orin uses the generation 1 auto-generated backstory as the report source material.

## 2026-07-21

### Character Rewrite Workflow
- Added graph-backed summary and backstory rewrite actions to the character editor, routed rewrites through the local `llama` CLI path, and kept deterministic graph rewrites as the fallback path.
- Kept generated text reviewable after save/rerun and added focused Streamlit e2e coverage for the rewrite controls.

### Local Rewrite Model Tuning
- Tuned model-backed summary and backstory rewrites around the Qwen 0.5B local model candidate, removed retry-loop distractions, and kept deterministic graph rewrites as the fallback path.

### Rewrite Quality Reporting
- Split summary and backstory evaluation into dedicated single-character and multi-character reports with normalized 0-100 scores for overall quality, length, similarity, sentence length, and sentence quality.
- Added sentence-structure charts with sentence category distributions and KDE overlays for the single-character rewrite flow.
- Reordered report candidates so model rewrites appear first, previous Markdown rewrites appear second when present, and original/source text appears last without blocking release acceptance.

### Save Flow Safety
- Fixed generated-text promotion so choosing `Replace Original` promotes current generated summary and backstory text into the main character Markdown and removes stale generated/original markers.
- Added regression coverage for accepting generated character sections and preserving the promoted text in both Markdown and profile metadata.

### Supporting Graph Cleanup
- Included post-`knowledge_graph2` fixture and graph cleanup where it affected character rewrite inputs and report stability.
