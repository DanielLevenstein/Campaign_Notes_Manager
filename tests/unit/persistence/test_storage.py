from character_graph.schema import (
    CharacterGraph,
    CharacterNode,
    EmbeddingRecord,
    PrimaryCharacterRef,
    RelationshipEdge,
)
from src.persistence.storage import (
    delete_file,
    file_hash_key,
    graph_path_for_lore_path,
    lore_file_hash_changed,
    load_graph,
    persist_file_hash,
    read_json,
    read_markdown,
    save_graph,
    write_bytes,
    write_json,
    write_markdown,
    write_text,
)


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


def test_markdown_write_reads_and_updates_graph_callback(tmp_path):
    path = tmp_path / "world_building" / "lore" / "places" / "Atlantia.md"
    updated_paths = []

    write_markdown(path, "# Atlantia\n", update_graph=updated_paths.append)

    assert read_markdown(path) == "# Atlantia\n"
    assert updated_paths == [path]


def test_text_write_reads_and_updates_graph_callback(tmp_path):
    path = tmp_path / "world_building" / "meta_data" / "character_metadata" / "Jory" / "PROFILE.json"
    updated_paths = []

    write_text(path, '{"name": "Jory"}\n', update_graph=updated_paths.append)

    assert path.read_text(encoding="utf-8") == '{"name": "Jory"}\n'
    assert updated_paths == [path]


def test_lore_file_hash_manifest_tracks_unchanged_markdown(tmp_path):
    lore_root = tmp_path / "world_building" / "lore"
    meta_data_root = tmp_path / "world_building" / "meta_data"
    path = lore_root / "character_sheets" / "Jory_Ravenmark.md"
    write_markdown(path, "# Jory Ravenmark\n")

    assert lore_file_hash_changed(path, lore_root=lore_root, meta_data_root=meta_data_root)

    persist_file_hash(path, lore_root=lore_root, meta_data_root=meta_data_root)

    assert not lore_file_hash_changed(path, lore_root=lore_root, meta_data_root=meta_data_root)
    assert file_hash_key(path, lore_root=lore_root) == "character_sheets/Jory_Ravenmark.md"

    write_markdown(path, "# Jory Ravenmark\n\nChanged.\n")

    assert lore_file_hash_changed(path, lore_root=lore_root, meta_data_root=meta_data_root)


def test_json_and_bytes_helpers_create_parent_directories(tmp_path):
    payload_path = tmp_path / "world_building" / "meta_data" / "places" / "Atlantia.json"
    bytes_path = tmp_path / "world_building" / "lore" / "assets" / "map.bin"

    write_json(payload_path, {"name": "Atlantia"})
    write_bytes(bytes_path, b"map bytes")

    assert read_json(payload_path) == {"name": "Atlantia"}
    assert bytes_path.read_bytes() == b"map bytes"


def test_delete_file_removes_linked_graph_path(tmp_path):
    markdown_path = tmp_path / "world_building" / "lore" / "places" / "Atlantia.md"
    graph_path = tmp_path / "world_building" / "meta_data" / "places" / "Atlantia.graph.json"
    write_markdown(markdown_path, "# Atlantia\n")
    write_json(graph_path, {"graph": True})

    delete_file(markdown_path, linked_graph_path=graph_path)

    assert not markdown_path.exists()
    assert not graph_path.exists()


def test_save_graph_excludes_synthetic_edges(tmp_path):
    graph = minimal_graph("world_building/lore/character_sheets/Jory_Ravenmark.md")
    graph_path = tmp_path / "Jory_Ravenmark.graph.json"

    save_graph(graph, graph_path)

    reloaded = load_graph(graph_path)
    assert reloaded is not None
    assert [(edge.relationship_type, edge.relationship_label) for edge in reloaded.relationships] == [
        ("ally", "trusts")
    ]
