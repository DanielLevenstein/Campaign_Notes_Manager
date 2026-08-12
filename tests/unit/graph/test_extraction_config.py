import pytest

from src.extraction.config import (
    DEFAULT_EXTRACTION_CONFIG,
    character_extraction_config_from_payload,
    load_character_extraction_config,
)


def test_character_extraction_config_uses_normalization_config_name():
    assert DEFAULT_EXTRACTION_CONFIG.name == "normalization.json"


def test_character_extraction_config_loads_constants_from_json():
    config = load_character_extraction_config()

    assert config.name_pattern.startswith("\\b(")
    assert "Mr" in config.honorific_words
    assert "Mage College" in config.place_suffixes
    assert config.generic_place_names >= {"academy", "mage college"}
    assert config.generated_evidence_max_length == 240
    assert config.relationship_rules[0].relationship_type == "betrayer"
    assert "betray" in config.relationship_rules[0].keywords


def test_character_extraction_config_rejects_missing_relationship_rules():
    with pytest.raises(ValueError, match="relationship_rules"):
        character_extraction_config_from_payload(
            {
                "patterns": {
                    "name": "name",
                    "heading": "heading",
                    "sentence": "sentence",
                },
                "honorific_words": ["Mr"],
                "unknown_values": ["unknown"],
                "non_name_words": ["The"],
                "place_suffixes": ["City"],
                "motivation_patterns": ["motivation"],
                "trait_words": ["brave"],
                "generated_evidence_max_length": 240,
            }
        )
