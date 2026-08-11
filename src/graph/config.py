from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHARACTER_GRAPH_CONFIG = PROJECT_ROOT / "config" / "character_graph.json"
DEFAULT_EDGE_CONFIG = PROJECT_ROOT / "config" / "edges" / "character_graph.json"
DEFAULT_NODE_CONFIG = PROJECT_ROOT / "config" / "nodes" / "character_graph.json"
DEFAULT_COMBINED_GRAPH_ALIAS_CONFIG = PROJECT_ROOT / "config" / "aliases" / "combined_graph.json"
CONFIG_BUCKETS = ("relationships", "attributes", "places")


@dataclass(frozen=True)
class EdgeTypeConfig:
    type: str
    label: str
    category: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class CharacterGraphConfig:
    schema_version: str
    relationships: frozenset[str]
    attributes: frozenset[str]
    places: frozenset[str]
    edge_types: dict[str, EdgeTypeConfig] | None = None
    node_buckets: dict[str, str] | None = None

    @property
    def valid_edge_types(self) -> frozenset[str]:
        return self.relationships | self.attributes | self.places

    def edge_label(self, edge_type: str) -> str:
        edge = (self.edge_types or {}).get(edge_type.strip().lower())
        return edge.label if edge else edge_type.replace("_", " ").title()

    def canonical_edge_type(self, value: str) -> str | None:
        key = normalize_edge_key(value)
        if key in self.valid_edge_types:
            return key
        for edge_type, edge in (self.edge_types or {}).items():
            candidates = {edge.label, edge.type, *edge.aliases}
            if key in {normalize_edge_key(candidate) for candidate in candidates}:
                return edge_type
        return None

    def infer_edge_type_from_evidence(self, evidence: str, fallback: str = "reference") -> str:
        normalized_evidence = evidence.casefold()
        matches: list[tuple[int, str]] = []
        for edge_type, edge in (self.edge_types or {}).items():
            candidates = list(edge.aliases)
            for candidate in candidates:
                cleaned = candidate.strip()
                if cleaned and cleaned.casefold() in normalized_evidence:
                    matches.append((len(cleaned), edge_type))
        if matches:
            return sorted(matches, reverse=True)[0][1]
        return self.canonical_edge_type(fallback) or "reference"


@lru_cache(maxsize=1)
def load_combined_graph_aliases(path: Path = DEFAULT_COMBINED_GRAPH_ALIAS_CONFIG) -> dict[str, frozenset[str]]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid combined graph alias config JSON at {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Combined graph alias config at {path} must contain a JSON object.")
    return combined_graph_aliases_from_payload(payload)


def combined_graph_aliases_from_payload(payload: dict[str, Any]) -> dict[str, frozenset[str]]:
    variants = payload.get("session_name_variants", {})
    if not isinstance(variants, dict):
        raise ValueError("Combined graph alias config must contain a `session_name_variants` object.")
    aliases: dict[str, frozenset[str]] = {}
    for canonical_name, raw_aliases in variants.items():
        canonical_key = normalize_edge_key(str(canonical_name))
        if not canonical_key:
            raise ValueError("Session name variant keys must be non-empty strings.")
        if not isinstance(raw_aliases, list):
            raise ValueError(f"Session name variants for `{canonical_name}` must be a list.")
        aliases[canonical_key] = frozenset(
            str(alias).strip()
            for alias in raw_aliases
            if str(alias).strip()
        )
    return aliases


def load_character_graph_config(
    path: Path = DEFAULT_CHARACTER_GRAPH_CONFIG,
    *,
    edge_path: Path = DEFAULT_EDGE_CONFIG,
    node_path: Path = DEFAULT_NODE_CONFIG,
) -> CharacterGraphConfig:
    if edge_path.exists() and node_path.exists():
        return character_graph_config_from_split_files(edge_path, node_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid character graph config JSON at {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Character graph config at {path} must contain a JSON object.")
    return character_graph_config_from_dict(payload)


def character_graph_config_from_split_files(edge_path: Path, node_path: Path) -> CharacterGraphConfig:
    try:
        edge_payload = json.loads(edge_path.read_text(encoding="utf-8"))
        node_payload = json.loads(node_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid graph config JSON: {exc}") from exc
    edges = edge_types_from_payload(edge_payload)
    node_buckets = node_buckets_from_payload(node_payload)
    buckets: dict[str, set[str]] = {bucket: set() for bucket in CONFIG_BUCKETS}
    for edge in edges.values():
        if edge.category not in buckets:
            raise ValueError(f"Unknown edge category `{edge.category}` for `{edge.type}`.")
        buckets[edge.category].add(edge.type)
    schema_version = str(edge_payload.get("schema_version") or node_payload.get("schema_version") or "").strip()
    if not schema_version:
        raise ValueError("Graph config must include a non-empty schema_version.")
    return CharacterGraphConfig(
        schema_version=schema_version,
        relationships=frozenset(buckets["relationships"]),
        attributes=frozenset(buckets["attributes"]),
        places=frozenset(buckets["places"]),
        edge_types=edges,
        node_buckets=node_buckets,
    )


def edge_types_from_payload(payload: dict[str, Any]) -> dict[str, EdgeTypeConfig]:
    values = payload.get("edges")
    if not isinstance(values, list) or not values:
        raise ValueError("Edge config must include a non-empty `edges` list.")
    edges: dict[str, EdgeTypeConfig] = {}
    for item in values:
        if not isinstance(item, dict):
            raise ValueError("Edge config entries must be objects.")
        edge_type = normalize_edge_key(str(item.get("type", "")))
        label = str(item.get("label", "")).strip()
        category = str(item.get("category", "")).strip().lower()
        aliases = item.get("aliases", [])
        if not edge_type or not label or not category:
            raise ValueError("Edge config entries must include type, label, and category.")
        if edge_type in edges:
            raise ValueError(f"Duplicate edge type: {edge_type}.")
        if not isinstance(aliases, list):
            raise ValueError(f"Edge aliases for `{edge_type}` must be a list.")
        edges[edge_type] = EdgeTypeConfig(
            type=edge_type,
            label=label,
            category=category,
            aliases=tuple(str(alias).strip() for alias in aliases if str(alias).strip()),
        )
    return edges


def node_buckets_from_payload(payload: dict[str, Any]) -> dict[str, str]:
    values = payload.get("nodes")
    if not isinstance(values, list) or not values:
        raise ValueError("Node config must include a non-empty `nodes` list.")
    buckets: dict[str, str] = {}
    for item in values:
        if not isinstance(item, dict):
            raise ValueError("Node config entries must be objects.")
        node_type = normalize_edge_key(str(item.get("type", "")))
        bucket = str(item.get("bucket", "")).strip().lower()
        if not node_type or not bucket:
            raise ValueError("Node config entries must include type and bucket.")
        buckets[node_type] = bucket
    return buckets


def character_graph_config_from_dict(payload: dict[str, Any]) -> CharacterGraphConfig:
    schema_version = payload.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version.strip():
        raise ValueError("Character graph config must include a non-empty schema_version.")
    buckets: dict[str, frozenset[str]] = {}
    seen: dict[str, str] = {}
    for bucket_name in CONFIG_BUCKETS:
        values = payload.get(bucket_name)
        if not isinstance(values, list) or not values:
            raise ValueError(f"Character graph config must include a non-empty `{bucket_name}` list.")
        normalized_values: list[str] = []
        for value in values:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"`{bucket_name}` entries must be non-empty strings.")
            normalized = value.strip().lower()
            if normalized in normalized_values:
                raise ValueError(f"Duplicate `{bucket_name}` entry: {normalized}.")
            if normalized in seen:
                raise ValueError(
                    f"Connection type `{normalized}` appears in both `{seen[normalized]}` and `{bucket_name}`."
                )
            normalized_values.append(normalized)
            seen[normalized] = bucket_name
        buckets[bucket_name] = frozenset(normalized_values)
    return CharacterGraphConfig(
        schema_version=schema_version.strip(),
        relationships=buckets["relationships"],
        attributes=buckets["attributes"],
        places=buckets["places"],
    )


def normalize_edge_key(value: str) -> str:
    return "_".join(part for part in value.strip().lower().replace("-", " ").split() if part)
