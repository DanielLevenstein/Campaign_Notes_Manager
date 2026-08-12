import json
from pathlib import Path

from src.graph.graphviz_config import load_graphviz_config


TEST_FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"
TEST_GRAPHVIZ_CONFIG_DIR = TEST_FIXTURES_DIR / "graphviz"
TEST_GRAPH_VIEW_SCENARIO_DIR = TEST_FIXTURES_DIR / "graph_views"


def test_load_graphviz_config_merges_global_then_view_override(tmp_path):
    config_dir = tmp_path / "graphviz"
    config_dir.mkdir()
    (config_dir / "global_graph_view.json").write_text(
        json.dumps(
            {
                "graph": {"bgcolor": "transparent", "splines": "line"},
                "spacing": {"small_graph": {"max_nodes": 8, "ranksep": 1.15, "nodesep": 0.4}},
                "node_type_overrides": {
                    "family": {"shape": "folder", "fillcolor": "#fef3c7"},
                    "place": {"shape": "component", "fillcolor": "#dcfce7"},
                },
            }
        ),
        encoding="utf-8",
    )
    (config_dir / "character_view.json").write_text(
        json.dumps(
            {
                "graph": {"rankdir": "LR"},
                "node_type_overrides": {
                    "family": {"fillcolor": "#fff7ed"},
                },
            }
        ),
        encoding="utf-8",
    )

    config = load_graphviz_config("character_view", config_dir)

    assert config["graph"] == {
        "bgcolor": "transparent",
        "splines": "line",
        "rankdir": "LR",
    }
    assert config["spacing"] == {
        "small_graph": {
            "max_nodes": 8,
            "ranksep": 1.15,
            "nodesep": 0.4,
        }
    }
    assert config["node_type_overrides"]["family"] == {
        "shape": "folder",
        "fillcolor": "#fff7ed",
    }
    assert config["node_type_overrides"]["place"] == {
        "shape": "component",
        "fillcolor": "#dcfce7",
    }


def test_load_graphviz_config_recursively_merges_parent_view_config(tmp_path):
    config_dir = tmp_path / "graphviz"
    config_dir.mkdir()
    (config_dir / "global_graph_view.json").write_text(
        json.dumps(
            {
                "graph": {"bgcolor": "transparent", "splines": "line"},
                "node": {"shape": "box"},
                "spacing": {"column_layout": {"ranksep": 0.65, "nodesep": 0.35}},
            }
        ),
        encoding="utf-8",
    )
    (config_dir / "directory_view.json").write_text(
        json.dumps(
            {
                "inherits": "config/graphviz/global_graph_view.json",
                "graph": {"rankdir": "LR"},
                "spacing": {"column_layout": {"ranksep": 0.75}},
                "columns": [["source_files", "h1"], ["linked_characters"]],
            }
        ),
        encoding="utf-8",
    )
    (config_dir / "session_view.json").write_text(
        json.dumps(
            {
                "inherits": "config/graphviz/directory_view.json",
                "columns": [["source_files"], ["h1"], ["linked_characters"]],
            }
        ),
        encoding="utf-8",
    )

    config = load_graphviz_config("session_view", config_dir)

    assert config["graph"] == {
        "bgcolor": "transparent",
        "splines": "line",
        "rankdir": "LR",
    }
    assert config["node"] == {"shape": "box"}
    assert config["spacing"]["column_layout"] == {
        "ranksep": 0.75,
        "nodesep": 0.35,
    }
    assert config["columns"] == [["source_files"], ["h1"], ["linked_characters"]]


def test_global_graphviz_config_includes_artifact_node_override():
    config = load_graphviz_config("character_view", TEST_GRAPHVIZ_CONFIG_DIR)

    assert config["node_type_overrides"]["artifact"] == {
        "shape": "hexagon",
        "fillcolor": "#fce7f3",
    }


def test_graphviz_config_fixtures_are_separate_from_graph_view_scenarios():
    graphviz_config = load_graphviz_config("session_view", TEST_GRAPHVIZ_CONFIG_DIR)
    scenario = json.loads(
        (TEST_GRAPH_VIEW_SCENARIO_DIR / "session_notes_graph_place_lore.json").read_text(
            encoding="utf-8",
        )
    )

    assert graphviz_config["config_scope"] == "knowledge_view"
    assert graphviz_config["view_key"] == "session_view"
    assert "source_fixtures" not in graphviz_config
    assert scenario["fixture_type"] == "knowledge_graph_view"
    assert scenario["source_fixtures"] == [
        "tests/fixtures/character_sheets",
        "tests/fixtures/session_notes/Family_Tree.md",
    ]
    assert "config_scope" not in scenario


def test_full_structured_graph_config_preserves_legacy_column_grouping():
    config = load_graphviz_config("full_structured_graph", TEST_GRAPHVIZ_CONFIG_DIR)

    assert config["view_key"] == "full_structured_graph"
    assert "columns" not in config
    assert config["graph"]["rankdir"] == "LR"


def test_location_and_session_graphviz_configs_inherit_directory_view(tmp_path):
    config_dir = tmp_path / "graphviz"
    config_dir.mkdir()
    (config_dir / "global_graph_view.json").write_text(
        json.dumps(
            {
                "graph": {"bgcolor": "transparent", "splines": "line"},
                "node": {"shape": "box"},
                "edge": {"label_attribute": "label"},
            }
        ),
        encoding="utf-8",
    )
    (config_dir / "directory_view.json").write_text(
        json.dumps(
            {
                "view_key": "directory_view",
                "label": "Directory View",
                "inherits": "config/graphviz/global_graph_view.json",
                "graph": {"rankdir": "LR"},
            }
        ),
        encoding="utf-8",
    )
    (config_dir / "location_view.json").write_text(
        json.dumps(
            {
                "view_key": "location_view",
                "label": "Location View",
                "inherits": "config/graphviz/directory_view.json",
            }
        ),
        encoding="utf-8",
    )
    (config_dir / "session_view.json").write_text(
        json.dumps(
            {
                "view_key": "session_view",
                "label": "Session View",
                "inherits": "config/graphviz/directory_view.json",
            }
        ),
        encoding="utf-8",
    )

    directory_config = load_graphviz_config("directory_view", config_dir)
    location_config = load_graphviz_config("location_view", config_dir)
    session_config = load_graphviz_config("session_view", config_dir)

    assert directory_config["view_key"] == "directory_view"
    assert location_config["view_key"] == "location_view"
    assert session_config["view_key"] == "session_view"
    assert location_config["label"] == "Location View"
    assert session_config["label"] == "Session View"
    assert location_config["graph"]["rankdir"] == "LR"
    assert session_config["graph"]["rankdir"] == "LR"
    assert session_config["graph"]["splines"] == "line"
    assert session_config["node"]["shape"] == "box"
    assert session_config["edge"]["label_attribute"] == "label"


def test_graphviz_view_configs_use_nested_column_arrays(tmp_path):
    config_dir = tmp_path / "graphviz"
    config_dir.mkdir()
    (config_dir / "global_graph_view.json").write_text("{}", encoding="utf-8")
    view_columns = {
        "character_view": [
            ["family_names", "artifacts", "groups"],
            ["main_characters"],
            ["secondary_characters", "places"],
        ],
        "party_view_fixture": [
            ["family_names", "artifacts", "groups"],
            ["main_characters"],
            ["secondary_characters", "places"],
        ],
        "directory_view": [
            ["source_files", "h1"],
            ["h2"],
            ["h3"],
            ["places"],
            ["groups"],
            ["artifacts"],
            ["linked_characters"],
        ],
        "location_view": [
            ["source_files", "h1", "places"],
            ["h2"],
            ["h3"],
            ["groups"],
            ["artifacts"],
            ["linked_characters"],
        ],
        "session_view": [
            ["source_files"],
            ["h1", "places"],
            ["h2", "groups", "artifacts"],
            ["h3"],
            ["main_characters"],
            ["secondary_characters"],
        ],
        "full_knowledge_graph": [
            ["source_files", "h1"],
            ["h2"],
            ["h3"],
            ["places"],
            ["groups", "family_names", "artifacts"],
            ["main_characters"],
            ["secondary_characters"],
        ],
    }
    for view_key, columns in view_columns.items():
        (config_dir / f"{view_key}.json").write_text(
            json.dumps({"columns": columns}),
            encoding="utf-8",
        )

    assert load_graphviz_config("character_view", config_dir)["columns"] == [
        ["family_names", "artifacts", "groups"],
        ["main_characters"],
        ["secondary_characters", "places"],
    ]
    assert load_graphviz_config("party_view_fixture", config_dir)["columns"] == [
        ["family_names", "artifacts", "groups"],
        ["main_characters"],
        ["secondary_characters", "places"],
    ]
    assert load_graphviz_config("directory_view", config_dir)["columns"] == [
        ["source_files", "h1"],
        ["h2"],
        ["h3"],
        ["places"],
        ["groups"],
        ["artifacts"],
        ["linked_characters"],
    ]
    assert load_graphviz_config("location_view", config_dir)["columns"] == [
        ["source_files", "h1", "places"],
        ["h2"],
        ["h3"],
        ["groups"],
        ["artifacts"],
        ["linked_characters"],
    ]
    assert load_graphviz_config("session_view", config_dir)["columns"] == [
        ["source_files"],
        ["h1", "places"],
        ["h2", "groups", "artifacts"],
        ["h3"],
        ["main_characters"],
        ["secondary_characters"],
    ]
    assert load_graphviz_config("full_knowledge_graph", config_dir)["columns"] == [
        ["source_files", "h1"],
        ["h2"],
        ["h3"],
        ["places"],
        ["groups", "family_names", "artifacts"],
        ["main_characters"],
        ["secondary_characters"],
    ]
