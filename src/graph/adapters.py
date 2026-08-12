from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from .models import CanonicalEdge, CanonicalGraph, CanonicalNode
from .source_paths import normalize_source_file


LEGACY_TYPE_MAP = {
    "character": "character",
    "place": "place",
    "family": "family",
    "group": "group",
    "artifact": "artifact",
    "note": "note",
    "source_document": "source_document",
}


def canonical_type_for_legacy_node(node_type: str, source_file: str = "", display_name: str = "") -> str:
    cleaned = (node_type or "").strip().lower()
    if cleaned.startswith("source_heading"):
        return "markdown_heading"
    if cleaned in LEGACY_TYPE_MAP:
        return LEGACY_TYPE_MAP[cleaned]
    if canonical_source_kind(source_file) == "session_note" and display_name.strip().lower().startswith("session"):
        return "note"
    return "entity"


def canonical_source_kind(source_file: str | Path) -> str:
    normalized = str(source_file).replace("\\", "/").casefold()
    parts = [part for part in normalized.split("/") if part]
    if "character_sheets" in parts:
        return "character_sheet"
    if "places" in parts:
        return "place_lore"
    if "session_notes" in parts:
        return "session_note"
    return "unknown"


def canonical_node_from_legacy(node: Any, *, root: str | Path | None = None) -> CanonicalNode:
    source_file = normalize_source_file(getattr(node, "source_file", "") or "", root=root) if getattr(node, "source_file", "") else ""
    legacy_type = getattr(node, "node_type", "")
    display_name = getattr(node, "name", getattr(node, "display_name", getattr(node, "id", "")))
    return CanonicalNode(
        id=getattr(node, "id"),
        canonical_type=canonical_type_for_legacy_node(legacy_type, source_file, display_name),
        display_name=display_name,
        source_file=source_file,
        source_id=getattr(node, "id"),
        properties={
            "legacy_node_type": legacy_type,
        },
        provenance={
            "adapter": "combined_character_graph",
            "source_kind": canonical_source_kind(source_file),
        },
    )


def canonical_edge_from_legacy(edge: Any) -> CanonicalEdge:
    relation_type = one_word_relation(getattr(edge, "relationship_type", "reference"))
    evidence = tuple(value for value in getattr(edge, "evidence", ()) if value)
    return CanonicalEdge(
        id=canonical_edge_id(getattr(edge, "source"), getattr(edge, "target"), relation_type),
        source_id=getattr(edge, "source"),
        target_id=getattr(edge, "target"),
        relation_type=relation_type,
        relation_label=getattr(edge, "relationship_label", "") or relation_type.replace("_", " ").title(),
        evidence=evidence,
        properties={
            "bidirectional": bool(getattr(edge, "bidirectional", False)),
        },
        provenance={
            "adapter": "combined_character_graph",
        },
    )


def canonical_node_from_character_graph(
    node_id: str,
    node: Any,
    *,
    node_type: str,
    source_file: str,
    root: str | Path | None = None,
) -> CanonicalNode:
    normalized_source = normalize_source_file(source_file, root=root) if source_file else ""
    display_name = getattr(node, "name", getattr(node, "value", node_id))
    properties: dict[str, object] = {"legacy_node_type": node_type}
    aliases = getattr(node, "aliases", None)
    if aliases:
        properties["aliases"] = list(aliases)
    source_spans = getattr(node, "source_spans", None)
    if source_spans:
        properties["source_spans"] = list(source_spans)
    if node_type == "attribute":
        properties["attribute_type"] = getattr(node, "attribute_type", "")
    if node_type == "place":
        properties["place_type"] = getattr(node, "place_type", "")
    return CanonicalNode(
        id=node_id,
        canonical_type=canonical_type_for_character_graph_node(node_type, source_file, display_name),
        display_name=display_name,
        source_file=normalized_source,
        source_id=node_id,
        properties=properties,
        provenance={
            "adapter": "character_graph",
            "source_kind": canonical_source_kind(normalized_source),
        },
    )


def canonical_type_for_character_graph_node(node_type: str, source_file: str = "", display_name: str = "") -> str:
    if node_type == "attribute":
        return "entity"
    return canonical_type_for_legacy_node(node_type, source_file, display_name)


def canonical_edge_from_character_graph(edge: Any) -> CanonicalEdge:
    relation_type = one_word_relation(getattr(edge, "relationship_type", "reference"))
    evidence = tuple(value for value in getattr(edge, "evidence", ()) if value)
    return CanonicalEdge(
        id=canonical_edge_id(getattr(edge, "source"), getattr(edge, "target"), relation_type),
        source_id=getattr(edge, "source"),
        target_id=getattr(edge, "target"),
        relation_type=relation_type,
        relation_label=getattr(edge, "relationship_label", "") or relation_type.replace("_", " ").title(),
        evidence=evidence,
        properties={
            "sentiment": getattr(edge, "sentiment", "unknown"),
            "trust_level": getattr(edge, "trust_level", 0.5),
            "conflict_level": getattr(edge, "conflict_level", 0.0),
            "emotional_weight": getattr(edge, "emotional_weight", 0.4),
        },
        provenance={
            "adapter": "character_graph",
        },
    )


def canonical_graph_from_character_graph(graph: Any, *, root: str | Path | None = None) -> CanonicalGraph:
    source_file = getattr(getattr(graph, "primary_character", None), "source_file", "")
    nodes: dict[str, CanonicalNode] = {}
    for node_id, node in getattr(graph, "characters", {}).items():
        nodes[node_id] = canonical_node_from_character_graph(
            node_id,
            node,
            node_type=getattr(node, "node_type", "character"),
            source_file=source_file,
            root=root,
        )
    for node_id, node in getattr(graph, "attributes", {}).items():
        nodes[node_id] = canonical_node_from_character_graph(
            node_id,
            node,
            node_type="attribute",
            source_file=source_file,
            root=root,
        )
    for node_id, node in getattr(graph, "places", {}).items():
        nodes[node_id] = canonical_node_from_character_graph(
            node_id,
            node,
            node_type="place",
            source_file=source_file,
            root=root,
        )
    edges = {
        canonical_edge_from_character_graph(edge).id: canonical_edge_from_character_graph(edge)
        for edge in getattr(graph, "relationships", [])
    }
    return CanonicalGraph(nodes=nodes, edges=edges)


def canonical_graph_from_combined(graph: Any, *, root: str | Path | None = None) -> CanonicalGraph:
    nodes = {
        node_id: canonical_node_from_legacy(node, root=root)
        for node_id, node in getattr(graph, "characters", {}).items()
    }
    edges = {
        canonical_edge_from_legacy(edge).id: canonical_edge_from_legacy(edge)
        for edge in getattr(graph, "edges", [])
    }
    return CanonicalGraph(nodes=nodes, edges=edges)


def canonical_edge_id(source_id: str, target_id: str, relation_type: str) -> str:
    raw = f"{source_id}|{target_id}|{relation_type}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"edge_{safe_token(source_id)}_{safe_token(target_id)}_{safe_token(relation_type)}_{digest}"


def one_word_relation(value: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", value.lower())
    return words[0] if words else "reference"


def safe_token(value: str) -> str:
    token = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return token[:40] or "unknown"
