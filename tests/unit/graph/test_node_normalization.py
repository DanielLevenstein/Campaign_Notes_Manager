from src.graph.node_normalization import normalize_entity_display_name, normalize_graph_nodes
from src.graph.schema import (
    CharacterGraph,
    CharacterNode,
    EmbeddingRecord,
    PlaceNode,
    PrimaryCharacterRef,
    RelationshipEdge,
)


def test_normalize_entity_display_name_strips_descriptors_for_entities():
    assert normalize_entity_display_name("Atlantia Lore", "place") == "Atlantia"
    assert normalize_entity_display_name("Indigo Cult Investigation", "group") == "Indigo Cult"
    assert normalize_entity_display_name("Session Notes", "note") == "Session"
    assert normalize_entity_display_name("Atlantia Lore", "source_heading_1") == "Atlantia Lore"
    assert normalize_entity_display_name("Atlantia Lore", "place", is_heading=True) == "Atlantia Lore"


def test_normalize_graph_nodes_marks_place_lore_root_as_place_without_schema_migration():
    graph = CharacterGraph(
        schema_version="0.3.0",
        primary_character=PrimaryCharacterRef(
            id="atlantia_lore",
            name="Atlantia Lore",
            source_file="world_building/lore/places/Atlantia_Lore.md",
            node_type="character",
        ),
        characters={
            "atlantia_lore": CharacterNode(
                name="Atlantia Lore",
                role="primary character",
                summary="Atlantia is a bright coastal city.",
            )
        },
        embeddings={
            "atlantia_lore": EmbeddingRecord(
                node_id="atlantia_lore",
                embedding_text="Atlantia is a bright coastal city.",
                embedding_ref="test:atlantia",
                vector=[0.1],
            )
        },
    )

    normalized = normalize_graph_nodes(graph)

    assert normalized.primary_character.name == "Atlantia"
    assert normalized.primary_character.node_type == "place"
    assert normalized.characters["atlantia_lore"].name == "Atlantia"
    assert normalized.characters["atlantia_lore"].node_type == "place"
    assert normalized.characters["atlantia_lore"].role == "place"


def test_normalize_graph_nodes_preserves_markdown_heading_text():
    graph = CharacterGraph(
        schema_version="0.3.0",
        primary_character=PrimaryCharacterRef(id="session_notes", name="Session Notes", source_file="session_notes.md"),
        characters={
            "session_notes": CharacterNode(name="Session Notes", summary="Session notes root."),
            "heading": CharacterNode(
                name="Atlantia Lore",
                node_type="source_heading_1",
                summary="Heading.",
            ),
        },
    )

    normalized = normalize_graph_nodes(graph)

    assert normalized.characters["heading"].name == "Atlantia Lore"


def test_normalize_graph_nodes_resolves_character_group_type_conflicts():
    graph = CharacterGraph(
        schema_version="0.3.0",
        primary_character=PrimaryCharacterRef(id="session_notes", name="Session Notes", source_file="session_notes.md"),
        characters={
            "session_notes": CharacterNode(name="Session Notes", summary="Session notes root."),
            "indigo_cult": CharacterNode(name="Indigo Cult", summary="Mistyped character."),
            "indigocult": CharacterNode(name="Indigo Cult", node_type="group", summary="A real group."),
        },
        relationships=[
            RelationshipEdge(
                source="session_notes",
                target="indigo_cult",
                relationship_type="mentioned",
                relationship_label="Mentioned",
                evidence=["They traced the Indigo Cult."],
            )
        ],
        embeddings={
            "session_notes": EmbeddingRecord(
                node_id="session_notes",
                embedding_text="Session notes root.",
                embedding_ref="test:session",
                vector=[0.1],
            ),
            "indigo_cult": EmbeddingRecord(
                node_id="indigo_cult",
                embedding_text="Mistyped character.",
                embedding_ref="test:mistyped",
                vector=[0.2],
            ),
            "indigocult": EmbeddingRecord(
                node_id="indigocult",
                embedding_text="A real group.",
                embedding_ref="test:group",
                vector=[0.3],
            ),
        },
    )

    normalized = normalize_graph_nodes(graph)

    assert "indigo_cult" not in normalized.characters
    assert normalized.characters["indigocult"].node_type == "group"
    assert [(edge.source, edge.target) for edge in normalized.relationships] == [("session_notes", "indigocult")]
    assert set(normalized.embeddings) == {"session_notes", "indigocult"}
    assert normalized.embeddings["indigocult"].node_id == "indigocult"


def test_normalize_graph_nodes_resolves_character_place_type_conflicts():
    graph = CharacterGraph(
        schema_version="0.3.0",
        primary_character=PrimaryCharacterRef(id="session_notes", name="Session Notes", source_file="session_notes.md"),
        characters={
            "session_notes": CharacterNode(name="Session Notes", summary="Session notes root."),
            "moon_gate_character": CharacterNode(name="Moon Gate", summary="Mistyped character."),
        },
        places={
            "moon_gate": PlaceNode(
                name="Moon Gate",
                summary="A place in the session notes.",
                source_spans=["They traced the Indigo Cult to the Moon Gate."],
            )
        },
        relationships=[
            RelationshipEdge(
                source="session_notes",
                target="moon_gate_character",
                relationship_type="mentioned",
                relationship_label="Mentioned",
                evidence=["They traced the Indigo Cult to the Moon Gate."],
            )
        ],
    )

    normalized = normalize_graph_nodes(graph)

    assert "moon_gate_character" not in normalized.characters
    assert "moon_gate" in normalized.places
    assert [(edge.source, edge.target) for edge in normalized.relationships] == [("session_notes", "moon_gate")]
