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


def test_global_graphviz_config_includes_artifact_node_override():
    config = load_graphviz_config("character_view")

    assert config["node_type_overrides"]["artifact"] == {
        "shape": "hexagon",
        "fillcolor": "#fce7f3",
    }


def test_directory_graphviz_config_exists_for_location_and_session_views():
    config = load_graphviz_config("directory_view")

    assert config["view_key"] == "directory_view"
    assert config["label"] == "Directory View"
    assert config["graph"]["rankdir"] == "LR"
