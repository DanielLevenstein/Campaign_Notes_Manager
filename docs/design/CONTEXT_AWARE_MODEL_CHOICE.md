# Context-Aware Embeddings Model Choice

## Components

1) An extraction model which extracts likely nodes. 
2) A classification model, which can be used to determine a node type based on the information in normalization.json
3) A second classification model which can be used to determine an edge connection type when heading elements are removed from visible graphs. 

Context info currently stored in normalization.json should slowly be moved to these three models. 

## Purpose

The context-aware edge pipeline needs a Python tool that can learn from `config/extraction/normalization.json` and use that knowledge to create graph nodes and connection types. The desired model should infer node types, attribute types, and edge types from evidence text instead of relying only on exact keyword matches.

This is broader than edge-type classification. The model-choice decision should support a pipeline that can:

- Identify entity mentions that should become graph nodes.
- Classify node types such as `character`, `place`, `group`, `family`, `artifact`, `attribute`, `note`, and `source_document`.
- Reject generic or invalid candidates using configured stoplists and unknown-value handling.
- Canonicalize known names and family names from `session_entity_normalization`.
- Classify relationship edges from `relationship_rules`.
- Preserve source-backed evidence and confidence for every model-created graph fact.

The model should learn the semantic intent of `normalization.json`, but deterministic normalization should still enforce schema constraints, precedence rules, aliases, known-name overrides, and safe fallbacks.

The current configured relationship types are:

| Type | Label | Sentiment | Seed keywords |
| --- | --- | --- | --- |
| `betrayer` | Betrayer | hostile | betray, betrayed, betraying |
| `mentor` | Former mentor | complicated | former mentor, trained, teacher, mentor |
| `family` | Family | positive | sister, brother, mother, father, parent, child, family |
| `client` | Client | positive | client, customer, patron, regular |
| `rival` | Rivals | hostile | rival, competitor |
| `enemy` | Enemy | hostile | enemy, foe, hates, opposes, against |
| `ally` | Ally | positive | ally, companion, friend, trusted |
| `lover` | Lover | positive | lover, beloved, romance, romantic |

The tool should classify evidence spans such as sentences or clauses into one of those configured edge types, or return a low-confidence fallback such as `mentioned_with` when the evidence does not support a stronger relation.

## Target Pipeline

Treat `normalization.json` as both a schema source and a weak-supervision source.

The pipeline should compile the config into three artifacts:

1. **Node schema**: valid node labels, type precedence, suffix hints, canonical names, rejected names, generic entities, and place/artifact/group/family vocabulary.
2. **Edge schema**: valid relationship labels from `relationship_rules`, sentiment, keywords, and generated natural-language descriptions.
3. **Training/evaluation fixtures**: synthetic and hand-authored examples that convert current config entries into model inputs and expected graph outputs.

Runtime flow:

1. Parse source text into heading-aware evidence spans.
2. Generate entity candidates with deterministic extractors and/or GLiNER.
3. Classify each candidate into a configured node type.
4. Canonicalize or reject candidates using `normalization.json`.
5. Build candidate entity pairs from shared evidence spans and heading context.
6. Classify each pair into a configured edge type, or fall back to `mentioned_with`.
7. Persist nodes and edges with evidence, source line, classifier version, score, and normalization schema version.

## Smallest-Impact Path

The safest first implementation should not replace the existing connection workflow. A lot of useful work already exists in the heading-mediated graph builder, and the current design intentionally connects nodes through source documents and Markdown headings before projection hides or removes those headings.

The smallest-impact change is:

1. Keep the existing extraction and heading-connection pipeline.
2. Treat the produced graph as the candidate graph.
3. Use Sentence Transformers to classify existing nodes into configured node types when deterministic rules are uncertain.
4. Use heading context, evidence text, and neighboring nodes as classifier input.
5. Store model output as enrichment metadata, not as the only source of truth.
6. Let existing projection code continue removing headings, but prefer enriched node and edge metadata when choosing which semantic connections survive.

This keeps the blast radius small because the model does not decide which mentions exist. It only improves the graph facts that the current system already knows how to create.

### Node Type Classification

For each existing node, build a classification input from:

- Node display name.
- Current node type, if any.
- Source file and heading stack.
- Evidence sentence or heading text.
- Adjacent source-document, heading, and entity nodes.
- Config-derived label descriptions from `normalization.json`.

Example:

```text
Candidate node: Moon Gate
Current type: entity
Evidence: The Moon Gate hummed softly beneath the old tower.
Heading context: Atlantia Lore > Old Roads
Adjacent nodes: Old Tower, Atlantia
Choose one configured type: character, place, group, family, artifact, attribute, entity
```

The classifier can promote `Moon Gate` from `entity` to `place` only when the score clears a threshold and beats the next candidate by a margin. Otherwise the existing deterministic type remains.

### Connection Type Classification

After node typing improves, classify existing graph paths rather than inventing new relationship pairs immediately.

For each heading-mediated path such as:

```text
Heading -> Character
Heading -> Group
```

derive a candidate semantic edge:

```text
Character -> Group
```

Then use the shared heading context and evidence sentence to decide whether the edge should remain a generic `mentioned_with` connection or become a configured relationship type such as `ally`, `enemy`, `family`, or `mentor`.

This matches the current projection design: headings gather evidence first, then projection removes headings while preserving useful semantic connections.

### Long-Term Risk

This approach could backfire if the project lets projection-time enrichment become the real graph model. The long-term risk is a split-brain graph:

- The canonical graph says nodes are connected through headings.
- The rendered graph shows semantic edges inferred after heading removal.
- Bugs become harder to debug because source evidence, canonical storage, and visual projection disagree.

To avoid that, model-created classifications should be persisted as canonical graph metadata as soon as they are trusted:

- `classified_node_type`
- `classification_score`
- `classification_model`
- `classification_schema_version`
- `semantic_relation_type`
- `semantic_relation_score`
- `evidence_span`
- `derived_from_heading_path`

The first implementation can enrich existing nodes and connections. The long-term implementation should promote accepted enrichments into the canonical graph service before projection.

## Recommendation

Use `sentence-transformers` plus `scikit-learn` as the first controllable implementation path, starting with enrichment of existing graph nodes and heading-mediated connections. Run GLiNER/GLiNER2 later as a serious spike for the broader node-and-edge extraction goal.

This gives the project a practical middle path:

- `sentence-transformers` can classify existing node and edge candidates against label descriptions generated from `normalization.json`.
- `scikit-learn` can provide the fast deterministic baseline, evaluation harness, and future supervised classifier.
- GLiNER/GLiNER2 may be a better long-term fit if the project eventually wants model-driven schema extraction from campaign prose.
- Deterministic config rules remain the guardrails for canonicalization, invalid candidates, type precedence, and low-confidence fallbacks.
- The graph pipeline avoids committing immediately to a hosted LLM or a large local generation model.

GLiNER should be evaluated as the best alternative if the project wants one model to handle entity and relation extraction together. The risk is that the original GLiNER family is strongest at entity extraction, while edge typing needs relation classification between already-normalized graph entities. GLiNER2 looks closer to the desired schema-driven relation workflow, but it is newer and should be treated as a spike until local reliability is proven.

## Option 1: Sentence Transformers

Sources:

- [Sentence Transformers semantic textual similarity documentation](https://www.sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html)
- [Sentence Transformers pretrained model guidance](https://github.com/huggingface/sentence-transformers/blob/main/docs/sentence_transformer/pretrained_models.md)

### Fit

`sentence-transformers` is the strongest fit for the first controllable version of automatic node and edge classification. It embeds evidence spans and label descriptions into the same vector space, then uses cosine similarity or dot product to rank configured types.

Example classification text for the `ally` rule:

```text
Relationship type: Ally.
Sentiment: positive.
Evidence means one entity is a friend, trusted companion, or ally of the other.
Seed terms: ally, companion, friend, trusted.
```

### Pros

- Good semantic matching without requiring a large labeled project dataset.
- Works well with the current small relationship vocabulary.
- Easy to combine with deterministic keyword overrides.
- Produces numeric scores that can drive confidence thresholds and review queues.
- Can run fully local after model download.
- Supports future fine-tuning if the project accumulates accepted/rejected edge examples.

### Cons

- Requires adding a new dependency and model artifact.
- Similarity scores are not calibrated probabilities.
- Short evidence spans can be ambiguous without entity-pair context.
- Label descriptions must be carefully written and tested.
- Model choice matters; MTEB leaderboard quality does not guarantee good lore-relationship classification.

### Suggested Use

Use this as the primary candidate for `src/graph/graph_fact_classifier.py`.

Start with a compact model such as a MiniLM or MPNet Sentence Transformer, then evaluate on fixture spans from character sheets and session notes. Keep the model name configurable so larger or domain-tuned models can be tested later.

Use separate label-description sets for:

- Node type classification: `character`, `place`, `group`, `family`, `artifact`, `attribute`, and fallback `entity`.
- Attribute classification: traits, motivations, race/class/family values, and other sheet-derived facts.
- Edge type classification: configured `relationship_rules` plus `mentioned_with`.

## Option 2: scikit-learn

Sources:

- [scikit-learn `TfidfVectorizer` documentation](https://sklearn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
- [scikit-learn text feature extraction guide](https://scikit-learn.sourceforge.net/stable/modules/feature_extraction.html)

### Fit

`scikit-learn` is already in `requirements.txt`, so it is the lowest-friction option. It can support TF-IDF similarity against rule descriptions, or a supervised classifier once enough labeled graph-fact examples exist.

### Pros

- Already available in the project dependencies.
- Very fast and deterministic.
- Easy to test in small unit fixtures.
- Good baseline for keyword-heavy relationship types like `family`, `enemy`, and `client`.
- Does not require heavyweight model downloads.
- Excellent for evaluation tooling, confusion matrices, threshold sweeps, and regression metrics.

### Cons

- Weak semantic generalization compared with embedding models.
- Sparse lexical matching will miss paraphrases such as "raised her after the fire" for `family`.
- Needs labeled data for supervised classification.
- TF-IDF similarity over the current seed keywords may behave like a softer keyword matcher rather than true context awareness.

### Suggested Use

Use as the baseline and test harness even if another tool becomes the primary classifier.

Recommended roles:

- A no-download fallback classifier.
- A regression benchmark for semantic models.
- A supervised classifier once reviewer-approved node and edge labels are collected.

## Option 3: GLiNER and GLiNER2

Sources:

- [GLiNER GitHub project](https://github.com/urchade/GLiNER)
- [GLiNER documentation](https://urchade.github.io/GLiNER/)
- [GLiNER2 GitHub project](https://github.com/fastino-ai/GLiNER2)

### Fit

GLiNER is a lightweight information-extraction model family built around flexible labels. The original GLiNER project is centered on zero-shot named entity recognition and also documents joint entity and relation extraction. GLiNER2 is more directly relevant to this design because it exposes schema-based extraction for entities, classification, structured data, and relations.

For this project, GLiNER should be tested in two modes:

1. Entity extraction support: predict `character`, `place`, `group`, `artifact`, and `family` candidates from evidence spans.
2. Relation extraction support: predict configured relationship names such as `mentor`, `family`, `enemy`, and `ally` as directional tuples between detected or supplied entities.

### Pros

- Strong fit for information extraction rather than generic text similarity.
- Can potentially extract entities and edge types in one pass.
- Supports flexible labels, which maps well to `normalization.json`.
- Designed for local execution and smaller hardware compared with LLMs.
- GLiNER2's schema-driven relation extraction matches the desired closed-vocabulary edge typing workflow.
- Could reduce custom glue code if relation extraction proves reliable.

### Cons

- Original GLiNER is primarily an NER tool; relation extraction support may require newer models or specialized APIs.
- GLiNER2 is newer and should be validated carefully before becoming a core dependency.
- Adds model-management complexity and likely pulls in `torch`/`transformers` for local inference.
- May extract relationship tuples that conflict with the project's existing canonical entity ids unless constrained by known entities.
- Needs fixture-based evaluation on campaign prose, especially invented names and indirect narrative relationships.
- May be more complex than needed for a first edge-type classifier if candidate entity pairs are already known.

### Suggested Use

Run a focused spike after the Sentence Transformers baseline:

- Give GLiNER/GLiNER2 the same `edge_type_examples.json` fixture.
- Prefer schemas generated from `normalization.json` rather than free-form labels.
- Test whether it can classify supplied entity pairs, not only discover new entities.
- Compare false positives on incidental co-mentions against the Sentence Transformers threshold-and-margin approach.

If GLiNER2 can reliably return closed-vocabulary relation tuples with evidence spans, it may become the best long-term extraction tool. If it struggles with supplied canonical entities or local performance, keep it as an optional extractor and use embeddings for edge-type ranking.

## Option 4: Hugging Face Transformers

Sources:

- [Hugging Face Transformers pipelines documentation](https://huggingface.co/docs/transformers/main_classes/pipelines)

### Fit

`transformers` can run zero-shot classification using NLI models, or can host a fine-tuned text classifier. For edge typing, each evidence span can be classified against candidate labels generated from `normalization.json`.

### Pros

- Strong zero-shot classification path without project-specific training data.
- Candidate labels can be built dynamically from `normalization.json`.
- Can later move from zero-shot NLI to a fine-tuned classifier using the same library.
- Broad model ecosystem and deployment options.
- Better direct classification semantics than pure embedding similarity for some labels.

### Cons

- Heavier dependency and runtime footprint than `sentence-transformers`.
- Zero-shot NLI inference is often slower than embedding similarity.
- Model downloads and CPU performance may be painful for a Streamlit workflow.
- Scores still need calibration against project fixtures.
- More moving parts for local/offline reproducibility.

### Suggested Use

Use for a second-pass classifier or experiment branch when Sentence Transformers cannot distinguish close labels such as `rival`, `enemy`, and `betrayer`.

Do not make this the first production dependency unless evaluation shows a clear quality gain over Sentence Transformers.

## Option 5: spaCy

Sources:

- [spaCy rule-based matching documentation](https://spacy.io/usage/rule-based-matching)
- [spaCy Matcher API documentation](https://spacy.io/api/matcher/)

### Fit

`spaCy` is best suited for the deterministic half of the pipeline: tokenization, sentence boundaries, entity spans, dependency-aware patterns, and high-precision relationship rules. It can also train text categorization models, but its strongest immediate value is robust linguistic preprocessing and rule bootstrapping.

### Pros

- Excellent tokenization and sentence segmentation for evidence-span creation.
- Rule matchers are more maintainable than raw regex for relationship phrases.
- Can combine rule-based and statistical pipeline components.
- Useful for dependency patterns such as "X trained Y" or "X is Y's father".
- Good path for bootstrapping labeled examples before training another classifier.

### Cons

- Not primarily an embeddings model choice by itself.
- Requires adding spaCy and a language pipeline dependency.
- Relationship classification still needs custom rules, a trained component, or another model.
- Fantasy names and invented entities may need project-specific handling.

### Suggested Use

Use as a preprocessing and high-precision rule layer if sentence boundary detection or grammatical relation patterns become brittle.

For the first automatic classifier, spaCy should support the model rather than replace it.

## Option 6: LangChain Structured Output with a Local or Hosted LLM

Sources:

- [LangChain structured output documentation](https://docs.langchain.com/oss/python/langchain/structured-output)
- [LangChain model structured output documentation](https://docs.langchain.com/oss/python/langchain/models)

### Fit

LangChain can ask a language model to return a structured edge classification object validated by Pydantic, TypedDict, or JSON Schema. This is the most flexible option for nuanced narrative relationships, especially when evidence requires inference beyond a sentence-level keyword or embedding match.

### Pros

- Best at interpreting nuanced prose and implicit relationships.
- Can return structured fields such as `edge_type`, `confidence`, `rationale`, and `evidence_span`.
- Can use the configured relationship types as a closed enum.
- Integrates cleanly with Pydantic validation and retry handling.
- Compatible with a future LangGraph extraction workflow.

### Cons

- More expensive and less deterministic than embedding or lexical approaches.
- Requires careful prompt-injection boundaries because source lore is untrusted input.
- Hosted models add privacy, network, and cost concerns.
- Local LLMs add model-management and performance concerns.
- Harder to regression-test than a pure classifier.

### Suggested Use

Use as an optional review assistant or low-confidence repair path, not the default classifier.

The project already has local `llama` integration for rewrite workflows, but edge detection should remain smaller, faster, and easier to test unless fixtures prove that embeddings cannot reach acceptable quality.

## Comparison Summary

| Rank | Tool | Best Role | Implementation Risk | Runtime Cost | Recommended Now |
| --- | --- | --- | --- | --- | --- |
| 1 | `sentence-transformers` | Primary semantic graph-fact classifier | Medium | Medium | Yes |
| 2 | `scikit-learn` | Baseline, fallback, evaluation harness | Low | Low | Yes |
| 3 | GLiNER / GLiNER2 | Schema-driven entity and relation extraction spike | Medium-high | Medium | Spike now |
| 4 | `transformers` | Zero-shot or fine-tuned classifier experiment | Medium-high | Medium-high | Later |
| 5 | `spaCy` | Sentence/entity preprocessing and high-precision rules | Medium | Low-medium | Later/supporting |
| 6 | LangChain structured output | Ambiguous-case review or LLM extraction workflow | High | Variable | Optional |

## Acceptance Criteria for Tool Selection

The chosen tool should pass these checks before becoming part of the canonical graph pipeline:

- Given fixture evidence spans, it correctly identifies configured node types and configured `relationship_rules` types that have direct support.
- It can enrich existing graph nodes without changing node ids, deleting nodes, or bypassing current heading-context extraction.
- It can classify semantic edges derived from existing heading-mediated paths before any new model-created relationship pair generation is enabled.
- It rejects or downgrades configured `unknown_values`, `generic_entities`, `non_name_words`, and low-confidence incidental mentions.
- It returns fallback node type `entity` or fallback edge type `mentioned_with` when evidence does not support a more specific configured type.
- It records the selected node/edge type, score, model/tool name, model version, evidence span, and configured rule version.
- It remains deterministic enough for unit tests by using fixed model names, thresholds, and fixture inputs.
- It supports offline execution after dependencies and model artifacts are installed.
- It does not overwrite deterministic high-confidence rules from `normalization.json`.

## Proposed Next Step

Create small evaluation fixtures before implementing the production classifier:

```text
tests/fixtures/node_type_examples.json
tests/fixtures/edge_type_examples.json
```

Each node example should include:

```json
{
  "evidence": "The Moon Gate hummed softly beneath the old tower.",
  "candidate": "Moon Gate",
  "expected_type": "place",
  "expected_rejected": false
}
```

Each edge example should include:

```json
{
  "source_id": "character:jory_ravenmark",
  "target_id": "character:orin_nightbloom",
  "evidence": "Orin trained Jory before leaving the academy.",
  "expected_type": "mentor",
  "expected_fallback_allowed": false
}
```

Then compare:

1. Current keyword matching.
2. `scikit-learn` TF-IDF similarity.
3. `sentence-transformers` semantic similarity.
4. GLiNER/GLiNER2 schema-based relation extraction.

Promote Sentence Transformers only if it beats the deterministic baseline on paraphrases without creating unacceptable false positives on incidental co-mentions. Promote GLiNER/GLiNER2 instead only if it returns reliable closed-vocabulary relation tuples for known entity pairs and preserves evidence spans cleanly enough for graph provenance.
