# Knowledge View Definition Migration

## Purpose

This document captures the Phase 0 migration roadmap for the next release. The work makes knowledge graph views data-driven in the main Streamlit app before the context-aware edge phases depend on those views.

The current branch has three related concepts that are useful but not fully unified:

- `tests/fixtures/graph_views/*.json` describe expected user-facing graph scenarios.
- `config/graphviz/*.json` describe Graphviz style, layout, column, and inheritance behavior.
- `src/rendering/graphviz_rendering.py` still contains Python-specific view wiring, tab decisions, source and heading controls, projection selection, table policy, and Graphviz config lookup.

The migration goal is to turn graph view definitions and Graphviz config into one hierarchical view-definition system used by the app, tests, and documentation. The renderer should execute view definitions instead of carrying custom per-view branching logic.

This is planned as next-release Phase 0 work. It does not need to happen on the current `feature/knowledge_graph3` branch, but the design should remain small enough that the migration can be back-ported if the current release needs the hierarchical view-definition path.

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

- `view_name`.
- `graphviz_view`.
- `source_fixtures`.
- `hidden_elements`.
- `unhidden_elements`.
- Optional `columns`.

Additional renderer, projection, table, and empty-state behavior can be added later after the stubs prove useful. Phase 0 should not commit to those execution details too early.

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
  "view_name": "Session View",
  "description": "Directory-style graph for a selected session-note source file or heading.",
  "source_fixtures": [
    "tests/fixtures/character_sheets",
    "tests/fixtures/session_notes/complex_session_graph.md"
  ],
  "hidden_elements": [
    "file_name",
    "h1",
    "h2",
    "h3"
  ],
  "unhidden_elements": [
    "file_name"
  ],
  "columns": [
    ["source_files"],
    ["h1", "places"],
    ["main_characters"],
    ["h2", "groups", "artifacts"],
    ["h3"],
    ["secondary_characters"]
  ],
  "graphviz_view": "heading_view",
  "migration_status": "stub"
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

Knowledge view definitions should reference Graphviz config with `graphviz_view` rather than duplicating DOT styling values. Semantic column grouping can live in knowledge view definitions because it describes the view, not the Graphviz renderer.

The hierarchy should look like:

```text
knowledge view definition
  -> projection strategy
  -> control contract
  -> table policy
  -> graphviz_view
       -> global graphviz defaults
       -> shared heading/directory graphviz config
```

This keeps app behavior and DOT rendering related but separate.

Knowledge views should not have a `global_view_defaults.json` or `inherits` chain. Each knowledge view file should be explicit. This avoids recreating the hierarchy confusion this migration is meant to remove.

During the transition, Graphviz configs may still contain `columns` for compatibility. Once the renderer reads `knowledge_views.columns`, `config/graphviz/location_view.json` and `config/graphviz/session_view.json` can be deleted and both app views can use `graphviz_view: "heading_view"`.

## Python Registry

The Phase 0 stubs should not contain Python import paths or strategy names. They only identify the view, source fixtures, hidden and unhidden elements, optional columns, and the backing Graphviz view.

When rendered as UI controls, the union of `hidden_elements` and `unhidden_elements` appears in the `Hide Elements` row. Entries in `hidden_elements` start checked, and entries in `unhidden_elements` start unchecked. If an element appears in both lists, `unhidden_elements` wins so the element is listed but visible by default.

When runtime migration starts, renderer and projection behavior should be added through stable strategy names resolved by a registry.

## Runtime Source Scope Gap

Adding a fifth knowledge view is not only an ordering problem. The current app loads view definitions from config, but source selection still comes from the live Streamlit dropdowns and the active lore directory. The `source_fixtures` field is test/import metadata; it does not constrain runtime source files.

Until this is redesigned, `config/knowledge_view_order.json` should activate only the four migrated views:

- `character_view`
- `party_view`
- `location_view`
- `session_view`

Supporting additional views such as `family_tree` needs a source-scope contract first. A future design should decide whether each view can declare one of these policies:

- Use all live sources matching `source_predicate`.
- Use a configured source subset.
- Use a configured default source while still allowing the live dropdown.
- Use fixture paths only in tests, never at runtime.

That decision belongs with the view definition model, not in Graphviz rendering.

Possible future registries:

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

### Phase 0.1: Model And Loader

- Add typed dataclasses for knowledge view definitions.
- Add a config loader with inheritance and validation.
- Add tests for merge order, unknown strategy names, missing required fields, and malformed control/table declarations.
- Keep the existing renderer unchanged.

### Phase 0.2: Promote Test Fixtures Into View Contracts

- Add app-facing config files for Character View, Party View, Location View, Session View, and Full Knowledge Graph.
- Cross-check the new configs against `tests/fixtures/graph_views/*.json`.
- Decide whether test fixtures should become generated from app config or remain scenario-specific fixtures that reference app config keys.

### Phase 0.3: Migrate Directory Views First

- Replace Python-defined `LoreGraphViewDefinition` objects for Location View and Session View with loaded configs.
- Keep existing projection functions.
- Keep existing Graphviz config files.
- Verify source-file filters, heading filters, hide-source controls, hide-heading controls, graph rendering, and connection tables.

### Phase 0.4: Migrate Party And Character Views

- Move Party View into a `presented_relationship_graph` renderer strategy.
- Move Character View into a `focused_root_selector` renderer strategy.
- Keep strategy-specific code small and isolated.
- Remove duplicate tab and view-name branching from `graphviz_rendering.py`.

### Phase 0.5: Migrate Full Knowledge Graph

- Add a `full_graph` renderer strategy.
- Define hide-source-file and future hide-heading controls in config.
- Keep this separate from the legacy Month Selection view until that view is intentionally retired or migrated.

### Phase 0.6: Cleanup And Documentation

- Delete obsolete compatibility wrappers once all callers use the new definitions.
- Update `docs/specs/KNOWLEDGE_GRAPH_UI_SPEC.md` and `docs/specs/GRAPH_PROJECTION_SPEC.md`.
- Update screenshot fixtures or regenerate them if the rendered view structure intentionally changes.
- Add a short README for `config/knowledge_views/`.

## Old View Retirement Plan

The migration is not complete until the app has one active knowledge-view path and the old Graphviz-view-specific path is removed. The desired final state is:

- `config/knowledge_views/*.json` defines every app-visible graph view.
- `config/graphviz/*.json` defines only Graphviz styling and shared renderer behavior.
- `graphviz_rendering.py` renders loaded view definitions instead of branching on hardcoded tab names.
- Location View and Session View both use `graphviz_view: "heading_view"` plus their own `columns`.
- `config/graphviz/location_view.json` and `config/graphviz/session_view.json` are deleted.
- Tests load the same view definitions as the app instead of maintaining parallel graph-view scenario contracts.

### Retirement Step 1: Freeze Legacy View Additions

- Treat `config/graphviz/location_view.json` and `config/graphviz/session_view.json` as compatibility-only files.
- Do not add new app behavior to Graphviz configs.
- Do not add new hardcoded graph tab names to `graphviz_rendering.py`.
- Add a short comment or test assertion that Location View and Session View must resolve through `knowledge_views`.

Exit gate:

- Unit tests prove `graph_tab_names()` and directory view definitions load from `config/knowledge_views`.

### Retirement Step 2: Move Remaining View Semantics Into Knowledge Views

Add the missing app semantics to each knowledge view definition only when the renderer needs them:

- Renderer strategy.
- Projection strategy.
- Source predicate.
- Source and heading control labels.
- Empty-state messages.
- Connection table policy.

Keep these as stable string keys resolved by Python registries. Do not put Python import paths in JSON.

Exit gate:

- Character View, Party View, Location View, and Session View can each be constructed from `KnowledgeViewDefinition` without custom tab-name branching.

### Retirement Step 3: Replace Legacy Directory View Construction

- Remove direct Python construction of Location View and Session View from the renderer.
- Replace it with a generic directory-view adapter that consumes loaded knowledge view definitions.
- Inject `knowledge_view.columns` into the loaded Graphviz config.
- Keep `column_layout` only as an internal transition field while `combined_graph.py` still needs it.

Exit gate:

- Location View and Session View screenshots match or intentionally update approved fixtures.
- Source-file filters, heading filters, and Hide Elements controls work from loaded config.
- No runtime call loads `config/graphviz/location_view.json` or `config/graphviz/session_view.json`.

### Retirement Step 4: Delete Redundant Graphviz View Files

Delete:

```text
config/graphviz/location_view.json
config/graphviz/session_view.json
tests/fixtures/graphviz/location_view.json
tests/fixtures/graphviz/session_view.json
```

Update tests that referenced those files to use:

- `config/knowledge_views/location_view.json`
- `config/knowledge_views/session_view.json`
- `config/graphviz/heading_view.json`

Exit gate:

- `rg '"location_view"|"session_view"' config/graphviz tests/fixtures/graphviz src tests` shows no Graphviz config-key dependency on deleted files.
- Graphviz config tests prove `heading_view` remains the shared Graphviz base for directory views.

### Retirement Step 5: Retire Legacy View Constants And Compatibility Wrappers

Delete or reduce legacy constants, compatibility wrappers, and standalone render helpers when no longer needed.

Keep constants only when they are stable public labels used by tests and app config.

Exit gate:

- `graphviz_rendering.py` has one entry point for rendering loaded graph views.
- There is no code path that renders Directory View, Heading View, Directory File View, Directory Section View, or Place Lore as app-visible tabs.

### Retirement Step 6: Merge Test Scenario And App Config Contracts

- Decide whether `tests/fixtures/graph_views/*.json` should reference app `view_key`s or be generated from `config/knowledge_views`.
- Remove duplicate fields from test fixtures when they are already owned by app config.
- Keep screenshot-specific fields, source fixture bundles, and expected table assertions in test fixtures if they are test-only concerns.
- Keep unit-test knowledge view fixtures under `tests/fixtures/knowledge_views` so test data does not depend on live production config while the UI migration is still settling.

Exit gate:

- A change to a knowledge view's `view_name`, `columns`, `hidden_elements`, `unhidden_elements`, or `graphviz_view` affects both app behavior and view-contract tests.
- No test passes because it uses an old fixture definition that the app ignores.

### Retirement Step 7: Final Guardrails

Add tests that fail if legacy paths reappear:

- No `config/graphviz/location_view.json` or `config/graphviz/session_view.json` files exist.
- Directory views reference `graphviz_view: "heading_view"`.
- `graphviz_rendering.py` loads view names from `config/knowledge_views`.
- No hardcoded app-visible graph tab list exists outside the knowledge view loader.
- No Graphviz config file contains app-facing source fixture or hidden-element settings.

Retirement is complete when those guardrails pass and the app has no fallback path for the old view definitions.

## Back-Port Option

If this work needs to be back-ported into the current release, keep the scope to the smallest useful vertical slice:

- Add the typed definition loader.
- Add Location View and Session View configs.
- Route only the directory-style views through loaded definitions.
- Leave Character View, Party View, Full Knowledge Graph, and Month Selection on their current code paths.

This provides the hierarchical view-definition path without forcing the whole renderer migration into the release branch.

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
