from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import CanonicalEdge, CanonicalGraph, CanonicalNode
from .source_paths import source_file_key
from src.persistence.sqlite_store import connect_database


class CanonicalGraphService:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self._initialize()

    def upsert_node(self, node: CanonicalNode) -> str:
        existing = self._fetch_one("SELECT version, created_at FROM nodes WHERE id = ?", (node.id,))
        now = timestamp()
        version = int(existing["version"]) + 1 if existing else 1
        created_at = existing["created_at"] if existing else now
        stored = replace(node, version=version, created_at=created_at, updated_at=now)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO nodes (
                    id, canonical_type, display_name, source_file, source_file_key, source_id,
                    properties_json, canonical_tags_json, provenance_json, version, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    canonical_type = excluded.canonical_type,
                    display_name = excluded.display_name,
                    source_file = excluded.source_file,
                    source_file_key = excluded.source_file_key,
                    source_id = excluded.source_id,
                    properties_json = excluded.properties_json,
                    canonical_tags_json = excluded.canonical_tags_json,
                    provenance_json = excluded.provenance_json,
                    version = excluded.version,
                    updated_at = excluded.updated_at
                """,
                (
                    stored.id,
                    stored.canonical_type,
                    stored.display_name,
                    stored.source_file,
                    source_file_key(stored.source_file) if stored.source_file else "",
                    stored.source_id,
                    dumps(stored.properties),
                    dumps(list(stored.canonical_tags)),
                    dumps(stored.provenance),
                    stored.version,
                    stored.created_at,
                    stored.updated_at,
                ),
            )
            self._bump_store_version(connection)
        return stored.id

    def upsert_edge(self, edge: CanonicalEdge) -> str:
        existing = self._fetch_one("SELECT version, created_at FROM edges WHERE id = ?", (edge.id,))
        now = timestamp()
        version = int(existing["version"]) + 1 if existing else 1
        created_at = existing["created_at"] if existing else now
        stored = replace(edge, version=version, created_at=created_at, updated_at=now)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO edges (
                    id, source_id, target_id, relation_type, relation_label, evidence_json,
                    properties_json, provenance_json, version, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    source_id = excluded.source_id,
                    target_id = excluded.target_id,
                    relation_type = excluded.relation_type,
                    relation_label = excluded.relation_label,
                    evidence_json = excluded.evidence_json,
                    properties_json = excluded.properties_json,
                    provenance_json = excluded.provenance_json,
                    version = excluded.version,
                    updated_at = excluded.updated_at
                """,
                (
                    stored.id,
                    stored.source_id,
                    stored.target_id,
                    stored.relation_type,
                    stored.relation_label,
                    dumps(list(stored.evidence)),
                    dumps(stored.properties),
                    dumps(stored.provenance),
                    stored.version,
                    stored.created_at,
                    stored.updated_at,
                ),
            )
            self._bump_store_version(connection)
        return stored.id

    def upsert_graph(self, graph: CanonicalGraph) -> None:
        for node in graph.nodes.values():
            self.upsert_node(node)
        for edge in graph.edges.values():
            self.upsert_edge(edge)

    def replace_source_graph(self, source_file: str | Path, graph: CanonicalGraph) -> None:
        source_key = source_file_key(source_file)
        with self._connect() as connection:
            source_node_rows = connection.execute(
                "SELECT id FROM nodes WHERE source_file_key = ?",
                (source_key,),
            ).fetchall()
            source_node_ids = [row["id"] for row in source_node_rows]
            if source_node_ids:
                placeholders = ",".join("?" for _ in source_node_ids)
                connection.execute(
                    f"DELETE FROM edges WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})",
                    (*source_node_ids, *source_node_ids),
                )
                connection.execute(f"DELETE FROM nodes WHERE id IN ({placeholders})", source_node_ids)
            for node in graph.nodes.values():
                self._upsert_node(connection, node)
            for edge in graph.edges.values():
                self._upsert_edge(connection, edge)
            self._bump_store_version(connection)

    def get_nodes(self, filters: dict[str, object] | None = None) -> list[CanonicalNode]:
        clauses, values = self._node_filter(filters or {})
        query = "SELECT * FROM nodes"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY display_name, id"
        with self._connect() as connection:
            return [node_from_row(row) for row in connection.execute(query, values)]

    def get_edges(self, filters: dict[str, object] | None = None) -> list[CanonicalEdge]:
        clauses, values = self._edge_filter(filters or {})
        query = "SELECT * FROM edges"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY source_id, target_id, relation_type, id"
        with self._connect() as connection:
            return [edge_from_row(row) for row in connection.execute(query, values)]

    def get_nodes_by_source_file(self, path: str | Path) -> list[CanonicalNode]:
        return self.get_nodes({"source_file": path})

    def version(self) -> int:
        row = self._fetch_one("SELECT value FROM metadata WHERE key = 'version'", ())
        return int(row["value"]) if row else 0

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    canonical_type TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    source_file_key TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    properties_json TEXT NOT NULL,
                    canonical_tags_json TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_nodes_source_file_key ON nodes(source_file_key);
                CREATE INDEX IF NOT EXISTS idx_nodes_canonical_type ON nodes(canonical_type);
                CREATE TABLE IF NOT EXISTS edges (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    relation_label TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    properties_json TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_edges_source_id ON edges(source_id);
                CREATE INDEX IF NOT EXISTS idx_edges_target_id ON edges(target_id);
                """
            )
            connection.execute("INSERT OR IGNORE INTO metadata(key, value) VALUES ('version', '0')")

    def _connect(self) -> sqlite3.Connection:
        return connect_database(self.database_path)

    def _fetch_one(self, query: str, values: tuple[object, ...]) -> sqlite3.Row | None:
        with self._connect() as connection:
            return connection.execute(query, values).fetchone()

    def _upsert_node(self, connection: sqlite3.Connection, node: CanonicalNode) -> None:
        now = timestamp()
        stored = replace(node, version=1, created_at=now, updated_at=now)
        connection.execute(
            """
            INSERT INTO nodes (
                id, canonical_type, display_name, source_file, source_file_key, source_id,
                properties_json, canonical_tags_json, provenance_json, version, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                canonical_type = excluded.canonical_type,
                display_name = excluded.display_name,
                source_file = excluded.source_file,
                source_file_key = excluded.source_file_key,
                source_id = excluded.source_id,
                properties_json = excluded.properties_json,
                canonical_tags_json = excluded.canonical_tags_json,
                provenance_json = excluded.provenance_json,
                version = nodes.version + 1,
                updated_at = excluded.updated_at
            """,
            (
                stored.id,
                stored.canonical_type,
                stored.display_name,
                stored.source_file,
                source_file_key(stored.source_file) if stored.source_file else "",
                stored.source_id,
                dumps(stored.properties),
                dumps(list(stored.canonical_tags)),
                dumps(stored.provenance),
                stored.version,
                stored.created_at,
                stored.updated_at,
            ),
        )

    def _upsert_edge(self, connection: sqlite3.Connection, edge: CanonicalEdge) -> None:
        now = timestamp()
        stored = replace(edge, version=1, created_at=now, updated_at=now)
        connection.execute(
            """
            INSERT INTO edges (
                id, source_id, target_id, relation_type, relation_label, evidence_json,
                properties_json, provenance_json, version, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                source_id = excluded.source_id,
                target_id = excluded.target_id,
                relation_type = excluded.relation_type,
                relation_label = excluded.relation_label,
                evidence_json = excluded.evidence_json,
                properties_json = excluded.properties_json,
                provenance_json = excluded.provenance_json,
                version = edges.version + 1,
                updated_at = excluded.updated_at
            """,
            (
                stored.id,
                stored.source_id,
                stored.target_id,
                stored.relation_type,
                stored.relation_label,
                dumps(list(stored.evidence)),
                dumps(stored.properties),
                dumps(stored.provenance),
                stored.version,
                stored.created_at,
                stored.updated_at,
            ),
        )

    def _bump_store_version(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            "UPDATE metadata SET value = CAST(CAST(value AS INTEGER) + 1 AS TEXT) WHERE key = 'version'"
        )

    def _node_filter(self, filters: dict[str, object]) -> tuple[list[str], list[object]]:
        clauses: list[str] = []
        values: list[object] = []
        if "id" in filters:
            clauses.append("id = ?")
            values.append(filters["id"])
        if "canonical_type" in filters:
            clauses.append("canonical_type = ?")
            values.append(filters["canonical_type"])
        if "source_file" in filters:
            clauses.append("source_file_key = ?")
            values.append(source_file_key(str(filters["source_file"])))
        if "source_id" in filters:
            clauses.append("source_id = ?")
            values.append(filters["source_id"])
        return clauses, values

    def _edge_filter(self, filters: dict[str, object]) -> tuple[list[str], list[object]]:
        clauses: list[str] = []
        values: list[object] = []
        for key in ("id", "source_id", "target_id", "relation_type"):
            if key in filters:
                clauses.append(f"{key} = ?")
                values.append(filters[key])
        return clauses, values


def node_from_row(row: sqlite3.Row) -> CanonicalNode:
    return CanonicalNode(
        id=row["id"],
        canonical_type=row["canonical_type"],
        display_name=row["display_name"],
        source_file=row["source_file"],
        source_id=row["source_id"],
        properties=loads(row["properties_json"]),
        canonical_tags=tuple(loads(row["canonical_tags_json"])),
        provenance=loads(row["provenance_json"]),
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def edge_from_row(row: sqlite3.Row) -> CanonicalEdge:
    return CanonicalEdge(
        id=row["id"],
        source_id=row["source_id"],
        target_id=row["target_id"],
        relation_type=row["relation_type"],
        relation_label=row["relation_label"],
        evidence=tuple(loads(row["evidence_json"])),
        properties=loads(row["properties_json"]),
        provenance=loads(row["provenance_json"]),
        version=row["version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def loads(value: str) -> Any:
    return json.loads(value)
