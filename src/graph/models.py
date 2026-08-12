from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CanonicalNode:
    id: str
    canonical_type: str
    display_name: str
    source_file: str = ""
    source_id: str = ""
    properties: dict[str, object] = field(default_factory=dict)
    canonical_tags: tuple[str, ...] = ()
    provenance: dict[str, object] = field(default_factory=dict)
    version: int = 1
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True)
class CanonicalEdge:
    id: str
    source_id: str
    target_id: str
    relation_type: str
    relation_label: str = ""
    evidence: tuple[str, ...] = ()
    properties: dict[str, object] = field(default_factory=dict)
    provenance: dict[str, object] = field(default_factory=dict)
    version: int = 1
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True)
class CanonicalGraph:
    nodes: dict[str, CanonicalNode] = field(default_factory=dict)
    edges: dict[str, CanonicalEdge] = field(default_factory=dict)
