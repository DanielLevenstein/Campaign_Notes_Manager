from src.persistence.session_entities import derived_lore_entity_relationships


def relationships_for(text: str) -> list[dict[str, str]]:
    return derived_lore_entity_relationships(
        source_id="session_notes",
        source_name="Session Notes",
        source_type="note",
        source_file="world_building/lore/session_notes/complex_session_graph.md",
        text=text,
        known_character_names=["Mr Light", "John Doctor"],
        known_place_names=[],
    )


def relationship_named(relationships: list[dict[str, str]], target_name: str) -> dict[str, str]:
    return next(
        relationship
        for relationship in relationships
        if relationship.get("target_name") == target_name
    )


def test_context_aware_edge_occurrences_include_source_line_and_heading_stack():
    relationships = relationships_for(
        """# Session Notes

## October 2023

### Session 7

Mr Light discussed the Ignis Cult.
"""
    )

    cult = relationship_named(relationships, "Ignis Cult")

    assert cult["source_line"] == 7
    assert cult["heading_stack"] == [
        {"level": 1, "text": "Session Notes", "id": "source_heading_1_session_notes"},
        {"level": 2, "text": "October 2023", "id": "source_heading_2_october_2023"},
        {"level": 3, "text": "Session 7", "id": "source_heading_3_session_7"},
    ]
    assert cult["context_anchor_id"] == "source_heading_3_session_7"


def test_graph_creation_emits_direct_edges_for_entities_in_the_same_evidence_sentence():
    relationships = relationships_for(
        """# Session Notes

## October 2023

### Session 7

Mr Light discussed the Ignis Cult.
"""
    )

    direct_edges = [
        relationship
        for relationship in relationships
        if relationship.get("source_id") == "mrlight"
        and relationship.get("target_id") == "igniscult"
        and relationship.get("relationship_kind") == "direct_context"
    ]

    assert direct_edges == [
        {
            "source_id": "mrlight",
            "source_name": "Mr Light",
            "source_type": "character",
            "source_file": "world_building/lore/session_notes/complex_session_graph.md",
            "target_id": "igniscult",
            "target_name": "Ignis Cult",
            "target_type": "group",
            "relationship": "Mentioned With",
            "relationship_kind": "direct_context",
            "evidence": "Mr Light discussed the Ignis Cult.",
            "source_line": 7,
            "context_anchor_id": "source_heading_3_session_7",
        }
    ]


def test_context_aware_edges_preserve_each_visible_ancestor_for_repeated_group_evidence():
    relationships = relationships_for(
        """# Session Notes

## October 2023

### Session 7

Mr Light discussed the Ignis Cult.

## February 2023

### Session 3

John Doctor found another Ignis Cult sign.
"""
    )

    cult_occurrences = [
        relationship
        for relationship in relationships
        if relationship.get("target_name") == "Ignis Cult"
        and relationship.get("relationship_kind") == "context_anchor"
    ]

    assert {
        relationship["visible_ancestor_context_ids"]["hide_h3"]
        for relationship in cult_occurrences
    } == {
        "source_heading_2_october_2023",
        "source_heading_2_february_2023",
    }


def test_moon_gate_is_typed_as_a_place_before_projection():
    relationships = relationships_for(
        """# Session Notes

## October 2023

### Session 7

They traced the Indigo Cult to the Moon Gate.
"""
    )

    moon_gate = relationship_named(relationships, "Moon Gate")

    assert moon_gate["target_type"] == "place"


def test_group_mentions_do_not_create_duplicate_character_nodes_for_the_same_name():
    relationships = relationships_for(
        """# Session Notes

## October 2023

### Session 7

They traced the Indigo Cult to the Moon Gate.
Mr Light questioned an Indigo Cult member.
"""
    )

    indigo_types = {
        relationship["target_type"]
        for relationship in relationships
        if relationship.get("target_name") == "Indigo Cult"
    }

    assert indigo_types == {"group"}
