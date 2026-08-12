import json

from src.graph.graphviz_config import load_graphviz_config


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
    config = load_graphviz_config("character_view")

    assert config["node_type_overrides"]["artifact"] == {
        "shape": "hexagon",
        "fillcolor": "#fce7f3",
    }


def test_location_and_session_graphviz_configs_inherit_directory_view():
    directory_config = load_graphviz_config("directory_view")
    location_config = load_graphviz_config("location_view")
    session_config = load_graphviz_config("session_view")

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


def test_graphviz_view_configs_use_nested_column_arrays():
    assert load_graphviz_config("character_view")["columns"] == [
        ["family_names", "artifacts", "groups"],
        ["main_characters"],
        ["secondary_characters", "places"],
    ]
    assert load_graphviz_config("party_view_fixture")["columns"] == [
        ["family_names", "artifacts", "groups"],
        ["main_characters"],
        ["secondary_characters", "places"],
    ]
    assert load_graphviz_config("directory_view")["columns"] == [
        ["source_files", "h1"],
        ["h2"],
        ["h3"],
        ["places"],
        ["groups"],
        ["artifacts"],
        ["linked_characters"],
    ]
    assert load_graphviz_config("location_view")["columns"] == [
        ["source_files", "h1"],
        ["h2"],
        ["h3"],
        ["places"],
        ["groups"],
        ["artifacts"],
        ["linked_characters"],
    ]
    assert load_graphviz_config("session_view")["columns"] == [
        ["source_files"],
        ["h1", "places"],
        ["h2", "groups", "artifacts"],
        ["h3"],
        ["linked_characters"],
    ]
    assert load_graphviz_config("full_knowledge_graph")["columns"] == [
        ["source_files", "h1"],
        ["h2"],
        ["h3"],
        ["places"],
        ["groups", "family_names", "artifacts"],
        ["main_characters"],
        ["secondary_characters"],
    ]
