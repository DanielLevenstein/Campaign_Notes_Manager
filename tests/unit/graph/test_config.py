import pytest

from src.graph.config import character_graph_config_from_dict, load_character_graph_config


def test_character_graph_config_loads_edges_and_nodes_from_split_config():
    config = load_character_graph_config()

    assert "artifact" in config.relationships
    assert "investigate" in config.relationships
    assert "artifact" in config.valid_edge_types
    assert config.edge_label("investigate") == "Investigate"
    assert config.canonical_edge_type("investigated") == "investigate"
    assert config.infer_edge_type_from_evidence("Jory investigated the cult.", "Mentioned") == "investigate"
    assert config.node_buckets["entity"] == "characters"


def test_character_graph_config_rejects_duplicate_edge_types_across_buckets():
    with pytest.raises(ValueError, match="appears in both"):
        character_graph_config_from_dict(
            {
                "schema_version": "0.3.0",
                "relationships": ["artifact"],
                "attributes": ["artifact"],
                "places": ["place"],
            }
        )
