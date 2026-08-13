# Context-Aware Model Migration

## Purpose

This document defines the migration path for v1.4.0 Context Aware Edges. It uses the `ROADMAP.md` plan as the source of truth and turns it into a staged implementation strategy that preserves the current heading-mediated graph design while slowly introducing model-backed node and edge classification.

The migration should avoid a full graph rewrite. The current graph builder already provides valuable structure:

- Source document and Markdown heading context.
- Stable graph nodes and edges.
- Deterministic normalization from `config/extraction/normalization.json`.
- Projection behavior that can hide headings while still rendering useful graphs.
- Existing test coverage around Graphviz views, headings, node typing, and session-note import.

The model migration should enrich this design before replacing any part of it.

## Migration Principle

Use models as advisory enrichment first, canonical truth later.

The first production path should:

1. Preserve current extraction behavior.
2. Preserve current node ids and edge ids where possible.
3. Add occurrence and classifier metadata to existing graph facts.
4. Use classifier output only when confidence and tests support it.
5. Keep deterministic rules as high-precision overrides and safe fallbacks.
6. Feature-flag any behavior that changes visible graph output.

The long-term goal is to move context currently encoded in `normalization.json` into three model-backed capabilities:

1. An extraction model that identifies likely nodes.
2. A node classification model trained or configured from `normalization.json`.
3. An edge classification model used when heading elements are removed from visible graphs.

## Current Roadmap

The v1.4.0 roadmap has four model-related phases:

1. **Phase 1.1 Context Aware Edges**
   - Create and persist an occurrence model.
   - Move session-note relationships onto occurrences.
   - Replace hidden-heading bridge creation with visible-anchor selection from occurrence metadata.

2. **Phase 1.2 Context Aware Node Type Detection**
   - Build classifier labels from `normalization.json`.
   - Add classifier-backed node type enrichment for existing nodes.
   - Preserve deterministic typing as override/fallback.
   - Persist node classification metadata.
   - Promote classifier type only after confidence and fixture validation.

3. **Phase 1.3 Context Aware Edge Type Detection**
   - Derive candidate semantic edges from existing heading-mediated paths.
   - Use evidence, heading context, and node types to classify edge connection type.
   - Persist semantic relation metadata separately from render-only helper edges.
   - Use classified edge metadata when headings are hidden from visible graphs.

4. **Phase 1.4 GLiNER Node Extraction**
   - Add GLiNER extraction behind a feature flag.
   - Compare GLiNER candidates against current non-heading extraction.
   - Persist GLiNER confidence and evidence metadata.
   - Replace current non-heading extraction only after fixture and e2e parity is proven.

## Data Contracts

### Occurrence Metadata

Every model-backed decision must be traceable to source text. The occurrence model should include:

| Field | Purpose |
| --- | --- |
| `occurrence_id` | Stable id derived from source file, source line, entity id, and occurrence index. |
| `source_file` | Repo-relative source file path. |
| `source_line` | 1-based line number for the evidence. |
| `evidence` | Sentence, clause, heading text, or table row that supports the fact. |
| `heading_stack` | Ordered H1-H6 heading records active at the evidence line. |
| `context_anchor_id` | Nearest heading id, or source document id if no heading exists. |
| `entity_id` | Canonical graph node id. |
| `entity_name` | Display name at extraction time. |
| `entity_type` | Current canonical node type before model enrichment. |
| `extraction_source` | Deterministic rule, parser, current extractor, GLiNER, or other source. |
| `confidence` | Confidence value or enum from the extractor/classifier. |

### Node Classification Metadata

Classifier output for nodes should be stored separately from the canonical node type at first:

| Field | Purpose |
| --- | --- |
| `classified_node_type` | Model-predicted type such as `place`, `group`, `artifact`, or `character`. |
| `classification_score` | Top model score. |
| `classification_margin` | Difference between top score and runner-up. |
| `classification_model` | Model family and exact model id. |
| `classification_schema_version` | `normalization.json` schema version used to build labels. |
| `classification_input_hash` | Hash of the text/context used for the model call. |
| `classification_evidence` | Evidence span used for the prediction. |
| `classification_status` | `candidate`, `accepted`, `rejected`, or `fallback`. |

### Edge Classification Metadata

Classified semantic edges should be persisted separately from render-only Graphviz helper edges:

| Field | Purpose |
| --- | --- |
| `semantic_relation_type` | Model-predicted relation such as `ally`, `enemy`, `family`, or `mentor`. |
| `semantic_relation_score` | Top model score. |
| `semantic_relation_margin` | Difference between top score and runner-up. |
| `semantic_relation_model` | Model family and exact model id. |
| `semantic_relation_schema_version` | `normalization.json` schema version used to build labels. |
| `derived_from_heading_path` | Source heading path or context anchor path that produced the candidate semantic edge. |
| `semantic_relation_evidence` | Evidence span used for classification. |
| `semantic_relation_status` | `candidate`, `accepted`, `rejected`, or `fallback`. |

## Phase 1.1 Migration: Context-Aware Occurrences

### Goal

Create the provenance layer needed for safe model-backed classification.

### Implementation Steps

1. Add `src/graph/context_edges.py`.
   - Define `GraphOccurrence`, `HeadingContext`, and `ContextAwareEdge`.
   - Add heading-stack parsing with line numbers.
   - Add occurrence-to-context-edge derivation.

2. Move session-note derived relationships onto the occurrence model.
   - Keep current dict outputs behind compatibility adapters.
   - Attach source file, line, evidence, heading stack, and context anchor to each derived relationship.

3. Persist occurrence metadata in canonical graph edges.
   - Store occurrence metadata in edge provenance/properties.
   - Do not store render-only Graphviz helper edges.
   - Keep updates source-scoped so re-importing a file replaces that file's graph facts idempotently.

4. Replace hidden-heading bridges with visible-anchor selection.
   - When a heading is hidden, choose the nearest visible ancestor from occurrence metadata.
   - If no heading is visible, preserve semantic direct edges and keep hidden heading labels as provenance.

### Entry Criteria

- Existing graph persistence and projection tests pass.
- Current session-note import behavior is understood and covered by fixtures.
- `CONTEXT_AWARE_EDGES_DESIGN.md` is the accepted design reference.

### Exit Criteria

- Occurrences include source line, evidence, heading stack, and context anchor.
- Hidden-heading graph projection uses occurrence metadata instead of opportunistic bridge creation.
- Re-running ingestion for the same source does not duplicate nodes or edges.
- Graphviz helper edges remain excluded from canonical persistence.

### Tests

- Unit tests for heading-stack parsing.
- Unit tests for occurrence ids and context anchors.
- Unit tests for hidden-heading visible-anchor selection.
- Regression tests for group evidence under multiple months.
- Regression tests for `Moon Gate` and `Indigo Cult` behavior.

## Phase 1.2 Migration: Node Type Classification

### Goal

Use Sentence Transformers to classify existing graph nodes into configured node types without replacing current extraction.

### Implementation Steps

1. Build label descriptions from `normalization.json`.
   - Include type precedence.
   - Include place, group, artifact, and family suffix hints.
   - Include canonical names and rejected/generic names as guardrails.
   - Generate natural-language descriptions for labels such as `place`, `group`, `artifact`, `family`, `character`, and fallback `entity`.

2. Add `src/graph/graph_fact_classifier.py`.
   - Define a small classifier interface that can be backed by Sentence Transformers.
   - Accept candidate text, context text, and valid labels.
   - Return top label, score, margin, model id, and label schema version.

3. Add classifier-backed enrichment for existing nodes.
   - Classify only nodes that are uncertain or weakly typed at first.
   - Use node name, evidence span, heading stack, source file, current type, and neighbors as input.
   - Persist classification metadata separately from canonical node type.

4. Preserve deterministic overrides.
   - Known character and place names win over model output.
   - Rejected/generic names cannot be promoted by model output alone.
   - Type precedence resolves ties.
   - Low score or low margin falls back to existing type.

5. Promote classifier output only after validation.
   - Add thresholds to config.
   - Start in read-only/enrichment mode.
   - Feature-flag promotion into canonical node type.

### Entry Criteria

- Phase 1.1 occurrence metadata exists.
- `sentence-transformers` is installed in `requirements.txt`.
- A no-model fallback path exists for tests and environments without downloaded model artifacts.

### Exit Criteria

- Existing graph nodes can be enriched with classifier metadata.
- No node ids change.
- No nodes are deleted by the classifier.
- Deterministic typing remains authoritative when confidence is high.
- Classifier decisions are reproducible for fixed model id, schema version, and input text.

### Tests

- Fixture-backed tests for `place`, `group`, `artifact`, `family`, `character`, and fallback `entity`.
- Negative tests for generic entities and non-name words.
- Regression tests for `Moon Gate` becoming place only when threshold and margin pass.
- Regression tests for `Indigo Cult` not becoming both group and character.
- Snapshot tests for persisted classification metadata.

## Phase 1.3 Migration: Edge Type Classification

### Goal

Use model-backed classification to decide which semantic connection should survive when heading elements are removed from visible graphs.

### Implementation Steps

1. Derive candidate semantic edges from existing heading-mediated paths.
   - For a shared heading or source context, inspect connected semantic nodes.
   - Prefer high-value pairs such as character/group, character/place, group/place, artifact/character, and artifact/place.
   - Do not create arbitrary all-to-all edges without evidence.

2. Build edge label descriptions from `relationship_rules`.
   - Use type, label, sentiment, and keywords.
   - Add fallback `mentioned_with`.
   - Include direction guidance where applicable.

3. Classify candidate edges.
   - Use source node name/type, target node name/type, evidence span, heading context, and neighboring nodes.
   - Return relation type, score, margin, model id, and schema version.
   - Fall back to `mentioned_with` when no label clears threshold and margin.

4. Persist semantic relation metadata.
   - Store classification metadata on canonical edges or edge provenance.
   - Keep this separate from render-only helper edges.
   - Record `derived_from_heading_path` so every semantic edge can be traced back to heading evidence.

5. Use classified edge metadata in projection.
   - When headings are hidden, prefer accepted semantic relation metadata.
   - If metadata is missing or low confidence, use the visible-anchor occurrence path from Phase 1.1.

### Entry Criteria

- Phase 1.1 visible-anchor selection is implemented.
- Phase 1.2 node typing metadata is available for candidate edge inputs.
- Edge relation labels are generated from `normalization.json`.

### Exit Criteria

- Heading-hidden graph views can use accepted semantic relation metadata.
- Low-confidence relation classification falls back to `mentioned_with`.
- Render-only helper edges remain out of canonical storage.
- Every classified edge has evidence and a derived heading path.

### Tests

- Fixture-backed edge examples for `ally`, `enemy`, `family`, `mentor`, `rival`, `client`, `lover`, and `betrayer`.
- Negative tests for incidental co-mentions.
- Regression tests that a generic `Session Notes` edge does not win over a more specific month/session context.
- Projection tests for heading-hidden views.

## Phase 1.4 Migration: GLiNER Node Extraction

### Goal

Evaluate GLiNER as a replacement or supplement for current non-heading-based node extraction without risking existing graph behavior.

### Implementation Steps

1. Add GLiNER behind a feature flag.
   - Default off.
   - Keep current extractor as the production path.
   - Record model id, threshold, and schema version.

2. Run GLiNER in comparison mode.
   - Feed the same evidence spans used by the current extractor.
   - Compare GLiNER candidates against current non-heading extraction.
   - Store comparison output in test artifacts or debug metadata, not canonical graph facts.

3. Persist GLiNER confidence and evidence metadata when enabled.
   - Capture candidate text, predicted label, confidence, evidence span, and source line.
   - Do not create canonical nodes unless the feature flag explicitly allows it.

4. Promote GLiNER only after parity.
   - Require fixture parity against current extraction.
   - Require e2e graph view parity where no user-visible behavior should change.
   - Require better recall on known missed-node fixtures.

### Entry Criteria

- Phases 1.1 through 1.3 are stable.
- Node and edge classifier metadata can already describe existing graph facts.
- GLiNER dependency and model artifact strategy is understood.

### Exit Criteria

- GLiNER comparison mode reports precision/recall against fixtures.
- GLiNER-created candidates preserve source-backed evidence.
- Current extraction remains available as rollback.
- GLiNER replacement is feature-flagged and can be disabled without data migration.

### Tests

- Candidate extraction comparison tests.
- Fixture parity tests against existing session notes and lore files.
- E2E tests for graph views with GLiNER disabled and enabled.
- Regression tests that GLiNER does not create duplicate canonical nodes for known names.

## Rollout Strategy

### Stage 1: Metadata Only

Write occurrence and classifier metadata, but do not change rendered graph behavior.

Success signal:

- Metadata is stable across repeated ingestion.
- No visible graph regressions.
- Existing tests pass.

### Stage 2: Feature-Flagged Projection Use

Allow selected graph projections to use accepted classifier metadata.

Success signal:

- Heading-hidden views improve without breaking heading-visible views.
- Low-confidence classifications fall back to current behavior.
- Users can disable model-backed projection.

### Stage 3: Canonical Promotion

Promote accepted node and edge classifications into canonical graph metadata.

Success signal:

- Accepted classifications survive graph regeneration.
- Projection no longer needs to infer semantic facts ad hoc.
- Review decisions can override model output.

### Stage 4: Extractor Replacement Spike

Evaluate GLiNER as a replacement for current non-heading extraction.

Success signal:

- GLiNER improves recall without unacceptable false positives.
- GLiNER preserves evidence and canonical identity rules.
- Current extraction remains a rollback path.

## Rollback Strategy

Every phase should be reversible:

- Disable classifier promotion and keep metadata only.
- Ignore model metadata in projection.
- Fall back from semantic edges to visible-anchor occurrence paths.
- Disable GLiNER and return to current extraction.
- Rebuild graph data from source Markdown and deterministic normalization.

No migration step should require destructive changes to Markdown source files or review decisions.

## Risks

### Split-Brain Graph

Risk: projection shows semantic connections that canonical graph storage does not understand.

Mitigation: persist model-created classifications as canonical metadata once trusted, and always store evidence plus `derived_from_heading_path`.

### Model Overreach

Risk: the classifier promotes incidental mentions or generic words into real graph facts.

Mitigation: keep deterministic rejection lists, thresholds, margins, and review workflow ahead of promotion.

### Unstable Model Artifacts

Risk: model downloads, model versions, or dependency updates change graph output.

Mitigation: pin model ids, record model version metadata, hash classifier inputs, and keep fixture snapshots.

### GLiNER Recall/Precision Tradeoff

Risk: GLiNER finds more candidates but creates duplicate or low-value nodes.

Mitigation: run GLiNER in comparison mode first, require parity tests, and keep canonicalization rules authoritative.

## Release Gate

v1.4.0 should not be considered complete until:

- Occurrence metadata is persisted and used for hidden-heading projection.
- Node classification enrichment exists for current graph nodes.
- Edge classification enrichment exists for heading-mediated semantic edges.
- All model-backed facts preserve source evidence, scores, model ids, and schema versions.
- GLiNER extraction is either feature-flagged comparison-only or has passed fixture/e2e parity.
- Existing Graphviz and session-note tests pass without requiring model downloads in default test mode.
