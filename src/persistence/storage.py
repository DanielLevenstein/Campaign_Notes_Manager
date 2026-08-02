from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from character_graph.schema import CharacterGraph, RelationshipEdge
from character_graph.validation import validate_graph


GRAPH_FILE_SUFFIX = ".graph.json"
SYNTHETIC_EDGE_TYPES = {"synthetic", "derived_synthetic"}


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def graph_path_for_lore_path(
    path: Path | str,
    *,
    lore_root: Path | str,
    meta_data_root: Path | str,
) -> Path:
    source = Path(path)
    root = Path(lore_root)
    meta_root = Path(meta_data_root)
    try:
        relative_path = source.resolve().relative_to(root.resolve())
    except ValueError:
        relative_path = Path(source.name)
    return meta_root / relative_path.with_suffix(GRAPH_FILE_SUFFIX)


def read_markdown(path: Path | str) -> str:
    source = Path(path)
    if not source.exists():
        return ""
    return source.read_text(encoding="utf-8")


def write_markdown(
    path: Path | str,
    content: str,
    *,
    update_graph: Callable[[Path], None] | None = None,
) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    if update_graph is not None:
        update_graph(destination)


def write_bytes(path: Path | str, content: bytes) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)


def read_json(path: Path | str) -> Any:
    source = Path(path)
    return json.loads(source.read_text(encoding="utf-8"))


def write_json(path: Path | str, payload: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def delete_file(path: Path | str, *, linked_graph_path: Path | str | None = None) -> None:
    source = Path(path)
    source.unlink(missing_ok=True)
    if linked_graph_path is not None:
        Path(linked_graph_path).unlink(missing_ok=True)


def save_graph(graph: CharacterGraph, path: Path | str) -> None:
    persisted_graph = graph_for_persistence(graph)
    warnings = validate_graph(persisted_graph)
    if warnings:
        details = "\n".join(f"- {warning}" for warning in warnings)
        raise ValueError(f"Cannot save invalid character graph:\n{details}")
    write_json(path, persisted_graph.to_dict())


def load_graph(path: Path | str) -> CharacterGraph | None:
    source = Path(path)
    if not source.exists():
        return None
    try:
        payload = read_json(source)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{source} must contain valid graph JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{source} must contain a JSON object.")
    try:
        return CharacterGraph.from_dict(payload)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{source} does not contain a valid character graph.") from exc


def graph_for_persistence(graph: CharacterGraph) -> CharacterGraph:
    return CharacterGraph(
        schema_version=graph.schema_version,
        primary_character=graph.primary_character,
        characters=graph.characters,
        attributes=graph.attributes,
        places=graph.places,
        relationships=[
            relationship
            for relationship in graph.relationships
            if not is_synthetic_edge(relationship)
        ],
        embeddings=graph.embeddings,
        metadata=graph.metadata,
    )


def is_synthetic_edge(edge: RelationshipEdge) -> bool:
    edge_type = edge.relationship_type.strip().lower()
    edge_label = edge.relationship_label.strip().lower()
    return edge_type in SYNTHETIC_EDGE_TYPES or edge_label in SYNTHETIC_EDGE_TYPES
