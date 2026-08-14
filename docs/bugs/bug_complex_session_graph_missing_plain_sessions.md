# Complex Session Graph Missing Plain Sessions

## Date
2026-08-14

## Status
Deferred

## Summary
In Session View, `tests/fixtures/session_notes/complex_session_graph.md` does not show Sessions 2, 3, 5, and 6. This is a graph projection/rendering bug, not a knowledge-view configuration bug.

## Observed Behavior
- Session View can render later sections that contain extracted semantic lore connections.
- Sessions 2, 3, 5, and 6 are missing from the graph.
- The missing sessions are plain markdown note sections with headings and prose, but they do not appear to have semantic entity edges that survive projection pruning.

## Expected Behavior
- Session View should preserve visible session structure from the selected source file.
- Plain note sessions should still appear as session/heading context, even when no character, place, group, or artifact node was extracted from that section.
- Hiding heading levels should collapse or bridge those sessions intentionally instead of silently dropping them.

## Reproduction
1. Load or import `tests/fixtures/session_notes/complex_session_graph.md`.
2. Open the Knowledge Graph area.
3. Select `Session View`.
4. Select `complex_session_graph.md`.
5. Observe that Sessions 2, 3, 5, and 6 are absent.

## Important Scope Note
Do not treat this as part of the knowledge-view hierarchy migration. Knowledge views should decide which view, controls, and columns are active. The missing sessions are caused by how the Session View projection preserves or prunes markdown heading nodes.

## Initial Investigation Notes
The likely area is `markdown_header_lore_graph` and its pruning/collapse helpers in `src/rendering/graphviz_rendering.py`.

Current suspicion:

- The projection creates markdown heading nodes from the selected source file.
- Later pruning removes markdown headings that do not have an associated non-source entity edge.
- Plain session sections can therefore disappear even though they are real source structure.
- When H1/H2/H3 controls hide heading nodes, empty session context needs an explicit preservation or bridge rule.

Relevant helpers to inspect:

- `markdown_header_lore_graph`
- `prune_unassociated_markdown_headings`
- `graph_without_markdown_heading_nodes`
- `filter_lore_graph_by_heading`

## Recommended Future Fix
Add a regression test around `complex_session_graph.md` before changing projection behavior.

The test should assert that Session View preserves Sessions 2, 3, 5, and 6 either as visible heading nodes or as deliberate collapsed context after heading-hide controls are applied. Then update the projection so markdown source structure is retained independently from semantic entity extraction.
