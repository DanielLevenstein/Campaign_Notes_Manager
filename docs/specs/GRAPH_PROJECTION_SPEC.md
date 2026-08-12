# Graph Projection API Specification

This document specifies the projection API needed to support the current knowledge graph views in the Streamlit application. The goal is to make every existing graph view implementable through a single projection module instead of view-specific graph heuristics.

## Goals

- Provide a stable API for view projections and file/heading selection lists.
- Decouple view behavior from the underlying graph storage and node-type heuristics.
- Support all existing Characters, Places, Session Notes, and Structured Graph views.
- Enable future extension for deduplication, migration, and canonical graph layering.

## Current Supported View Patterns
### New Design
Every top-level section displays the same four graph tabs:

- Character View
- Party View
- Location View
- Session View

Location View uses the shared Directory View presentation pipeline with source-file drop-downs filtered to place lore. Session View uses the same Directory View pipeline with source-file drop-downs filtered to session notes.

### Old Design

1. Characters
   - Character View (focused graph by root character)
   - Party View (full character-connection view)
2. Places
   - Location View (place source file projection)
   - Heading View (place markdown heading projection)
   - Directory File View (place source file projection with directory-style layout)
3. Session Notes
   - Location View (session-note source file projection)
   - Heading View (session-note markdown heading projection)
   - Directory File View (session-note source file projection with directory-style layout)
4. Structured Knowledge
   - Full graph with lore source knots hidden
   - Session-note month filtering

## Updated Patterns
- Graphviz views must not change depending on what tab they are displayed under. 
- Views should take two parameters ("View Name", "Source File", "Heading Selected") Streamlit should handle code determining what files are present in dropdowns.
- Streamlit should handle filtering based on files while graph projection should handle filtering based on heading. Only nodes from the selected source file should be sent to projection module.
- In streamlit heading filters should be displayed as a separate dropdown from the "Source File" dropdown. 
- Location View and Session View are separate visible tabs backed by the shared Directory View rendering pipeline and `heading_view` Graphviz config.

## Document View Improvement
- UI buttons should be added to the Directory view to hide elements with a checkbox next to each node element which we support hiding. 
- When heading elements are hidden new graph connections should be created from the hidden node to all it's children with h1-h3 being the inital connection label. 
- language model should be used to update the derived connection labels values.

![Directory View Busy](docs/screenshots/Session_Notes_Busy.png)
**In the figure above "Tharevon" is connected to the "Pixi Kingdom" through "Session 4" but in current ui it's almost impossible to see**

## Hidden Nodes


## Required Projection API Surface

The projection module should expose the following capabilities:

### 1. Source File List Projection

Returns selectable source-file choices for a given view predicate.

Signature example:
```
get_source_file_options(
    graph: CombinedCharacterGraph,
    source_predicate: Callable[[CombinedCharacterNode], bool],
) -> list[tuple[str, str]]
```

Responsibilities:
- Discover all nodes with `source_file` that satisfy the provided predicate.
- Return options as `(display_label, source_file)` pairs.
- Use normalized path equality for default selection matching.

This projection supports:
- Places Location View
- Session Notes Location View
- directory-style file views

### 2. Heading List Projection

Returns selectable markdown-heading options for a given source predicate and optional projected graph.

Signature example:
```
get_heading_options(
    graph: CombinedCharacterGraph,
    source_predicate: Callable[[CombinedCharacterNode], bool],
    projected_graph: CombinedCharacterGraph | None = None,
) -> list[tuple[str, str]]
```

Responsibilities:
- Discover markdown headings from source files that satisfy the source predicate.
- Only include headings present in the optional projected graph when provided.
- Format labels as `FileName / H{level}: {heading text}`.

This projection supports:
- Places Heading View
- Session Notes Heading View

### 3. Place Lore Projection

Produces a place-aware projected graph for a source file or heading.

Signature example:
```
project_place_lore_graph(
    graph: CombinedCharacterGraph,
    source_file: str | None = None,
    heading_id: str | None = None,
    fanout_linked_characters: bool = False,
    hide_source_document_roots: bool = False,
) -> CombinedCharacterGraph
```

Responsibilities:
- Build projected source-heading nodes for markdown sections.
- Retarget place edges through semantic headings where appropriate.
- Include place, group, character, and source-document roots relevant to the chosen source or heading.
- Optionally hide source-document roots for cleaner section and directory layouts.

This projection supports:
- Places Location View
- Places Heading View
- Places Directory File View

### 4. Session Note Projection

Produces a session-note-aware projected graph for a source file or heading.

Signature example:
```
project_session_note_graph(
    graph: CombinedCharacterGraph,
    source_file: str | None = None,
    heading_id: str | None = None,
    fanout_linked_characters: bool = False,
    hide_source_document_roots: bool = False,
    hide_node_types: set[str] | None = None,
    hide_heading_levels: set[int] | None = None,
) -> CombinedCharacterGraph
```

Responsibilities:
- Select nodes by session-note source predicate rather than only `source_document` type.
- Build projected heading nodes from markdown source files.
- Include connected characters, groups, places, and source documents as appropriate.
- Optionally hide source-document roots.
- Optionally hide nodes by node type and markdown heading level to support alternative renderings and deduplication-aware display.

This projection supports:
- Session Notes Location View
- Session Notes Heading View
- Session Notes Directory File View

### 5. Session Note Month Projection

Provides a month-filtered session-note graph.

Signature example:
```
filter_session_note_graph_by_month(
    graph: CombinedCharacterGraph,
    month: str,
) -> CombinedCharacterGraph
```

Responsibilities:
- Filter a session-note graph to only include source documents matching the selected month grouping.
- Preserve all connected nodes and edges for the selected session notes.

This projection supports:
- Session Note Month View

### 6. Structured Graph Projection

Produces the full structured graph with source-document knots hidden.

Signature example:
```
project_structured_knowledge_graph(
    graph: CombinedCharacterGraph,
    hide_node_types: set[str] | None = None,
    hide_heading_levels: set[int] | None = None,
) -> CombinedCharacterGraph
```

Responsibilities:
- Remove hidden lore source nodes from the final view.
- Preserve all remaining character, place, and relationship connectivity.
- Optionally hide nodes by node type and markdown heading level for additional rendering variants.

This projection supports:
- Full Structured Knowledge View

### 7. Focused Character Projection

Provides the graph data for the Character View root selector.

Signature example:
```
project_focused_character_graph(
    graph: CombinedCharacterGraph,
    center_node_id: str,
) -> CombinedCharacterGraph
```

Responsibilities:
- Return the “other connections” graph centered on the selected character node.
- Preserve connected nodes and relationship evidence needed for the focused view.

This projection supports:
- Characters Character View

### 8. Full Character Connection Projection

Provides the party/character data-only graph.

Signature example:
```
project_character_connection_graph(
    graph: CombinedCharacterGraph,
    hide_node_types: set[str] | None = None,
    hide_heading_levels: set[int] | None = None,
) -> CombinedCharacterGraph
```

Responsibilities:
- Return a graph containing all character-character relationships used by the party view.
- Allow nodes to be hidden by type or heading level so deduplication and alternate renderers can filter out noisy nodes.

This projection supports:
- Characters Party View
- Places Party View
- Session Notes Party View

## View Support Matrix

| UI View | Projection API | Selection Options |
|---|---|---|
| Characters - Character View | `project_focused_character_graph` | root character options from main tab nodes |
| Characters - Party View | `project_character_connection_graph` | none |
| Places - Location View | `project_place_lore_graph(source_file=...)` | `get_source_file_options` with place source predicate |
| Places - Heading View | `project_place_lore_graph(heading_id=...)` | `get_heading_options` with place source predicate |
| Places - Directory File View | `project_place_lore_graph(source_file=..., hide_source_document_roots=True)` | same as Location View |
| Session Notes - Location View | `project_session_note_graph(source_file=...)` | `get_source_file_options` with session-note predicate |
| Session Notes - Heading View | `project_session_note_graph(heading_id=...)` | `get_heading_options` with session-note predicate |
| Session Notes - Directory File View | `project_session_note_graph(source_file=..., hide_source_document_roots=True)` | same as Location View |
| Session Note Month View | `filter_session_note_graph_by_month(session_note_graph, month)` | month options from session-note metadata |
| Structured Knowledge View | `project_structured_knowledge_graph` | none |

## Selection Predicates

The projection module should expose or accept predicates for these source categories:

- `is_place_source_document_node(node)`
- `is_session_note_node(node)`
- `is_lore_source_node(node)`

These predicates are used to build source-file lists and heading lists.

## Requirements

- Projection graph should display node elements in graph in a deterministic order.
- Projection results should preserve node ids and edge evidence when possible, but may introduce synthetic heading nodes for markdown projections.
- Path normalization should be deterministic and support Windows path separators in a portable way.
- When a projection hides source-document roots, the resulting graph must remain connected for the displayed nodes.
- Heading projections must exclude headings that have no associated graph content when a projected_graph filter is applied.
- Projections must support hiding nodes by node type and markdown heading level to enable deduplication-aware rendering and display variants.
- Hide rules should be combinable with source-file, heading, and structured graph projections.

## Implementation Notes

- `get_source_file_options` should return unique, sorted file labels.
- `get_heading_options` should only expose headings that are actually present in the chosen projected graph when `projected_graph` is supplied.
- `project_place_lore_graph` and `project_session_note_graph` should both build heading nodes from markdown content and route edges through the nearest heading.
- `project_structured_knowledge_graph` should hide source-document knots instead of removing source-document edges.
- `project_focused_character_graph` should mirror the existing `other_connections_graph` helper.
- `project_character_connection_graph` should mirror the existing `full_character_connection_graph` helper.

## Future Extension

The projection API should be designed to sit above a canonical graph service. This means:

- Projections can be implemented from canonical node/edge data rather than legacy `node_type` strings.
- The view layer can consume projections without knowing which graph source or import flow produced the nodes.
- Future deduplication, review rules, and migration logic can operate in a separate layer beneath the projection API.
