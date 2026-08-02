from pathlib import Path

from character_graph.schema import CharacterGraph, CharacterNode, EmbeddingRecord, PrimaryCharacterRef, RelationshipEdge
from src.graph.projections import (
    build_combined_graph_projection,
    character_sheet_lore_graphs,
    load_lore_graphs,
    lore_source_document_id,
)
from src.persistence.lore_documents import Place


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def graph_for_source(path: Path, primary_id: str, primary_name: str, target_id: str, target_name: str) -> CharacterGraph:
    return CharacterGraph(
        schema_version="0.3.0",
        primary_character=PrimaryCharacterRef(
            id=primary_id,
            name=primary_name,
            source_file=str(path),
        ),
        characters={
            primary_id: CharacterNode(name=primary_name, summary=f"{primary_name} anchors the graph."),
            target_id: CharacterNode(name=target_name, summary=f"{target_name} is connected."),
        },
        relationships=[
            RelationshipEdge(
                source=primary_id,
                target=target_id,
                relationship_type="ally",
                relationship_label="Ally",
                evidence=[f"{primary_name} trusts {target_name}."],
            )
        ],
        embeddings={
            primary_id: EmbeddingRecord(
                node_id=primary_id,
                embedding_text=f"{primary_name} anchors the graph.",
                embedding_ref=f"test:{primary_id}",
                vector=[0.1],
            ),
            target_id: EmbeddingRecord(
                node_id=target_id,
                embedding_text=f"{target_name} is connected.",
                embedding_ref=f"test:{target_id}",
                vector=[0.2],
            ),
        },
    )


def test_combined_graph_projection_builds_stable_render_contract(tmp_path):
    place_path = tmp_path / "world_building" / "lore" / "places" / "Atlantia_Lore.md"
    character_path = tmp_path / "world_building" / "lore" / "character_sheets" / "Jory_Ravenmark.md"
    place_path.parent.mkdir(parents=True)
    character_path.parent.mkdir(parents=True)
    place_path.write_text(
        "# Atlantia Lore\n\n## Place Connections\n\n- Jory Ravenmark: Traveled there\n",
        encoding="utf-8",
    )
    character_path.write_text("# Jory Ravenmark\n", encoding="utf-8")
    place = Place(name="Atlantia_Lore", path=place_path)
    graph = graph_for_source(character_path, "jory_ravenmark", "Jory Ravenmark", "orin_nightbloom", "Orin Nightbloom")

    projection = build_combined_graph_projection(
        characters=[],
        places=[place],
        graphs=[graph],
        lore_paths=[place_path, character_path],
    )

    assert projection.has_lore
    assert projection.place_sources == [
        (lore_source_document_id(place_path), "Atlantia Lore", str(place_path), "source_document")
    ]
    assert lore_source_document_id(place_path) in projection.combined.characters
    assert "jory_ravenmark" in projection.character_sheet_combined.characters
    assert projection.main_place_ids == set()
    assert projection.main_character_ids == set()
    assert projection.character_sheet_detail_rows == []


def test_character_sheet_lore_graphs_filters_non_character_sources(tmp_path):
    character_path = tmp_path / "world_building" / "lore" / "character_sheets" / "Jory_Ravenmark.md"
    place_path = tmp_path / "world_building" / "lore" / "places" / "Atlantia.md"
    graphs = [
        graph_for_source(character_path, "jory_ravenmark", "Jory Ravenmark", "orin_nightbloom", "Orin Nightbloom"),
        graph_for_source(place_path, "atlantia", "Atlantia", "mara_voss", "Mara Voss"),
    ]

    filtered = character_sheet_lore_graphs(graphs)

    assert [graph.primary_character.id for graph in filtered] == ["jory_ravenmark"]


def test_load_lore_graphs_uses_projection_read_model(monkeypatch, tmp_path):
    path = tmp_path / "world_building" / "lore" / "places" / "Atlantia.md"
    graph = graph_for_source(path, "atlantia", "Atlantia", "mara_voss", "Mara Voss")
    calls = []

    def fake_load_or_regenerate_lore_graph(source_path):
        calls.append(source_path)
        return graph

    monkeypatch.setattr(
        "src.graph.projections.load_or_regenerate_lore_graph",
        fake_load_or_regenerate_lore_graph,
    )

    assert load_lore_graphs(lore_paths=[path]) == [graph]
    assert calls == [path]


def test_streamlit_combined_graph_uses_projection_api_instead_of_direct_graph_assembly():
    source = (PROJECT_ROOT / "streamlit_app.py").read_text(encoding="utf-8")

    assert "build_combined_graph_projection" in source
    assert "build_combined_character_graph(" not in source
    assert "load_or_regenerate_lore_graph(" not in source
    assert "combined_attribute_rows(" not in source
