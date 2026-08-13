# Knowledge View Definition Migration

## Purpose

This document captures a backlog migration for making knowledge graph views data-driven in the main Streamlit app.

The current branch has three related concepts that are useful but not fully unified:

- `tests/fixtures/graph_views/*.json` describe expected user-facing graph scenarios.
- `config/graphviz/*.json` describe Graphviz style, layout, column, and inheritance behavior.
- `src/rendering/graphviz_rendering.py` still contains Python-specific view wiring, tab decisions, source and heading controls, projection selection, table policy, and Graphviz config lookup.

The migration goal is to turn graph view definitions and Graphviz config into one hierarchical view-definition system used by the app, tests, and documentation. The renderer should execute view definitions instead of carrying custom per-view branching logic.

This is backlog work. It does not need to happen on the current `feature/knowledge_graph3` branch.

## Problem

The application currently has useful graph-view behavior, but the source of truth is split.

Test fixtures describe views such as Characters Graph Party View, Places Graph Location View, and Session Notes Graph Session View. These fixtures are good scenario contracts, but they are not loaded by the app.

Graphviz config files already support inheritance through `inherits`, but they only configure rendering details. They do not declare which projection, source-file predicate, controls, or connection-table behavior a view should use.

The Streamlit rendering module still has custom code for:

- Choosing visible tabs.
- Mapping a tab to a projection function.
- Mapping a tab to a Graphviz config key.
- Deciding whether source-file and heading filters are shown.
- Deciding whether source-document roots and heading levels can be hidden.
- Rendering Character View, Party View, Location View, Session View, and Full Knowledge Graph through separate paths.

This makes view behavior harder to audit and harder to extend. It also increases the chance that tests and the app drift apart.

## Desired Outcome

Knowledge graph views should be defined by a hierarchical configuration model.

At minimum, each app-facing view definition should declare:

- Stable `view_key`.
- User-facing `label`.
- Top-level graph families or app tabs where it appears.
- Projection strategy.
- Source predicate strategy.
- Graphviz config key.
- Column layout key when still needed by the graph projection/layout engine.
- UI controls.
- Table policy.
- Empty-state messages.
- Optional screenshot or fixture metadata for tests.

The Streamlit renderer should be mostly generic:

1. Load the active view definitions.
2. Render tabs from those definitions.
3. Render controls declared by the selected definition.
4. Resolve named projection and predicate strategies through a small registry.
5. Load the hierarchical Graphviz config referenced by the view definition.
6. Render the graph and declared tables.

## Proposed Config Shape

The exact file layout can change, but the preferred direction is to add app-facing view definitions under:

```text
config/knowledge_views/
  global_view_defaults.json
  character_view.json
  party_view.json
  location_view.json
  session_view.json
  full_knowledge_graph.json
```

Example:

```json
{
  "schema_version": "0.1.0",
  "view_key": "session_view",
  "label": "Session View",
  "description": "Directory-style graph for a selected session-note source file or heading.",
  "inherits": "config/knowledge_views/global_view_defaults.json",
  "visible_in": ["Characters", "Places", "Session Notes"],
  "projection": {
    "strategy": "markdown_header_lore_graph",
    "source_predicate": "session_notes",
    "fanout_linked_characters": true
  },
  "controls": {
    "source_file": true,
    "heading": true,
    "include_all_heading_option": true,
    "hide_source_document_roots": true,
    "hide_heading_levels": [1, 2, 3]
  },
  "graphviz": {
    "config_key": "session_view",
    "column_layout": "session_note_lore_directory"
  },
  "tables": {
    "connections": "character_connections_only",
    "lore_notes": false
  },
  "empty_states": {
    "source": "Add Session Notes To Use Session View.",
    "heading": "Add Markdown Headings To Session Notes To Use Session View.",
    "graph": "No Session Note Connections Were Found For This File."
  }
}
```

## Relationship To Graphviz Config

Graphviz config should remain focused on DOT rendering behavior:

- Graph attributes.
- Node and edge attributes.
- Spacing.
- Columns.
- Node type overrides.
- Constraint policy.
- Invisible layout guides.

Knowledge view definitions should reference Graphviz config by key rather than duplicating style/layout values.

The hierarchy should look like:

```text
knowledge view definition
  -> projection strategy
  -> control contract
  -> table policy
  -> graphviz config key
       -> global graphviz defaults
       -> shared heading/directory graphviz config
       -> concrete view graphviz override
```

This keeps app behavior and DOT rendering related but separate.

## Python Registry

The config should not contain Python import paths. It should use stable strategy names resolved by a registry.

Initial registries:

- Projection strategies:
  - `focused_character_graph`
  - `party_character_graph`
  - `place_lore_graph`
  - `markdown_header_lore_graph`
  - `full_knowledge_graph`
- Source predicates:
  - `places`
  - `session_notes`
  - `all_lore`
- Table policies:
  - `none`
  - `all_connections`
  - `character_connections_only`
  - `lore_notes`
- Renderer strategies:
  - `focused_root_selector`
  - `presented_relationship_graph`
  - `directory_lore_graph`
  - `full_graph`

Small Python registries are acceptable. The migration target is to remove custom per-view branching from the renderer, not to eliminate every strategy function.

## Migration Plan

### Phase 1: Model And Loader

- Add typed dataclasses for knowledge view definitions.
- Add a config loader with inheritance and validation.
- Add tests for merge order, unknown strategy names, missing required fields, and malformed control/table declarations.
- Keep the existing renderer unchanged.

### Phase 2: Promote Test Fixtures Into View Contracts

- Add app-facing config files for Character View, Party View, Location View, Session View, and Full Knowledge Graph.
- Cross-check the new configs against `tests/fixtures/graph_views/*.json`.
- Decide whether test fixtures should become generated from app config or remain scenario-specific fixtures that reference app config keys.

### Phase 3: Migrate Directory Views First

- Replace Python-defined `LoreGraphViewDefinition` objects for Location View and Session View with loaded configs.
- Keep existing projection functions.
- Keep existing Graphviz config files.
- Verify source-file filters, heading filters, hide-source controls, hide-heading controls, graph rendering, and connection tables.

### Phase 4: Migrate Party And Character Views

- Move Party View into a `presented_relationship_graph` renderer strategy.
- Move Character View into a `focused_root_selector` renderer strategy.
- Keep strategy-specific code small and isolated.
- Remove duplicate tab and view-name branching from `graphviz_rendering.py`.

### Phase 5: Migrate Full Knowledge Graph

- Add a `full_graph` renderer strategy.
- Define hide-source-file and future hide-heading controls in config.
- Keep this separate from the legacy Month Selection view until that view is intentionally retired or migrated.

### Phase 6: Cleanup And Documentation

- Delete obsolete compatibility wrappers once all callers use the new definitions.
- Update `docs/specs/KNOWLEDGE_GRAPH_UI_SPEC.md` and `docs/specs/GRAPH_PROJECTION_SPEC.md`.
- Update screenshot fixtures or regenerate them if the rendered view structure intentionally changes.
- Add a short README for `config/knowledge_views/`.

## Testing Strategy

Unit tests:

- Loader inheritance and validation.
- Registry lookup failures produce helpful errors.
- Active tab definitions resolve to the expected view sequence.
- Location View and Session View configs resolve to the expected projection, predicate, controls, table policy, Graphviz key, and column layout.
- Graphviz config inheritance remains independent from knowledge view inheritance.

Rendering tests:

- Existing Graphviz rendering tests should continue to pass.
- Add tests that execute views through loaded definitions rather than hand-built Python definitions.

E2E and screenshot tests:

- Character View screenshot.
- Party View screenshot.
- Location View screenshot.
- Session View screenshot.
- Full Knowledge Graph screenshot, if enabled.

Regression expectations:

- Edge labels remain attached to their owning edges.
- Column order remains stable.
- Source-file filtering and heading filtering behave the same as before the migration.
- Connection tables continue to hide source-document and non-character rows where required.

## Risks

- Visual regressions are easy to introduce because small config changes can alter DOT layout.
- Over-declarative config can become harder to understand than the current Python code.
- Character View and Party View do not fit the same source-file and heading projection model as Location View and Session View.
- Existing `column_layout` strings still drive behavior in `src/graph/combined_graph.py`; they may need their own later migration into declarative column rules.
- Full Knowledge Graph and legacy Month Selection should not be accidentally collapsed into one view.

## Recommended Scope

The first implementation should not try to make every graph behavior declarative.

Recommended first milestone:

- Create the knowledge view definition loader.
- Load Location View and Session View from config.
- Keep Character View and Party View on their current renderer strategies until the directory views prove the approach.

This gives the app a real hierarchical view-definition path while keeping the blast radius contained.

