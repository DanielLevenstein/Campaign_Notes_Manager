# Group Connection Bug Context Transfer

## Date
2026-08-02

## Status
Deferred to the next graph code version.

This issue is too tangled in the current projection/deduplication/rendering flow to fix safely without risking regressions. The notes below are a transfer packet for the next implementation pass.

## User-Visible Bug
When Session Notes directory graph headings are hidden, group nodes such as `Ignis Cult` do not reconnect to the visible month/session context the user expects.

Expected behavior:

- When lower-level headings are hidden, the group node should remain connected to each visible ancestor heading that contains evidence for that group.
- In the screenshots, `Ignis Cult` should connect to visible month headings such as `October 2023`, `February 2023`, etc.
- The group should not fall back to generic `Session Notes` group-to-character bridges.

Observed behavior:

- `Ignis Cult` appears as a group node.
- Some expected ancestor context edges are missing.
- A stale-looking edge such as `Ignis Cult -> Mr Light` labeled `Session Notes` appears after headings are hidden.

## Screenshot Evidence
Screenshots provided by the user:

- `docs/screenshots/group_connection_bug1.png`
- `docs/screenshots/group_connection_bug2.png`

Important interpretation from the user:

- The `Ignis Cult` vs `Indigo Cult` name difference is caused by a rename in the test harness.
- The name is not the bug.
- The actual bug is how group connections are handled when headings are removed.

## Current-Code Risk
The current code path mixes several responsibilities:

- Markdown heading parsing
- semantic heading/entity merging
- source-document root hiding
- hidden-heading bridge creation
- edge deduplication
- Graphviz column/rank layout
- relationship row generation

Because these steps mutate or project edges in sequence, fixes in one layer can produce plausible-looking but wrong edges in another layer. The bug likely needs a clearer intermediate graph model rather than more local patching.

## Investigation Findings
The likely culprit is ordering and deduplication around source-document hiding and heading hiding.

Specific suspicion:

- Source-document hiding can bridge visible parents and children through a hidden `source_document` root.
- If group/source edges already exist, that bridge may create generic edges labeled with the source document name, e.g. `Session Notes`.
- Later heading hiding or edge prominence/deduplication may preserve that generic edge instead of the more specific month/session-context edge.

The screenshot showing:

```text
Ignis Cult -> Mr Light [Session Notes]
```

strongly suggests source-root bridging is winning or surviving where heading-context projection should be authoritative.

## What Was Tried
The attempted current-version direction was:

1. Split source-document edges by evidence location so one combined group edge can project to multiple headings.
2. Merge semantic Markdown group headings with canonical group nodes.
3. Prevent source-document hiding from creating generic bridges when heading children exist.
4. Add regressions around:
   - group evidence in multiple hidden sections
   - stale source-document group bridges
   - capitalized cult group extraction

These changes made targeted tests pass, but the user correctly identified that the real UI issue is more subtle and likely not fixed by local patches in the current architecture.

## Tests/Fixtures Touched During Investigation
Relevant test file:

- `tests/test_graphviz_rendering.py`

Useful intended regression shape:

```markdown
# Session Notes
## October 2023
### Session 7
Mr Light discussed the Ignis Cult.
## February 2023
### Session 3
John Doctor found another Ignis Cult sign.
```

Expected projected edges after hiding session-level headings:

```text
October 2023 -> Ignis Cult
February 2023 -> Ignis Cult
```

Unexpected/stale edge to prevent:

```text
Ignis Cult -> Mr Light [Session Notes]
```

## Recommended Next-Version Fix Direction
Do not continue patching the current edge projection sequence piecemeal.

Instead, introduce a clearer staged model:

1. Build a source-backed occurrence model.
   - Each relationship evidence snippet should become an occurrence with:
     - source document id
     - source file
     - line index
     - nearest heading stack, e.g. H1/H2/H3
     - semantic target id
     - target type

2. Resolve canonical semantic nodes before hiding headings.
   - A group heading and a group entity with the same canonical identity should map to one semantic node.
   - The heading stack should remain as context/provenance, not as a competing node identity.

3. Apply visibility rules from the occurrence model.
   - If H3 is hidden and H2 is visible, evidence under H3 should connect to H2.
   - If H1 and H3 are hidden but H2 is visible, evidence should connect to H2.
   - If all headings are hidden, the semantic group should connect to other visible semantic entities using the hidden heading label as context.

4. Only deduplicate after semantic/context routing is complete.
   - Deduplication keys should include the resolved visible context source, target, relationship type, and label.
   - Generic source-document labels should lose to more specific heading labels when both describe the same evidence path.

5. Render Graphviz from the final visible graph only.
   - Graphviz column/rank helper edges should not participate in semantic relationship decisions.

## Suggested Acceptance Criteria
For a session-note graph with `Ignis Cult` evidence in October 2023 and February 2023:

- With file name hidden and session headings hidden, `Ignis Cult` is connected to both visible month headings.
- No generic `Session Notes` edge connects `Ignis Cult` directly to characters when a more specific heading context exists.
- If multiple evidence snippets mention the same group in different visible months, all visible month connections are preserved.
- Hiding all heading levels still preserves useful group-to-character/place context edges.
- Empty/unconnected group headings are pruned.

## Files To Review Next
Primary:

- `graphviz_rendering.py`
- `character_graph/combined_graph.py`

Related:

- `character_graph/session_entities.py`
- `tests/test_graphviz_rendering.py`
- `tests/e2e/test_character_sheet_roundtrip_ui.py`
- `tests/e2e/test_session_notes_ui.py`

## Caution
Avoid treating the `Ignis Cult` / `Indigo Cult` name mismatch as the bug. That mismatch is test-harness renaming noise. The durable problem is hidden-heading context preservation for group nodes.
