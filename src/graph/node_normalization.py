from __future__ import annotations

import re
from dataclasses import replace

from src.graph.config import NodeNormalizationConfig, load_node_normalization_config
from src.graph.schema import (
    AttributeNode,
    CharacterGraph,
    CharacterNode,
    EmbeddingRecord,
    PlaceNode,
)


def normalize_graph_nodes(
    graph: CharacterGraph,
    *,
    config: NodeNormalizationConfig | None = None,
) -> CharacterGraph:
    config = config or load_node_normalization_config()
    source_node_type = source_node_type_override(graph.primary_character.source_file)
    primary_node_type = normalized_node_type(graph.primary_character.node_type, source_node_type)
    primary_name = normalize_entity_display_name(
        graph.primary_character.name,
        primary_node_type,
        is_heading=is_heading_node_type(primary_node_type),
        config=config,
    )
    primary_character = replace(
        graph.primary_character,
        name=primary_name,
        node_type=primary_node_type,
    )

    candidates: list[tuple[str, str, CharacterNode | PlaceNode | AttributeNode]] = []
    for node_id, node in graph.characters.items():
        node_type = normalized_node_type(
            node.node_type,
            source_node_type if node_id == graph.primary_character.id else None,
        )
        candidates.append(("characters", node_id, replace(node, node_type=node_type)))
    for node_id, node in graph.places.items():
        candidates.append(("places", node_id, replace(node, node_type="place")))
    for node_id, node in graph.attributes.items():
        candidates.append(("attributes", node_id, replace(node, node_type="attribute")))

    winners = winning_nodes(candidates, primary_id=primary_character.id, config=config)
    id_map = {
        node_id: winners[node_identity_key(node_id, node, config=config)][1]
        for _, node_id, node in candidates
    }

    characters: dict[str, CharacterNode] = {}
    places: dict[str, PlaceNode] = {}
    attributes: dict[str, AttributeNode] = {}
    for key in sorted(winners, key=lambda item: winners[item][1]):
        bucket, node_id, node = winners[key]
        if bucket == "characters":
            characters[node_id] = normalize_character_node(node_id, node, primary_character.id, config=config)
        elif bucket == "places":
            places[node_id] = normalize_place_node(node, config=config)
        elif bucket == "attributes":
            attributes[node_id] = node

    relationships = [
        replace(
            relationship,
            source=id_map.get(relationship.source, relationship.source),
            target=id_map.get(relationship.target, relationship.target),
        )
        for relationship in graph.relationships
    ]
    embeddings = remap_embeddings(graph.embeddings, id_map)

    return CharacterGraph(
        schema_version=graph.schema_version,
        primary_character=primary_character,
        characters=characters,
        attributes=attributes,
        places=places,
        relationships=relationships,
        embeddings=embeddings,
        metadata=graph.metadata,
    )


def normalize_entity_display_name(
    name: str,
    node_type: str,
    is_heading: bool = False,
    *,
    config: NodeNormalizationConfig | None = None,
) -> str:
    config = config or load_node_normalization_config()
    cleaned = " ".join(name.replace("_", " ").split())
    if is_heading or is_heading_node_type(node_type):
        return cleaned
    if should_strip_descriptor_suffix(node_type):
        return strip_descriptor_suffix(cleaned, config=config)
    return cleaned


def normalized_node_type(node_type: str, source_node_type: str | None = None) -> str:
    cleaned = (node_type or "").strip().lower() or "character"
    if source_node_type == "place" and cleaned in {"character", "note", "source_document"}:
        return "place"
    if cleaned == "character" and source_node_type == "note":
        return source_node_type
    return cleaned


def source_node_type_override(source_file: str) -> str | None:
    normalized = source_file.replace("\\", "/").lower()
    parts = [part for part in normalized.split("/") if part]
    if "places" in parts:
        return "place"
    if "session_notes" in parts or normalized.endswith("/session_notes.md") or normalized.endswith("session_notes.md"):
        return "note"
    if "character_sheets" in parts:
        return "character"
    return None


def winning_nodes(
    candidates: list[tuple[str, str, CharacterNode | PlaceNode | AttributeNode]],
    *,
    primary_id: str = "",
    config: NodeNormalizationConfig,
) -> dict[tuple[str, str], tuple[str, str, CharacterNode | PlaceNode | AttributeNode]]:
    winners: dict[tuple[str, str], tuple[str, str, CharacterNode | PlaceNode | AttributeNode]] = {}
    for bucket, node_id, node in candidates:
        key = node_identity_key(node_id, node, config=config)
        current = winners.get(key)
        if current is None or candidate_rank(bucket, node_id, node, primary_id=primary_id, config=config) > candidate_rank(
            *current,
            primary_id=primary_id,
            config=config,
        ):
            winners[key] = (bucket, node_id, node)
    return winners


def node_identity_key(
    node_id: str,
    node: CharacterNode | PlaceNode | AttributeNode,
    *,
    config: NodeNormalizationConfig,
) -> tuple[str, str]:
    node_type = node_type_for_node(node)
    name = display_name_for_node(node)
    normalized_name = normalize_entity_display_name(
        name,
        node_type,
        is_heading=is_heading_node_type(node_type),
        config=config,
    )
    if identity_type(node_type) == "attribute":
        return "attribute", compact_key(f"{node_type}_{normalized_name or node_id}")
    return "canonical_node", compact_key(normalized_name or node_id)


def candidate_rank(
    bucket: str,
    node_id: str,
    node: CharacterNode | PlaceNode | AttributeNode,
    *,
    primary_id: str = "",
    config: NodeNormalizationConfig,
) -> tuple[int, int, int, int, str]:
    node_type = node_type_for_node(node)
    precedence = config.type_precedence.get(
        identity_type(node_type),
        config.type_precedence.get(node_type, 0),
    )
    source_span_count = len(getattr(node, "source_spans", []) or [])
    primary_bonus = 100 if node_id == primary_id and bucket == "characters" else 0
    bucket_bonus = {"places": 3, "characters": 2, "attributes": 1}.get(bucket, 0)
    return (
        precedence + primary_bonus,
        bucket_bonus,
        source_span_count,
        len(display_name_for_node(node)),
        node_id,
    )


def normalize_character_node(
    node_id: str,
    node: CharacterNode | PlaceNode | AttributeNode,
    primary_id: str,
    *,
    config: NodeNormalizationConfig,
) -> CharacterNode:
    if isinstance(node, CharacterNode):
        node_type = node.node_type
        role = node.role
        summary = node.summary
        motivations = node.motivations
        traits = node.traits
        alignment = node.alignment
    elif isinstance(node, PlaceNode):
        node_type = "place"
        role = node.place_type
        summary = node.summary
        motivations = []
        traits = []
        alignment = CharacterNode(name=node.name).alignment
    else:
        node_type = "attribute"
        role = node.attribute_type
        summary = node.summary
        motivations = []
        traits = []
        alignment = CharacterNode(name=node.value).alignment
    return CharacterNode(
        name=normalize_entity_display_name(
            display_name_for_node(node),
            node_type,
            is_heading=is_heading_node_type(node_type),
            config=config,
        ),
        node_type=node_type,
        aliases=list(getattr(node, "aliases", []) or []),
        role=normalized_character_role(role, node_type, node_id == primary_id),
        summary=summary,
        motivations=list(motivations),
        traits=list(traits),
        alignment=alignment,
        source_spans=list(getattr(node, "source_spans", []) or []),
    )


def normalize_place_node(
    node: CharacterNode | PlaceNode | AttributeNode,
    *,
    config: NodeNormalizationConfig,
) -> PlaceNode:
    if isinstance(node, PlaceNode):
        place_type = node.place_type
    elif isinstance(node, CharacterNode):
        place_type = node.role if node.role != "primary character" else "place"
    else:
        place_type = "place"
    return PlaceNode(
        name=normalize_entity_display_name(display_name_for_node(node), "place", config=config),
        place_type=place_type,
        aliases=list(getattr(node, "aliases", []) or []),
        summary=getattr(node, "summary", ""),
        source_spans=list(getattr(node, "source_spans", []) or []),
    )


def normalized_character_role(role: str, node_type: str, is_primary: bool) -> str:
    if is_primary and node_type == "character":
        return "primary character"
    if role == "primary character" and node_type != "character":
        return node_type
    return role


def remap_embeddings(embeddings: dict[str, EmbeddingRecord], id_map: dict[str, str]) -> dict[str, EmbeddingRecord]:
    remapped: dict[str, EmbeddingRecord] = {}
    for embedding_id, embedding in embeddings.items():
        target_id = id_map.get(embedding_id, embedding_id)
        remapped.setdefault(target_id, replace(embedding, node_id=target_id))
    return remapped


def display_name_for_node(node: CharacterNode | PlaceNode | AttributeNode) -> str:
    if isinstance(node, AttributeNode):
        return node.value
    return node.name


def node_type_for_node(node: CharacterNode | PlaceNode | AttributeNode) -> str:
    if isinstance(node, AttributeNode):
        return node.node_type
    return node.node_type


def identity_type(node_type: str) -> str:
    if is_heading_node_type(node_type):
        return "source_heading"
    return node_type


def is_heading_node_type(node_type: str) -> bool:
    return (node_type or "").strip().lower().startswith("source_heading")


def should_strip_descriptor_suffix(node_type: str) -> bool:
    return identity_type((node_type or "").strip().lower()) in {"place", "group", "source_document", "note"}


def strip_descriptor_suffix(name: str, *, config: NodeNormalizationConfig) -> str:
    cleaned = name.strip()
    for suffix in config.descriptor_suffixes:
        pattern = rf"\s+{re.escape(suffix)}$"
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned or name.strip()


def compact_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())
