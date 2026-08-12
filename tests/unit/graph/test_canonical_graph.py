from src.graph.combined_graph import (
    CombinedCharacterGraph,
    CombinedCharacterNode,
    CombinedRelationshipEdge,
)
from src.graph import (
    CanonicalEdge,
    CanonicalGraph,
    CanonicalGraphService,
    CanonicalNode,
    canonical_graph_from_character_graph,
    canonical_graph_from_combined,
    canonical_node_from_legacy,
    canonical_source_kind,
    canonical_type_for_legacy_node,
    normalize_source_file,
    source_file_key,
)
from src.graph.schema import (
    CharacterGraph,
    CharacterNode,
    PrimaryCharacterRef,
    RelationshipEdge,
)


def test_normalize_source_file_is_deterministic_for_projection_identifiers(tmp_path):
    root = tmp_path / "campaign"
    source = root / "world_building" / "lore" / "session_notes" / "Session_1.md"

    normalized = normalize_source_file(source, root=root)

    assert normalized == "world_building/lore/session_notes/Session_1.md"
    assert source_file_key(str(source).upper(), root=str(root).upper()) == normalized.casefold()


def test_legacy_node_types_map_to_canonical_types():
    assert canonical_type_for_legacy_node("source_heading_group_2") == "markdown_heading"
    assert canonical_type_for_legacy_node("source_document") == "source_document"
    assert canonical_type_for_legacy_node("group") == "group"
    assert canonical_type_for_legacy_node("unknown") == "entity"


def test_session_note_source_metadata_survives_legacy_adapter(tmp_path):
    source_file = tmp_path / "world_building" / "lore" / "session_notes" / "Family_Tree.md"
    node = CombinedCharacterNode(
        id="family_tree",
        name="Family Tree",
        source_file=str(source_file),
        node_type="character",
    )

    canonical = canonical_node_from_legacy(node, root=tmp_path)

    assert canonical.canonical_type == "character"
    assert canonical.source_file == "world_building/lore/session_notes/Family_Tree.md"
    assert canonical.source_id == "family_tree"
    assert canonical.provenance["source_kind"] == "session_note"
    assert canonical.properties["legacy_node_type"] == "character"
    assert canonical_source_kind(canonical.source_file) == "session_note"


def test_combined_graph_adapter_preserves_nodes_edges_and_evidence(tmp_path):
    source_file = tmp_path / "world_building" / "lore" / "places" / "Atlantia_Lore.md"
    combined = CombinedCharacterGraph(
        characters={
            "source_document__atlantia_lore": CombinedCharacterNode(
                id="source_document__atlantia_lore",
                name="Atlantia Lore",
                source_file=str(source_file),
                node_type="source_document",
            ),
            "orin_nightbloom": CombinedCharacterNode(
                id="orin_nightbloom",
                name="Orin Nightbloom",
                source_file=str(source_file),
                node_type="character",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="orin_nightbloom",
                relationship_type="Mentioned",
                relationship_label="Mentioned",
                evidence=["Atlantia Lore names Orin Nightbloom."],
            )
        ],
    )

    canonical = canonical_graph_from_combined(combined, root=tmp_path)

    assert canonical.nodes["source_document__atlantia_lore"].canonical_type == "source_document"
    assert canonical.nodes["source_document__atlantia_lore"].provenance["source_kind"] == "place_lore"
    assert len(canonical.edges) == 1
    edge = next(iter(canonical.edges.values()))
    assert edge.source_id == "source_document__atlantia_lore"
    assert edge.target_id == "orin_nightbloom"
    assert edge.relation_type == "mentioned"
    assert edge.evidence == ("Atlantia Lore names Orin Nightbloom.",)


def test_character_graph_adapter_preserves_source_metadata_and_edges(tmp_path):
    source_file = tmp_path / "world_building" / "lore" / "session_notes" / "Family_Tree.md"
    graph = CharacterGraph(
        schema_version="0.3.0",
        primary_character=PrimaryCharacterRef(
            id="family_tree",
            name="Family Tree",
            source_file=str(source_file),
        ),
        characters={
            "jory_ravenmark": CharacterNode(name="Jory Ravenmark"),
            "orin_nightbloom": CharacterNode(name="Orin Nightbloom"),
        },
        relationships=[
            RelationshipEdge(
                source="jory_ravenmark",
                target="orin_nightbloom",
                relationship_type="ally",
                relationship_label="Trusts",
                evidence=["Jory trusts Orin."],
            )
        ],
    )

    canonical = canonical_graph_from_character_graph(graph, root=tmp_path)

    assert canonical.nodes["jory_ravenmark"].source_file == "world_building/lore/session_notes/Family_Tree.md"
    assert canonical.nodes["jory_ravenmark"].provenance["source_kind"] == "session_note"
    assert canonical.nodes["jory_ravenmark"].canonical_type == "character"
    edge = next(iter(canonical.edges.values()))
    assert edge.source_id == "jory_ravenmark"
    assert edge.target_id == "orin_nightbloom"
    assert edge.relation_type == "ally"
    assert edge.evidence == ("Jory trusts Orin.",)


def test_canonical_graph_service_persists_nodes_edges_and_versions(tmp_path):
    service = CanonicalGraphService(tmp_path / "canonical_graph.sqlite3")
    node = CanonicalNode(
        id="orin_nightbloom",
        canonical_type="character",
        display_name="Orin Nightbloom",
        source_file="world_building/lore/character_sheets/Orin_Nightbloom.md",
        source_id="orin_nightbloom",
        canonical_tags=("primary",),
        provenance={"source_kind": "character_sheet"},
    )
    edge = CanonicalEdge(
        id="edge_orin_jory_ally",
        source_id="orin_nightbloom",
        target_id="jory_ravenmark",
        relation_type="ally",
        relation_label="Ally",
        evidence=("Orin trusts Jory.",),
    )

    service.upsert_graph(CanonicalGraph(nodes={node.id: node}, edges={edge.id: edge}))
    first_version = service.version()
    service.upsert_node(CanonicalNode(**{**node.__dict__, "display_name": "Orin Nightbloom II"}))

    nodes = service.get_nodes({"source_file": "WORLD_BUILDING/LORE/CHARACTER_SHEETS/ORIN_NIGHTBLOOM.MD"})
    edges = service.get_edges({"source_id": "orin_nightbloom"})

    assert first_version == 2
    assert service.version() == 3
    assert len(nodes) == 1
    assert nodes[0].display_name == "Orin Nightbloom II"
    assert nodes[0].version == 2
    assert nodes[0].canonical_tags == ("primary",)
    assert len(edges) == 1
    assert edges[0].id == edge.id
    assert edges[0].target_id == "jory_ravenmark"
    assert edges[0].relation_type == "ally"
    assert edges[0].evidence == ("Orin trusts Jory.",)
    assert edges[0].version == 1
    assert edges[0].created_at


def test_canonical_graph_service_uses_persistence_database_connector(tmp_path, monkeypatch):
    calls = []
    from src.persistence.sqlite_store import connect_database

    def tracking_connect(database_path):
        calls.append(database_path)
        return connect_database(database_path)

    monkeypatch.setattr("src.graph.service.connect_database", tracking_connect)

    service = CanonicalGraphService(tmp_path / "canonical_graph.sqlite3")
    service.upsert_node(
        CanonicalNode(
            id="jory_ravenmark",
            canonical_type="character",
            display_name="Jory Ravenmark",
        )
    )

    assert calls
    assert all(path == tmp_path / "canonical_graph.sqlite3" for path in calls)


def test_canonical_graph_service_replaces_source_graph_without_stale_edges(tmp_path):
    service = CanonicalGraphService(tmp_path / "canonical_graph.sqlite3")
    source_file = "world_building/lore/places/Atlantia.md"
    old_graph = CanonicalGraph(
        nodes={
            "atlantia": CanonicalNode(
                id="atlantia",
                canonical_type="source_document",
                display_name="Atlantia",
                source_file=source_file,
            ),
            "jory_ravenmark": CanonicalNode(
                id="jory_ravenmark",
                canonical_type="character",
                display_name="Jory Ravenmark",
                source_file=source_file,
            ),
        },
        edges={
            "edge_atlantia_jory": CanonicalEdge(
                id="edge_atlantia_jory",
                source_id="atlantia",
                target_id="jory_ravenmark",
                relation_type="mentioned",
            )
        },
    )
    new_graph = CanonicalGraph(
        nodes={
            "atlantia": CanonicalNode(
                id="atlantia",
                canonical_type="source_document",
                display_name="Atlantia",
                source_file=source_file,
            ),
            "orin_nightbloom": CanonicalNode(
                id="orin_nightbloom",
                canonical_type="character",
                display_name="Orin Nightbloom",
                source_file=source_file,
            ),
        },
        edges={
            "edge_atlantia_orin": CanonicalEdge(
                id="edge_atlantia_orin",
                source_id="atlantia",
                target_id="orin_nightbloom",
                relation_type="mentioned",
            )
        },
    )

    service.replace_source_graph(source_file, old_graph)
    service.replace_source_graph(source_file, new_graph)

    assert [node.id for node in service.get_nodes({"source_file": source_file})] == ["atlantia", "orin_nightbloom"]
    assert [edge.id for edge in service.get_edges()] == ["edge_atlantia_orin"]
