# Node Type Bugs

## Status
Resolved

## Moon Gate
- Based on the evidence in `complex_session_graph.md` "Moon Gate" should be a place not a character
  - "They traced the Indigo Cult to the Moon Gate."

## Fix Summary
Session-note entity extraction now treats `gate` names, along with related location terms such as `portal`, `temple`, `tower`, and `harbor`, as place-like names before projection.

## Test Evidence
- `tests/unit/graph/test_combined_character_graph.py::test_session_note_entity_extraction_treats_gate_names_as_places`
- `tests/unit/graph/test_context_aware_edges.py::test_moon_gate_is_typed_as_a_place_before_projection`
