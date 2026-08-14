import json
from pathlib import Path

import pytest

from src.graph.knowledge_view_config import (
    load_knowledge_view_definition,
    load_knowledge_view_definitions,
)


TEST_KNOWLEDGE_VIEW_CONFIG_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "knowledge_views"


def test_load_default_knowledge_view_stubs_match_current_graph_tabs():
    definitions = load_knowledge_view_definitions(TEST_KNOWLEDGE_VIEW_CONFIG_DIR)

    assert [definition.view_key for definition in definitions] == [
        "character_view",
        "party_view",
        "location_view",
        "session_view",
    ]
    assert [definition.view_name for definition in definitions] == [
        "Character View",
        "Party View",
        "Location View",
        "Session View",
    ]
    assert [definition.graphviz_view for definition in definitions] == [
        "character_view",
        "default_view_fixture",
        "default_view_fixture",
        "default_view_fixture",
    ]
    assert all(definition.migration_status == "stub" for definition in definitions)


def test_directory_knowledge_view_stubs_expose_source_fixtures_and_hidden_elements():
    location = load_knowledge_view_definition("location_view", TEST_KNOWLEDGE_VIEW_CONFIG_DIR)
    session = load_knowledge_view_definition("session_view", TEST_KNOWLEDGE_VIEW_CONFIG_DIR)

    assert location.source_fixtures == (
        "tests/fixtures/character_sheets",
        "tests/fixtures/places/Atlantia_Lore.md",
        "tests/fixtures/session_notes/Family_Tree.md",
    )
    assert location.hidden_elements == ("file_name",)
    assert location.unhidden_elements == ("h1", "h2", "h3")
    assert location.columns == (
        ("source_files", "h1", "places"),
        ("h2",),
        ("h3",),
        ("groups",),
        ("artifacts",),
        ("linked_characters",),
    )
    assert location.graphviz_view == "default_view_fixture"
    assert location.projection == "place_lore_graph"
    assert location.source_predicate == "places"
    assert location.column_layout == "place_lore_directory"
    assert location.source_key == "location_view_source_file"
    assert location.heading_key == "location_view_heading"
    assert location.include_all_heading_option is True
    assert location.source_empty_message == "Add Place Lore To Use Location View."
    assert location.heading_empty_message == "Add Markdown Headings To Place Lore To Use Location View."
    assert location.graph_empty_message == "No Place Lore Connections Were Found For This File."

    assert session.source_fixtures == (
        "tests/fixtures/character_sheets",
        "tests/fixtures/session_notes/complex_session_graph.md",
    )
    assert session.hidden_elements == ("file_name", "h1", "h2", "h3")
    assert session.unhidden_elements == ("h1",)
    assert session.columns == (
        ("source_files", "h1"),
        ("places",),
        ("main_characters",),
        ("h2", "groups", "artifacts"),
        ("h3",),
        ("secondary_characters",),
    )
    assert session.graphviz_view == "default_view_fixture"
    assert session.projection == "markdown_header_lore_graph"
    assert session.source_predicate == "session_notes"
    assert session.column_layout == "session_note_lore_directory"
    assert session.source_key == "session_view_source_file"
    assert session.heading_key == "session_view_heading"
    assert session.include_all_heading_option is True
    assert session.source_empty_message == "Add Session Notes To Use Session View."
    assert session.heading_empty_message == "Add Markdown Headings To Session Notes To Use Session View."
    assert session.graph_empty_message == "No Session Note Connections Were Found For This File."


def test_party_knowledge_view_uses_internal_column_keys():
    party = load_knowledge_view_definition("party_view", TEST_KNOWLEDGE_VIEW_CONFIG_DIR)

    assert party.columns == (
        ("family_names", "artifacts", "groups"),
        ("main_characters",),
        ("secondary_characters", "places"),
    )


def test_knowledge_view_config_loads_explicit_view_without_defaults(tmp_path):
    config_dir = tmp_path / "knowledge_views"
    config_dir.mkdir()
    (config_dir / "location_view.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1.0",
                "view_name": "Location View",
                "source_fixtures": ["tests/fixtures/places/Atlantia_Lore.md"],
                "hidden_elements": ["file_name"],
                "unhidden_elements": ["h1", "h2", "h3"],
                "columns": [["source_files", "h1", "places"], ["linked_characters"]],
                "graphviz_view": "heading_view",
                "projection": "place_lore_graph",
                "source_predicate": "places",
                "column_layout": "place_lore_directory",
                "source_key": "location_view_source_file",
                "heading_key": "location_view_heading",
                "include_all_heading_option": True,
                "source_empty_message": "Add Place Lore.",
                "heading_empty_message": "Add Headings.",
                "graph_empty_message": "No graph.",
            }
        ),
        encoding="utf-8",
    )

    definition = load_knowledge_view_definition("location_view", config_dir)

    assert definition.view_key == "location_view"
    assert definition.view_name == "Location View"
    assert definition.source_fixtures == ("tests/fixtures/places/Atlantia_Lore.md",)
    assert definition.hidden_elements == ("file_name",)
    assert definition.unhidden_elements == ("h1", "h2", "h3")
    assert definition.columns == (("source_files", "h1", "places"), ("linked_characters",))
    assert definition.graphviz_view == "heading_view"
    assert definition.projection == "place_lore_graph"
    assert definition.source_predicate == "places"
    assert definition.column_layout == "place_lore_directory"
    assert definition.source_key == "location_view_source_file"
    assert definition.heading_key == "location_view_heading"
    assert definition.include_all_heading_option is True
    assert definition.source_empty_message == "Add Place Lore."
    assert definition.heading_empty_message == "Add Headings."
    assert definition.graph_empty_message == "No graph."


def test_knowledge_view_config_requires_graphviz_view(tmp_path):
    config_dir = tmp_path / "knowledge_views"
    config_dir.mkdir()
    (config_dir / "character_view.json").write_text(
        json.dumps(
            {
                "schema_version": "0.1.0",
                "view_name": "Character View",
                "source_fixtures": ["tests/fixtures/character_sheets"],
                "hidden_elements": [],
                "unhidden_elements": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="graphviz_view"):
        load_knowledge_view_definition("character_view", config_dir)
