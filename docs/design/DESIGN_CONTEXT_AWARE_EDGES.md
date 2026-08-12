# Context-Aware Knowledge Graph Edges

## Problem

The current knowledge graph mostly creates edges from a source document or Markdown heading to extracted entities. That makes directory-style views possible, but it also means relationship meaning is inferred later from heading visibility. When a user hides headings, projection code has to bridge through removed nodes and can keep the wrong edge, such as a generic `Session Notes` edge, while losing the more useful month or session context.

The known bugs show the same root issue from different angles:

- `bug_group_connection_context_transfer.md`: group evidence should stay attached to each visible ancestor heading, not fall back to generic source-document bridges.
- `node_type_bugs.md`: `Moon Gate` must be typed as a place before projection.
- `bug_groups_in_character_column.md`: `Indigo Cult` must be one group node, not both a group and a character.
- `bug_location_view_heading_levels_lost.md`: authored heading levels must survive graph creation so layout can place nodes in the right columns.

The best fix is to capture context during graph creation, before projection, hiding, deduplication, and Graphviz layout.

## Goals

- Build source-backed occurrence records for every extracted mention and relationship.
- Create direct semantic edges between co-mentioned entities when the evidence sentence supports the connection.
- Preserve Markdown context as provenance, not as the only relationship path.
- Keep group, place, artifact, character, family, heading, and source-document identities canonical before projection.
- Let projections choose visible context anchors from occurrence metadata instead of bridging hidden nodes opportunistically.
- Make heading-level layout deterministic by preserving authored heading levels on occurrence and heading records.

## Non-Goals

- Do not solve Graphviz layout by adding more synthetic semantic edges.
- Do not require a full language-model extraction pass for the first implementation.
- Do not promote every co-mention into a high-confidence relationship; default direct edges can be low-confidence `mentioned_with` edges.
- Do not remove source-document or heading nodes. They remain useful context nodes, but they should not be the only connection model.

## Proposed Model

Add an occurrence layer between text extraction and canonical graph persistence.

### `GraphOccurrence`

Each entity mention extracted from source text should become a record with:

| Field | Description |
| --- | --- |
| `id` | Stable id from source file, line, normalized entity id, and occurrence index. |
| `source_file` | Repo-relative source path. |
| `source_document_id` | Canonical source-document node id. |
| `source_line` | 1-based source line containing the evidence. |
| `evidence` | The sentence or clause supporting this occurrence. |
| `heading_stack` | Ordered H1-H6 records active at `source_line`. |
| `context_anchor_id` | Nearest heading id, or source document id if no heading exists. |
| `entity_id` | Canonical entity id. |
| `entity_name` | Display name at extraction time. |
| `entity_type` | Canonical type: `character`, `place`, `group`, `artifact`, `family`, etc. |
| `confidence` | Deterministic confidence score or enum. |
| `extraction_rule` | Rule or model source that produced the occurrence. |

### `ContextAwareEdge`

Edges created from occurrences should include:

| Field | Description |
| --- | --- |
| `source_id` | Semantic source node or context anchor. |
| `target_id` | Semantic target node. |
| `relationship_kind` | `context_anchor`, `direct_context`, or future explicit relationship kind. |
| `relation_type` | `mentioned`, `mentioned_with`, `located_at`, `member_of`, etc. |
| `evidence` | Evidence sentence or clause. |
| `source_line` | Source line from occurrence. |
| `context_anchor_id` | Nearest heading/source context. |
| `heading_stack` | Full authored heading stack. |
| `visible_ancestor_context_ids` | Precomputed fallback anchors for common hide modes. |

## Edge Creation Rules

1. Parse Markdown into heading-aware text spans.
   - Build stable heading ids from source file, line, level, and compact heading text.
   - Preserve original heading level and text.

2. Extract typed entity occurrences per evidence sentence.
   - Known character and place names win over capitalization heuristics.
   - Group patterns win over generic entity extraction, so `Indigo Cult` is not also a character.
   - Place-like names include configured words such as `gate`, `portal`, `temple`, `tower`, `harbor`, and known place aliases.

3. Canonicalize entities before edge creation.
   - Merge same-name same-type entities.
   - Resolve renamed test-harness groups such as `Ignis Cult`/`Indigo Cult` only through configured aliases, not ad hoc UI rules.
   - Keep headings as context nodes and semantic entities as domain nodes.

4. Create context-anchor edges.
   - For each occurrence, create `context_anchor -> entity`.
   - The nearest visible context can later change, but the occurrence keeps the full heading stack.

5. Create direct context edges.
   - For each evidence sentence, connect meaningful co-mentioned entities directly.
   - Prefer character/group, character/place, group/place, artifact/character, and artifact/place pairs.
   - Use `mentioned_with` when no stronger deterministic relationship is inferred.
   - Avoid creating direct edges between two headings, between source document and heading, or between low-confidence incidental candidates.

6. Deduplicate after context and direct edges exist.
   - Deduplication keys must include source, target, relation type, relationship kind, context anchor, and evidence line.
   - Generic source-document context loses to a more specific heading context for the same evidence path.

## Projection Behavior

Projection should consume context-aware edges instead of inventing bridges.

- If H3 is hidden and H2 is visible, use the occurrence's H2 ancestor as the visible context anchor.
- If H1 and H3 are hidden but H2 is visible, still route to H2.
- If all headings are hidden, keep semantic direct edges and use the nearest hidden heading label as edge provenance, not as a visible node.
- If a generic `Session Notes` edge and a specific month/session edge describe the same evidence, keep the specific edge.
- Graphviz helper edges remain render-only and must not feed semantic relationship decisions.

## Implementation Plan

1. Add `src/graph/context_edges.py`.
   - Define `GraphOccurrence`, `HeadingContext`, and `ContextAwareEdge`.
   - Add Markdown heading-stack parsing with line numbers.
   - Add occurrence-to-edge derivation.

2. Move session-note derived relationships onto the occurrence model.
   - Keep the current dict output as a compatibility adapter.
   - Add metadata fields expected by `tests/unit/graph/test_context_aware_edges.py`.

3. Tighten deterministic typing.
   - Add `gate` and related terms to place detection.
   - Suppress normal entity candidates whose canonical key already exists as a group.
   - Let configured aliases and known names override regex defaults.

4. Persist occurrence metadata in canonical graph edges.
   - Store `source_line`, `context_anchor_id`, `heading_stack`, `relationship_kind`, and `extraction_rule` in edge provenance/properties.

5. Update projections.
   - Replace hidden-heading bridge creation with visible-anchor selection from occurrence metadata.
   - Deduplicate using context-aware keys.

6. Migrate Graphviz rendering.
   - Render only final projection edges plus explicit render helper edges.
   - Keep helper edges out of canonical graph storage.

## Test Plan

The initial failing coverage is in `tests/unit/graph/test_context_aware_edges.py`:

- Occurrences include `source_line`, `heading_stack`, and `context_anchor_id`.
- Graph creation emits a direct `Mr Light -> Ignis Cult` context edge from a shared evidence sentence.
- Repeated group evidence under different months preserves both visible H2 ancestors when H3 headings are hidden.
- `Moon Gate` is typed as a place before projection.
- `Indigo Cult` appears only as a group node, not as both group and character.

Additional implementation tests should cover:

- Place heading nodes retain authored H1/H2/H3 levels from `Atlantia_Lore.md`.
- Hiding all heading levels still leaves useful semantic direct edges.
- Generic source-document edges lose to more specific heading-context edges during deduplication.
- Context-aware edge metadata survives canonical SQLite persistence and source-scoped replacement.

## Acceptance Criteria

- With file name hidden and session headings hidden, cult/group nodes remain connected to each visible month that contains evidence.
- No stale generic `Session Notes` edge wins over a more specific context edge for the same evidence.
- Direct entity-to-entity edges exist at graph creation time for high-value co-mentioned entities.
- Group and place typing is resolved before projection and rendering.
- Location View can lay out place nodes by original heading level.
