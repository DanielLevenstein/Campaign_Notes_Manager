from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_VIEW_CONFIG_DIR = PROJECT_ROOT / "config" / "knowledge_views"
DEFAULT_VIEW_ORDER = (
    "character_view",
    "party_view",
    "location_view",
    "session_view",
)


@dataclass(frozen=True)
class KnowledgeViewDefinition:
    view_key: str
    view_name: str
    source_fixtures: tuple[str, ...]
    hidden_elements: tuple[str, ...]
    unhidden_elements: tuple[str, ...]
    graphviz_view: str
    columns: tuple[tuple[str, ...], ...] = ()
    projection: str = ""
    source_predicate: str = ""
    column_layout: str = ""
    source_key: str = ""
    heading_key: str = ""
    include_all_heading_option: bool = False
    source_empty_message: str = ""
    heading_empty_message: str = ""
    graph_empty_message: str = ""
    migration_status: str = ""


def load_knowledge_view_definition(
    view_key: str,
    config_dir: Path = KNOWLEDGE_VIEW_CONFIG_DIR,
) -> KnowledgeViewDefinition:
    path = config_dir / f"{view_key}.json"
    if not path.exists():
        raise ValueError(f"Knowledge view config `{view_key}` does not exist at {path}.")
    payload = read_knowledge_view_config(path)
    return knowledge_view_definition_from_payload(payload, view_key=view_key)


def load_knowledge_view_definitions(
    config_dir: Path = KNOWLEDGE_VIEW_CONFIG_DIR,
    view_order: tuple[str, ...] = DEFAULT_VIEW_ORDER,
) -> list[KnowledgeViewDefinition]:
    return [
        load_knowledge_view_definition(view_key, config_dir)
        for view_key in view_order
    ]


def knowledge_view_definition_from_payload(
    payload: dict[str, Any],
    *,
    view_key: str,
) -> KnowledgeViewDefinition:
    schema_version = non_empty_string(payload.get("schema_version"), "schema_version")
    if schema_version != "0.1.0":
        raise ValueError(f"Unsupported knowledge view schema_version `{schema_version}`.")
    return KnowledgeViewDefinition(
        view_key=view_key,
        view_name=non_empty_string(payload.get("view_name"), "view_name"),
        source_fixtures=string_tuple(payload.get("source_fixtures"), "source_fixtures", allow_empty=True),
        hidden_elements=string_tuple(payload.get("hidden_elements"), "hidden_elements", allow_empty=True),
        unhidden_elements=string_tuple(payload.get("unhidden_elements"), "unhidden_elements", allow_empty=True),
        graphviz_view=non_empty_string(payload.get("graphviz_view"), "graphviz_view"),
        columns=column_tuple(payload.get("columns", []), "columns"),
        projection=optional_string(payload.get("projection", ""), "projection"),
        source_predicate=optional_string(payload.get("source_predicate", ""), "source_predicate"),
        column_layout=optional_string(payload.get("column_layout", ""), "column_layout"),
        source_key=optional_string(payload.get("source_key", ""), "source_key"),
        heading_key=optional_string(payload.get("heading_key", ""), "heading_key"),
        include_all_heading_option=bool_value(
            payload.get("include_all_heading_option", False),
            "include_all_heading_option",
        ),
        source_empty_message=optional_string(payload.get("source_empty_message", ""), "source_empty_message"),
        heading_empty_message=optional_string(payload.get("heading_empty_message", ""), "heading_empty_message"),
        graph_empty_message=optional_string(payload.get("graph_empty_message", ""), "graph_empty_message"),
        migration_status=str(payload.get("migration_status", "")).strip(),
    )


def read_knowledge_view_config(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid knowledge view config JSON at {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Knowledge view config at {path} must contain a JSON object.")
    return payload


def non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Knowledge view `{field_name}` must be a non-empty string.")
    return value.strip()


def optional_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"Knowledge view `{field_name}` must be a string.")
    return value.strip()


def bool_value(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"Knowledge view `{field_name}` must be a boolean.")
    return value


def string_tuple(value: Any, field_name: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"Knowledge view `{field_name}` must be a list.")
    values = tuple(str(item).strip() for item in value if str(item).strip())
    if not values and not allow_empty:
        raise ValueError(f"Knowledge view `{field_name}` must contain non-empty strings.")
    return values


def column_tuple(value: Any, field_name: str) -> tuple[tuple[str, ...], ...]:
    if not isinstance(value, list):
        raise ValueError(f"Knowledge view `{field_name}` must be a list.")
    columns: list[tuple[str, ...]] = []
    for index, column in enumerate(value):
        if not isinstance(column, list):
            raise ValueError(f"Knowledge view `{field_name}` item {index} must be a list.")
        column_values = tuple(str(item).strip() for item in column if str(item).strip())
        if not column_values:
            raise ValueError(f"Knowledge view `{field_name}` item {index} must contain non-empty strings.")
        columns.append(column_values)
    return tuple(columns)
