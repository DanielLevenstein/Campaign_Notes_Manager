from character_graph.schema import (
    CharacterGraph,
    CharacterNode,
    EmbeddingRecord,
    PrimaryCharacterRef,
    RelationshipEdge,
)
from src.persistence.storage import graph_path_for_lore_path, load_graph, save_graph
import src.persistence.lore_documents as lore_storage
from src.persistence.lore_documents import PlaceProfile, create_place


def minimal_graph(source_file: str) -> CharacterGraph:
    return CharacterGraph(
        schema_version="0.3.0",
        primary_character=PrimaryCharacterRef(
            id="jory_ravenmark",
            name="Jory Ravenmark",
            source_file=source_file,
        ),
        characters={
            "jory_ravenmark": CharacterNode(
                name="Jory Ravenmark",
                role="primary character",
                summary="Jory keeps the party moving.",
            ),
            "orin_nightbloom": CharacterNode(
                name="Orin Nightbloom",
                summary="Orin knows more than he says.",
            ),
        },
        relationships=[
            RelationshipEdge(
                source="jory_ravenmark",
                target="orin_nightbloom",
                relationship_type="ally",
                relationship_label="trusts",
                evidence=["Jory trusts Orin."],
            ),
            RelationshipEdge(
                source="jory_ravenmark",
                target="jory_ravenmark",
                relationship_type="synthetic",
                relationship_label="synthetic",
            ),
        ],
        embeddings={
            "jory_ravenmark": EmbeddingRecord(
                node_id="jory_ravenmark",
                embedding_text="Jory keeps the party moving.",
                embedding_ref="test:jory",
                vector=[0.1],
            ),
            "orin_nightbloom": EmbeddingRecord(
                node_id="orin_nightbloom",
                embedding_text="Orin knows more than he says.",
                embedding_ref="test:orin",
                vector=[0.2],
            ),
        },
    )


def test_graph_path_for_lore_path_mirrors_source_tree(tmp_path):
    source = tmp_path / "world_building" / "lore" / "places" / "Atlantia.md"

    path = graph_path_for_lore_path(
        source,
        lore_root=tmp_path / "world_building" / "lore",
        meta_data_root=tmp_path / "world_building" / "meta_data",
    )

    assert path == tmp_path / "world_building" / "meta_data" / "places" / "Atlantia.graph.json"


def test_save_graph_excludes_synthetic_edges(tmp_path):
    graph = minimal_graph("world_building/lore/character_sheets/Jory_Ravenmark.md")
    graph_path = tmp_path / "Jory_Ravenmark.graph.json"

    save_graph(graph, graph_path)

    reloaded = load_graph(graph_path)
    assert reloaded is not None
    assert [(edge.relationship_type, edge.relationship_label) for edge in reloaded.relationships] == [
        ("ally", "trusts")
    ]


def test_markdown_save_updates_mirrored_graph_metadata(tmp_path, monkeypatch):
    places_dir = tmp_path / "world_building" / "lore" / "places"
    monkeypatch.setattr(lore_storage, "PLACES_DIR", places_dir)
    monkeypatch.setattr(lore_storage, "LORE_DIR", tmp_path / "world_building" / "lore")
    monkeypatch.setattr(lore_storage, "META_DATA_DIR", tmp_path / "world_building" / "meta_data")

    place = create_place(
        PlaceProfile(
            name="Atlantia",
            place_type="City",
            summary="A bright coastal city.",
            connections=["Jory Ravenmark: Traveled there"],
        )
    )

    graph_path = lore_storage.graph_path_for_lore_path(place.path)
    assert graph_path == tmp_path / "world_building" / "meta_data" / "places" / "Atlantia.graph.json"
    assert graph_path.exists()
