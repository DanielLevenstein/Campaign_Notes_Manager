from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.persistence.storage import read_json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GRAPHVIZ_CONFIG_DIR = PROJECT_ROOT / "config" / "graphviz"


def load_graphviz_config(view_key: str, config_dir: Path = GRAPHVIZ_CONFIG_DIR) -> dict[str, Any]:
    global_config = read_graphviz_config(config_dir / "global_graph_view.json")
    view_config_path = config_dir / f"{view_key}.json"
    if not view_config_path.exists():
        return global_config
    view_config = read_graphviz_config(view_config_path)
    inherited_config = inherited_graphviz_config(view_config, config_dir, seen={view_config_path.resolve()})
    base_config = deep_merge(global_config, inherited_config) if inherited_config is not None else global_config
    return deep_merge(base_config, view_config)


def inherited_graphviz_config(
    view_config: dict[str, Any],
    config_dir: Path,
    *,
    seen: set[Path] | None = None,
) -> dict[str, Any] | None:
    inherited_path = view_config.get("inherits")
    if not isinstance(inherited_path, str) or not inherited_path:
        return None
    path = Path(inherited_path)
    candidates = [
        path if path.is_absolute() else config_dir / path.name,
        path if path.is_absolute() else PROJECT_ROOT / path,
    ]
    for candidate in candidates:
        if candidate.exists():
            resolved_candidate = candidate.resolve()
            if seen is not None and resolved_candidate in seen:
                raise ValueError(f"Graphviz config inheritance cycle includes {candidate}.")
            parent_config = read_graphviz_config(candidate)
            parent_seen = {*seen, resolved_candidate} if seen is not None else {resolved_candidate}
            inherited_parent = inherited_graphviz_config(parent_config, config_dir, seen=parent_seen)
            return deep_merge(inherited_parent, parent_config) if inherited_parent is not None else parent_config
    return None


def read_graphviz_config(path: Path) -> dict[str, Any]:
    try:
        payload = read_json(path)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid Graphviz config JSON at {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Graphviz config at {path} must contain a JSON object.")
    return payload


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if (
            isinstance(value, dict)
            and isinstance(merged.get(key), dict)
        ):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = deepcopy(value)
    return merged
