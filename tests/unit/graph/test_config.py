import pytest

from src.graph.config import (
    DEFAULT_NODE_NORMALIZATION_CONFIG,
    character_graph_config_from_dict,
    load_character_graph_config,
    load_combined_graph_aliases,
    load_node_normalization_config,
    node_normalization_config_from_payload,
)


def test_character_graph_config_loads_edges_and_nodes_from_split_config():
    config = load_character_graph_config()

    assert "artifact" in config.relationships
    assert "investigate" in config.relationships
    assert "artifact" in config.valid_edge_types
    assert config.edge_label("investigate") == "Investigate"
    assert config.canonical_edge_type("investigated") == "investigate"
    assert config.infer_edge_type_from_evidence("Jory investigated the cult.", "Mentioned") == "investigate"
    assert config.node_buckets["entity"] == "characters"


def test_combined_graph_alias_config_loads_session_name_variants():
    aliases = load_combined_graph_aliases()

    assert aliases["typhon"] == frozenset({"Typheb", "Typhen", "Typhin"})
    assert aliases["sauriv"] == frozenset({"Sauriv-Isk", "Surriv"})


def test_node_normalization_config_loads_descriptor_suffixes_and_type_precedence():
    config = load_node_normalization_config()

    assert "Lore" in config.descriptor_suffixes
    assert DEFAULT_NODE_NORMALIZATION_CONFIG.name == "normalization.json"
    assert config.type_precedence["place"] > config.type_precedence["group"]
    assert config.type_precedence["group"] > config.type_precedence["character"]


def test_node_normalization_config_rejects_non_integer_precedence():
    with pytest.raises(ValueError, match="must be an integer"):
        node_normalization_config_from_payload(
            {
                "schema_version": "0.3.0",
                "descriptor_suffixes": ["Lore"],
                "type_precedence": {"place": "high"},
            }
        )


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
