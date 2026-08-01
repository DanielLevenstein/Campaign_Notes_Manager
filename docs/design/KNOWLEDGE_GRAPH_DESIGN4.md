# Decoupling Views from the Knowledge Graph

## Overview

Current problem: UI view logic and the knowledge-base representation are tightly coupled, causing fragile behaviour when imports or extraction pipelines produce nodes that do not match UI expectations (for example, session-note imports that lack `source_document` node types). This design specifies a clean separation between the canonical knowledge graph (data layer) and presentation/projection code (view layer) so the UI can reliably render file/heading projections and the graph ingestion pipeline can evolve independently.

## Goals

- Define a canonical graph model and storage API that is authoritative for node/edge data and metadata.
- Provide a stable projection API for views that converts canonical graph data into view-specific graphs.
- Make ingestion and extraction pipelines responsible only for producing canonical graph updates and events.
- Support incremental updates, versioning, and safe migration to new node/edge schemas.
- Improve testability by isolating the graph logic from Streamlit UI components.

## Principles

- Single source of truth: the canonical graph store is the authoritative representation of nodes, edges, and metadata.
- Explicit projection layer: views request projections or materialized subgraphs via a well-defined API rather than referencing internal node types directly.
- Event-driven updates: ingestion emits events that projection layers and caches can subscribe to; UI receives notifications when projections change.
- Backwards compatibility: create adapter layers to map legacy node/edge shapes into the canonical model.

## Components

1. Canonical Graph Service
   - Responsibilities: store nodes/edges, maintain node metadata (id, canonical type, source_file, source_id, timestamps, provenance), perform canonicalization and deduplication, expose query API.
   - Implementation choices: lightweight JSON-on-disk + SQLite index, or embedded graph DB (Neo4j/Arango) depending on scale. For this project prefer a small embedded store (SQLite + JSON columns) for portability.
   - Public API (example):
     - `upsert_node(node: dict) -> NodeID`
     - `upsert_edge(edge: dict) -> EdgeID`
     - `get_nodes(filter: dict) -> list[dict]`
     - `get_edges(filter: dict) -> list[dict]`
     - `get_nodes_by_source_file(path: str) -> list[dict]`

2. Ingest / Extraction Pipeline
   - Responsibilities: parse incoming files, extract entity/relationship candidates, normalize and call Canonical Graph Service to persist nodes/edges.
   - Emits domain events (e.g., `source_file_added`, `graph_updated`) containing minimal payload (source path, affected node ids) to drive UI selection or re-projection.

3. Projection Service (View Adapter)
   - Responsibilities: take projection queries (for example: `by_source_file(path)`, `by_heading(id)`, `focused_graph(center_ids, radius)`), apply transformation rules and return CombinedCharacterGraph-like objects for the UI.
   - Must NOT rely on node_type heuristics alone — instead projections should be able to query on `source_file`, `provenance.source_kind`, or canonical type aliases.
   - Provide caching and invalidation hooks keyed by `projection_key` + `source_version`.

4. UI Layer
   - Responsibilities: render projections returned by the Projection Service. For session-note import flows, the UI should react to `source_file_added` events to pre-select file choices.
   - The UI should only consume the projection API and never read internal graph storage directly.

5. Event Bus / Notification
   - Responsibilities: decouple producers (ingest) and consumers (projection cache, UI). Could be implemented with simple in-process Pub/Sub, filesystem event hooks, or a message broker for distributed setups.

## Data Model (Canonical)

- Node: {id, canonical_type, display_name, source_file, source_id, properties: dict, canonical_tags: list, created_at, updated_at, provenance}
- Edge: {id, source_id, target_id, relation_type, properties, evidence: list, created_at}

Notes:
- `canonical_type` replaces fragile `node_type` strings: map legacy types into canonical types during ingestion.
- `source_file` should always be stored as normalized absolute or repo-relative path. Use a deterministic normalization function (replace backslashes, collapse dots, lower-case on equality operations but preserve original casing for display).

## Projection API Examples

- get_files_projection(source_dir: str) -> list[{label, source_file, version}]
- get_file_headings(source_file: str) -> list[{heading_id, level, text}]
- get_file_projection(source_file: str, heading_id: str|None, radius: int=2) -> {nodes, edges}

Projection behavior:
- `get_file_projection` should operate by querying nodes where `source_file == requested` OR `provenance.origin_source == requested` (to catch nodes created from the file even if their canonical_type differs).
- Projections must return a `version` or `etag` so UI can cache and know when to re-request.

## Session-note Import Flow (example)

1. User imports a markdown session note.
2. Ingest pipeline parses markdown and calls `upsert_node`/`upsert_edge` on the Canonical Graph Service. For the primary document, ensure a node with `canonical_type=source_document` and `source_file` is created (adapter ensures canonical type is assigned when a document primary is detected).
3. Ingest emits `source_file_added` with `source_file` and affected node ids.
4. Projection Service invalidates any cache for `by_source_file(source_file)` and computes updated file/heading projections.
5. UI, which subscribes to the event bus, pre-selects the file dropdown (uses the `source_file` value emitted) and fetches `get_file_projection(source_file)`.

## Backwards Compatibility & Adapters

- Provide adapter code that maps legacy `node_type` and other historical properties into the canonical model. This adapter runs during ingestion and during one-time migrations.
- Keep a compatibility layer in Projection Service to accept old node shapes (helps during staged rollouts).

## Testing & Validation

- Unit tests for adapters (legacy -> canonical mapping).
- Integration tests for ingestion -> canonical store -> projection returns expected nodes for a sample session-note file.
- UI contract tests: mock Projection Service responses and verify Streamlit views render the expected dropdown and graph.

## Migration Plan

1. Implement Canonical Graph Service with adapter and projection API behind a feature flag.
2. Wire ingestion to write to the Canonical Graph Service while still maintaining previous side-effects (dual-write) for a short period.
3. Update Projection Service and UI to call the projection API.
4. Run integration tests and migrate data/transform old nodes to canonical representations.
5. Remove legacy code once coverage and confidence are high.

## Metrics & Observability

- Track `projection_latency`, `projection_cache_hit_rate`, number of `source_file_added` events, and `missing_projection_results` (when UI requests a file but projection returns empty).

## Roadmap / Next Steps

1. Implement a minimal Canonical Graph Service and Projection API (Python module with an in-memory store + SQLite persistence).
2. Add ingest-time canonicalization adapters for session notes and existing graph producers.
3. Replace direct graph reads in `graphviz_rendering.py` and `streamlit_app.py` with Projection API calls.
4. Add contract tests and a small e2e for session-note imports that exercises the full flow.

## Appendix: Implementation Notes

- Use normalized paths for `source_file` equality checks and include helper `normalize_source_file(path: str) -> str`.
- Avoid relying on `node_type` string equality in view logic; instead use canonical types and `provenance` fields.
- Provide `projection etag` values to allow the UI to request only when changed.

---

Document created to guide decoupling work and to act as the implementation blueprint for the team.
