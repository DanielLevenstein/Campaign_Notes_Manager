from pathlib import Path

from src.graph.schema import (
    CharacterGraph,
    CharacterNode,
    EmbeddingRecord,
    PrimaryCharacterRef,
    RelationshipEdge,
)
from src.graph import CanonicalGraphService
from src.persistence.storage import (
    canonical_graph_database_path,
    graph_path_for_lore_path,
    load_graph,
    save_graph,
    save_lore_graph,
)
import src.persistence.lore_documents as lore_storage
from src.persistence.lore_documents import PlaceProfile, create_place


PROJECT_ROOT = Path(__file__).resolve().parents[3]


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


def relationship_graph(
    source_file: str,
    source_id: str,
    source_name: str,
    target_id: str,
    target_name: str,
    relationship_type: str = "mentioned",
) -> CharacterGraph:
    return CharacterGraph(
        schema_version="0.3.0",
        primary_character=PrimaryCharacterRef(
            id=source_id,
            name=source_name,
            source_file=source_file,
        ),
        characters={
            source_id: CharacterNode(name=source_name, summary=f"{source_name} is the source node."),
            target_id: CharacterNode(name=target_name, summary=f"{target_name} is the target node."),
        },
        relationships=[
            RelationshipEdge(
                source=source_id,
                target=target_id,
                relationship_type=relationship_type,
                relationship_label=relationship_type.title(),
                evidence=[f"{source_name} mentions {target_name}."],
            )
        ],
        embeddings={
            source_id: EmbeddingRecord(
                node_id=source_id,
                embedding_text=f"{source_name} is the source node.",
                embedding_ref=f"test:{source_id}",
                vector=[0.1],
            ),
            target_id: EmbeddingRecord(
                node_id=target_id,
                embedding_text=f"{target_name} is the target node.",
                embedding_ref=f"test:{target_id}",
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


def test_save_lore_graph_updates_canonical_store_and_replaces_stale_source_rows(tmp_path):
    lore_root = tmp_path / "world_building" / "lore"
    meta_root = tmp_path / "world_building" / "meta_data"
    source = lore_root / "places" / "Atlantia.md"
    source.parent.mkdir(parents=True)
    source.write_text("# Atlantia\n", encoding="utf-8")

    first_graph = minimal_graph(str(source))
    save_lore_graph(first_graph, source, lore_root=lore_root, meta_data_root=meta_root)
    second_graph = CharacterGraph(
        schema_version="0.3.0",
        primary_character=PrimaryCharacterRef(
            id="atlantia",
            name="Atlantia",
            source_file=str(source),
        ),
        characters={
            "atlantia": CharacterNode(name="Atlantia", summary="Atlantia is a bright coastal city."),
            "mara_voss": CharacterNode(name="Mara Voss", summary="Mara Voss is mentioned in Atlantia lore."),
        },
        relationships=[
            RelationshipEdge(
                source="atlantia",
                target="mara_voss",
                relationship_type="mentioned",
                relationship_label="Mentioned",
                evidence=["Atlantia mentions Mara Voss."],
            ),
            RelationshipEdge(
                source="atlantia",
                target="atlantia",
                relationship_type="synthetic",
                relationship_label="synthetic",
            ),
        ],
        embeddings={
            "atlantia": EmbeddingRecord(
                node_id="atlantia",
                embedding_text="Atlantia is a bright coastal city.",
                embedding_ref="test:atlantia",
                vector=[0.1],
            ),
            "mara_voss": EmbeddingRecord(
                node_id="mara_voss",
                embedding_text="Mara Voss is mentioned in Atlantia lore.",
                embedding_ref="test:mara",
                vector=[0.2],
            ),
        },
    )

    graph_path = save_lore_graph(second_graph, source, lore_root=lore_root, meta_data_root=meta_root)
    persisted = load_graph(graph_path)
    service = CanonicalGraphService(canonical_graph_database_path(meta_data_root=meta_root))

    assert graph_path == meta_root / "places" / "Atlantia.graph.json"
    assert persisted is not None
    assert [(edge.source, edge.target) for edge in persisted.relationships] == [("atlantia", "mara_voss")]
    assert [node.id for node in service.get_nodes({"source_file": "world_building/lore/places/Atlantia.md"})] == [
        "atlantia",
        "mara_voss",
    ]
    assert [(edge.source_id, edge.target_id) for edge in service.get_edges()] == [("atlantia", "mara_voss")]


def test_save_lore_graph_uses_same_metadata_tree_for_all_source_kinds(tmp_path):
    lore_root = tmp_path / "world_building" / "lore"
    meta_root = tmp_path / "world_building" / "meta_data"
    expected_paths = [
        (lore_root / "character_sheets" / "Jory_Ravenmark.md", meta_root / "character_sheets" / "Jory_Ravenmark.graph.json"),
        (lore_root / "places" / "Atlantia.md", meta_root / "places" / "Atlantia.graph.json"),
        (lore_root / "session_notes" / "Family_Tree.md", meta_root / "session_notes" / "Family_Tree.graph.json"),
    ]

    for source, expected_graph_path in expected_paths:
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("# Source\n\nJory Ravenmark trusts Orin Nightbloom.\n", encoding="utf-8")
        graph = minimal_graph(str(source))

        graph_path = save_lore_graph(graph, source, lore_root=lore_root, meta_data_root=meta_root)

        assert graph_path == expected_graph_path
        assert graph_path.exists()


def test_save_lore_graph_filters_synthetic_edges_from_json_and_canonical_store(tmp_path):
    lore_root = tmp_path / "world_building" / "lore"
    meta_root = tmp_path / "world_building" / "meta_data"
    source = lore_root / "session_notes" / "Family_Tree.md"
    source.parent.mkdir(parents=True)
    source.write_text("# Family Tree\n", encoding="utf-8")

    graph_path = save_lore_graph(minimal_graph(str(source)), source, lore_root=lore_root, meta_data_root=meta_root)
    persisted = load_graph(graph_path)
    service = CanonicalGraphService(canonical_graph_database_path(meta_data_root=meta_root))

    assert persisted is not None
    assert all(edge.relationship_type != "synthetic" for edge in persisted.relationships)
    assert all(edge.relation_type != "synthetic" for edge in service.get_edges())
    assert [(edge.source_id, edge.target_id) for edge in service.get_edges()] == [
        ("jory_ravenmark", "orin_nightbloom")
    ]


def test_save_lore_graph_replacement_is_scoped_to_the_edited_source(tmp_path):
    lore_root = tmp_path / "world_building" / "lore"
    meta_root = tmp_path / "world_building" / "meta_data"
    atlantia = lore_root / "places" / "Atlantia.md"
    family_tree = lore_root / "session_notes" / "Family_Tree.md"
    atlantia.parent.mkdir(parents=True, exist_ok=True)
    family_tree.parent.mkdir(parents=True, exist_ok=True)
    atlantia.write_text("# Atlantia\n", encoding="utf-8")
    family_tree.write_text("# Family Tree\n", encoding="utf-8")

    save_lore_graph(
        relationship_graph(str(atlantia), "atlantia", "Atlantia", "jory_ravenmark", "Jory Ravenmark"),
        atlantia,
        lore_root=lore_root,
        meta_data_root=meta_root,
    )
    save_lore_graph(
        relationship_graph(str(family_tree), "family_tree", "Family Tree", "ravenmark_family", "Ravenmark Family"),
        family_tree,
        lore_root=lore_root,
        meta_data_root=meta_root,
    )
    revised_atlantia = relationship_graph(str(atlantia), "atlantia", "Atlantia", "mara_voss", "Mara Voss")

    save_lore_graph(revised_atlantia, atlantia, lore_root=lore_root, meta_data_root=meta_root)
    service = CanonicalGraphService(canonical_graph_database_path(meta_data_root=meta_root))

    assert [node.id for node in service.get_nodes({"source_file": "world_building/lore/places/Atlantia.md"})] == [
        "atlantia",
        "mara_voss",
    ]
    assert [
        node.id for node in service.get_nodes({"source_file": "world_building/lore/session_notes/Family_Tree.md"})
    ] == ["family_tree", "ravenmark_family"]


def test_lore_graph_load_regenerates_missing_metadata_and_canonical_rows(tmp_path, monkeypatch):
    lore_root = tmp_path / "world_building" / "lore"
    meta_root = tmp_path / "world_building" / "meta_data"
    session_root = lore_root / "session_notes"
    monkeypatch.setattr(lore_storage, "LORE_DIR", lore_root)
    monkeypatch.setattr(lore_storage, "META_DATA_DIR", meta_root)
    monkeypatch.setattr(lore_storage, "SESSION_NOTES_DIR", session_root)
    source = session_root / "Family_Tree.md"
    source.parent.mkdir(parents=True)
    source.write_text(
        "# Family Tree\n\n## Ravenmark Family\n\nJory Ravenmark trusts Orin Nightbloom.\n",
        encoding="utf-8",
    )

    graph = lore_storage.load_or_regenerate_lore_graph(source)
    service = CanonicalGraphService(canonical_graph_database_path(meta_data_root=meta_root))

    assert graph is not None
    assert lore_storage.graph_path_for_lore_path(source).exists()
    assert service.get_nodes({"source_file": "world_building/lore/session_notes/Family_Tree.md"})


def test_ui_and_domain_code_do_not_instantiate_graph_database_outside_persistence_layer():
    allowed = {
        PROJECT_ROOT / "src" / "persistence" / "storage.py",
        PROJECT_ROOT / "src" / "graph" / "service.py",
    }
    offenders = []
    for path in [PROJECT_ROOT / "streamlit_app.py", *PROJECT_ROOT.joinpath("src").rglob("*.py")]:
        if path in allowed:
            continue
        text = path.read_text(encoding="utf-8")
        if "CanonicalGraphService(" in text:
            offenders.append(path.relative_to(PROJECT_ROOT).as_posix())

    assert offenders == []
