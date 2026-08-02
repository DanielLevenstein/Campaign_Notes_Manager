from pathlib import Path

from character_graph.schema import CharacterGraph, CharacterNode, EmbeddingRecord, PrimaryCharacterRef, RelationshipEdge
from src.graph.presentation import party_view_presentation
from src.graph.projections import build_combined_graph_projection


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


def test_party_view_presentation_returns_render_ready_contract(tmp_path):
    character_path = tmp_path / "world_building" / "lore" / "character_sheets" / "Jory_Ravenmark.md"
    character_path.parent.mkdir(parents=True)
    character_path.write_text("# Jory Ravenmark\n", encoding="utf-8")
    graph = graph_for_source(character_path, "jory_ravenmark", "Jory Ravenmark", "orin_nightbloom", "Orin Nightbloom")
    projection = build_combined_graph_projection(
        characters=[],
        places=[],
        graphs=[graph],
        lore_paths=[character_path],
    )

    presentation = party_view_presentation(projection)

    assert presentation.has_graph
    assert presentation.graphviz_config_key == "party_view_fixture"
    assert set(presentation.graph.characters) == {"jory_ravenmark", "orin_nightbloom"}
    assert [(edge.source, edge.target) for edge in presentation.graph.edges] == [
        ("jory_ravenmark", "orin_nightbloom")
    ]
    assert presentation.empty_message == "Add Character Sheets To See Party Connections."


def test_party_view_is_wired_through_presentation_layer():
    app_source = (PROJECT_ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    rendering_source = (PROJECT_ROOT / "graphviz_rendering.py").read_text(encoding="utf-8")

    assert "party_view=party_view_presentation(projection)" in app_source
    assert "render_party_view_tab(party_view, label_font_color)" in rendering_source
    assert "def render_character_data_only_graph_view" not in rendering_source
