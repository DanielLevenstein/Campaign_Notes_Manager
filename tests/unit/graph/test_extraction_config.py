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
    assert "They" in config.session_non_entity_starts
    assert "Cultist" in config.session_generic_entities
    assert "Ignis" in config.session_rejected_name_parts
    assert "gate" in config.session_place_words
    assert "blade" in config.session_artifact_words
    assert config.session_canonical_names["typhin"] == "Typhon"
    assert config.session_canonical_names["mrdoctor"] == "John Doctor"
    assert config.session_canonical_family_names["nighbloom"] == "Nightbloom"
    assert config.session_entity_pattern.startswith("\\b")
    assert "?P<prefix>" in config.session_group_pattern
    assert "?P<name>" in config.session_family_heading_pattern
    assert config.session_sentence_pattern == "[^.!?\\n]+[.!?]?"
    assert config.session_max_derived_characters == 18
    assert config.session_max_derived_places == 9
    assert config.session_max_derived_groups == 6
    assert config.session_max_derived_artifacts == 6


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
                "session_entity_normalization": {
                    "patterns": {
                        "entity": "entity",
                        "group": "group",
                        "family_heading": "family",
                        "sentence": "sentence",
                    },
                    "max_derived": {
                        "characters": 1,
                        "places": 1,
                        "groups": 1,
                        "artifacts": 1,
                    },
                    "non_entity_starts": ["The"],
                    "generic_entities": ["Cultist"],
                    "rejected_name_parts": ["Ignis"],
                    "place_words": ["gate"],
                    "artifact_words": ["blade"],
                    "canonical_names": {"typhin": "Typhon"},
                    "canonical_family_names": {"nighbloom": "Nightbloom"},
                },
            }
        )
