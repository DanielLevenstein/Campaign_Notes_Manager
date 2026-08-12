from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXTRACTION_CONFIG = PROJECT_ROOT / "config" / "extraction" / "normalization.json"


@dataclass(frozen=True)
class RelationshipRuleConfig:
    relationship_type: str
    label: str
    sentiment: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class CharacterExtractionConfig:
    name_pattern: str
    heading_pattern: str
    sentence_pattern: str
    honorific_words: frozenset[str]
    unknown_values: frozenset[str]
    non_name_words: frozenset[str]
    place_suffixes: frozenset[str]
    motivation_patterns: tuple[str, ...]
    relationship_rules: tuple[RelationshipRuleConfig, ...]
    trait_words: frozenset[str]
    generated_evidence_max_length: int
    session_non_entity_starts: frozenset[str]
    session_generic_entities: frozenset[str]
    session_rejected_name_parts: frozenset[str]
    session_place_words: frozenset[str]
    session_artifact_words: frozenset[str]
    session_canonical_names: dict[str, str]
    session_canonical_family_names: dict[str, str]
    session_entity_pattern: str
    session_group_pattern: str
    session_family_heading_pattern: str
    session_sentence_pattern: str
    session_max_derived_characters: int
    session_max_derived_places: int
    session_max_derived_groups: int
    session_max_derived_artifacts: int

    @property
    def generic_place_names(self) -> frozenset[str]:
        return frozenset(suffix.lower() for suffix in self.place_suffixes)


@lru_cache(maxsize=1)
def load_character_extraction_config(path: Path = DEFAULT_EXTRACTION_CONFIG) -> CharacterExtractionConfig:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid character extraction config JSON at {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Character extraction config at {path} must contain a JSON object.")
    return character_extraction_config_from_payload(payload)


def character_extraction_config_from_payload(payload: dict[str, Any]) -> CharacterExtractionConfig:
    patterns = object_value(payload, "patterns")
    session_entities = object_value(payload, "session_entity_normalization")
    session_patterns = object_value(session_entities, "patterns")
    session_limits = object_value(session_entities, "max_derived")
    return CharacterExtractionConfig(
        name_pattern=string_value(patterns, "name"),
        heading_pattern=string_value(patterns, "heading"),
        sentence_pattern=string_value(patterns, "sentence"),
        honorific_words=string_set(payload, "honorific_words"),
        unknown_values=string_set(payload, "unknown_values"),
        non_name_words=string_set(payload, "non_name_words"),
        place_suffixes=string_set(payload, "place_suffixes"),
        motivation_patterns=string_tuple(payload, "motivation_patterns"),
        relationship_rules=relationship_rules(payload),
        trait_words=string_set(payload, "trait_words"),
        generated_evidence_max_length=positive_int(payload, "generated_evidence_max_length"),
        session_non_entity_starts=string_set(session_entities, "non_entity_starts"),
        session_generic_entities=string_set(session_entities, "generic_entities"),
        session_rejected_name_parts=string_set(session_entities, "rejected_name_parts"),
        session_place_words=string_set(session_entities, "place_words"),
        session_artifact_words=string_set(session_entities, "artifact_words"),
        session_canonical_names=string_map(session_entities, "canonical_names"),
        session_canonical_family_names=string_map(session_entities, "canonical_family_names"),
        session_entity_pattern=string_value(session_patterns, "entity"),
        session_group_pattern=string_value(session_patterns, "group"),
        session_family_heading_pattern=string_value(session_patterns, "family_heading"),
        session_sentence_pattern=string_value(session_patterns, "sentence"),
        session_max_derived_characters=positive_int(session_limits, "characters"),
        session_max_derived_places=positive_int(session_limits, "places"),
        session_max_derived_groups=positive_int(session_limits, "groups"),
        session_max_derived_artifacts=positive_int(session_limits, "artifacts"),
    )


def relationship_rules(payload: dict[str, Any]) -> tuple[RelationshipRuleConfig, ...]:
    values = payload.get("relationship_rules")
    if not isinstance(values, list) or not values:
        raise ValueError("Character extraction config must include a non-empty `relationship_rules` list.")
    rules: list[RelationshipRuleConfig] = []
    for item in values:
        if not isinstance(item, dict):
            raise ValueError("Relationship rules must be objects.")
        rules.append(
            RelationshipRuleConfig(
                relationship_type=string_value(item, "type"),
                label=string_value(item, "label"),
                sentiment=string_value(item, "sentiment"),
                keywords=string_tuple(item, "keywords"),
            )
        )
    return tuple(rules)


def object_value(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Character extraction config must include a `{key}` object.")
    return value


def string_value(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Character extraction config `{key}` must be a non-empty string.")
    return value.strip()


def string_tuple(payload: dict[str, Any], key: str) -> tuple[str, ...]:
    return tuple(sorted(string_set(payload, key)))


def string_set(payload: dict[str, Any], key: str) -> frozenset[str]:
    values = payload.get(key)
    if not isinstance(values, list) or not values:
        raise ValueError(f"Character extraction config must include a non-empty `{key}` list.")
    cleaned = [str(value).strip() for value in values if str(value).strip()]
    if not cleaned:
        raise ValueError(f"Character extraction config `{key}` must include non-empty strings.")
    return frozenset(cleaned)


def string_map(payload: dict[str, Any], key: str) -> dict[str, str]:
    values = payload.get(key)
    if not isinstance(values, dict) or not values:
        raise ValueError(f"Character extraction config must include a non-empty `{key}` object.")
    cleaned = {
        str(raw_key).strip(): str(raw_value).strip()
        for raw_key, raw_value in values.items()
        if str(raw_key).strip() and str(raw_value).strip()
    }
    if not cleaned:
        raise ValueError(f"Character extraction config `{key}` must include non-empty strings.")
    return cleaned


def positive_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"Character extraction config `{key}` must be a positive integer.")
    return value
