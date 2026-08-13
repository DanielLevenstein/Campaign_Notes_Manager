from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from src.graph.combined_graph import (
    CombinedCharacterGraph,
    CombinedCharacterNode,
    build_combined_character_graph,
    combined_attribute_rows,
    compact,
    graph_view_root_nodes,
)
from src.graph.schema import CharacterGraph
from src.persistence.session_entities import derived_lore_entity_relationships
from src.persistence.lore_documents import (
    Character,
    Place,
    load_or_regenerate_lore_graph,
    read_character_profile,
    read_place_markdown,
    read_text,
)
from src.app_paths import CHARACTERS_DIR, LORE_DIR, PLACES_DIR, SESSION_NOTES_DIR


DISABLE_LORE_BACKUPS = "LOCAL_CHATBOT_DISABLE_LORE_BACKUPS"


@dataclass(frozen=True)
class CombinedGraphProjection:
    graphs: list[CharacterGraph]
    place_sources: list[tuple[str, str, str, str]]
    combined: CombinedCharacterGraph
    character_sheet_combined: CombinedCharacterGraph
    character_sheet_detail_rows: list[dict[str, str]]
    character_nodes: list[CombinedCharacterNode]
    main_character_ids: set[str]
    main_place_ids: set[str]

    @property
    def has_lore(self) -> bool:
        return bool(self.graphs or self.place_sources)


def build_combined_graph_projection(
    *,
    characters: list[Character],
    places: list[Place],
    graphs: list[CharacterGraph] | None = None,
    lore_paths: list[Path] | None = None,
) -> CombinedGraphProjection:
    graphs = graphs if graphs is not None else load_lore_graphs(lore_paths=lore_paths)
    place_sources = place_source_rows(places)
    character_display_names = [display_character_name(character) for character in characters]
    place_display_names = [display_place_name(place) for place in places]
    relationships = [
        *place_lore_relationships(places),
        *derived_lore_relationships(
            characters=characters,
            places=places,
            graphs=graphs,
            lore_paths=lore_paths,
        ),
    ]
    combined = build_combined_character_graph(graphs, place_sources, relationships)
    character_nodes = graph_view_root_nodes(combined, character_display_names, place_display_names)
    character_sheet_graphs = character_sheet_lore_graphs(graphs)
    return CombinedGraphProjection(
        graphs=graphs,
        place_sources=place_sources,
        combined=combined,
        character_sheet_combined=build_combined_character_graph(character_sheet_graphs),
        character_sheet_detail_rows=combined_attribute_rows(character_sheet_graphs),
        character_nodes=character_nodes,
        main_character_ids={node.id for node in character_nodes if node.node_type == "character"},
        main_place_ids={node.id for node in character_nodes if node.node_type == "place" and not node.is_source},
    )


def load_lore_graphs(*, lore_paths: list[Path] | None = None) -> list[CharacterGraph]:
    graphs = []
    for path in lore_paths if lore_paths is not None else lore_markdown_files():
        try:
            graph = load_or_regenerate_lore_graph(path)
        except (OSError, ValueError):
            continue
        if graph is not None:
            graphs.append(graph)
    return graphs


def character_sheet_lore_graphs(graphs: list[CharacterGraph]) -> list[CharacterGraph]:
    return [
        graph
        for graph in graphs
        if is_character_lore_path(Path(graph.primary_character.source_file))
    ]


def place_source_rows(places: list[Place]) -> list[tuple[str, str, str, str]]:
    return [
        (lore_source_document_id(place.path), display_place_name(place), str(place.path), "place")
        for place in places
    ]


def derived_lore_relationships(
    *,
    characters: list[Character],
    places: list[Place],
    graphs: list[CharacterGraph],
    lore_paths: list[Path] | None = None,
) -> list[dict[str, str]]:
    graph_sources = {
        Path(graph.primary_character.source_file).resolve(): graph
        for graph in graphs
    }
    known_character_names = [display_character_name(character) for character in characters]
    known_place_names = known_knowledge_graph_place_names(places)
    relationships: list[dict[str, str]] = []
    for path in lore_paths if lore_paths is not None else lore_markdown_files():
        if is_character_lore_path(path):
            continue
        graph = graph_sources.get(path.resolve())
        source_id = graph.primary_character.id if graph and not path_is_place_lore(path) else lore_source_document_id(path)
        source_name = combined_lore_source_name(path, graph)
        source_type = source_node_type_for_path(path)
        try:
            text = read_text(path)
        except OSError:
            continue
        relationships.extend(
            derived_lore_entity_relationships(
                source_id=source_id,
                source_name=source_name,
                source_type=source_type,
                source_file=str(path),
                text=text,
                known_character_names=known_character_names,
                known_place_names=known_place_names,
            )
        )
    return relationships


def combined_lore_source_name(path: Path, graph: CharacterGraph | None) -> str:
    if graph is not None and path_is_session_note(path):
        return session_note_source_name(path)
    if graph is not None:
        return graph.primary_character.name
    return path.stem.replace("_", " ")


def known_knowledge_graph_place_names(places: list[Place]) -> list[str]:
    names: list[str] = []
    for place in places:
        for name in place_name_aliases(place):
            if name and name not in names:
                names.append(name)
    return names


def place_name_aliases(place: Place) -> list[str]:
    display_name = display_place_name(place)
    aliases = [display_name, place.path.stem.replace("_", " ")]
    title = markdown_document_title(read_place_markdown(place))
    if title:
        aliases.append(title)
    for name in list(aliases):
        stripped = source_title_without_lore_suffix(name)
        if stripped and stripped not in aliases:
            aliases.append(stripped)
    return aliases


def source_title_without_lore_suffix(name: str) -> str:
    return re.sub(r"\s+Lore$", "", name.strip(), flags=re.IGNORECASE)


def lore_source_document_id(path: Path) -> str:
    return f"source_document__{compact(path.stem)}"


def source_node_type_for_path(path: Path) -> str:
    normalized = str(path).replace("\\", "/").lower()
    if "/places/" in normalized:
        return "place"
    if "/session_notes/" in normalized:
        return "note"
    if "/character_sheets/" in normalized:
        return "character"
    return "note"


def is_character_lore_path(path: Path) -> bool:
    return "character_sheets" in path.parts


def path_is_place_lore(path: Path) -> bool:
    return "places" in path.parts


def path_is_session_note(path: Path) -> bool:
    normalized = str(path).replace("\\", "/").lower()
    try:
        path.resolve().relative_to(SESSION_NOTES_DIR.resolve())
        return True
    except ValueError:
        return "/session_notes/" in normalized or compact(path.stem) in {"sessionnote", "sessionnotes"}


def session_note_source_name(path: Path) -> str:
    name = path.stem.replace("_", " ")
    return name if name else "Session Notes"


def lore_markdown_files() -> list[Path]:
    paths: dict[Path, Path] = {}
    for directory in unique_lore_scan_dirs():
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*.md")):
            if (
                "TEMPLATE" not in path.name.upper()
                and not path.name.startswith(".")
                and not should_skip_lore_scan_path(path)
            ):
                paths[path.resolve()] = path
    return [paths[key] for key in sorted(paths, key=lambda item: str(item))]


def unique_lore_scan_dirs() -> list[Path]:
    directories: list[Path] = []
    for directory in [LORE_DIR, CHARACTERS_DIR, PLACES_DIR, SESSION_NOTES_DIR]:
        if directory not in directories:
            directories.append(directory)
    return directories


def should_skip_lore_scan_path(path: Path) -> bool:
    if not lore_backups_disabled():
        return False
    return any(part.lower() == "backup" for part in path.parts)


def lore_backups_disabled() -> bool:
    return os.environ.get(DISABLE_LORE_BACKUPS, "").strip().lower() in {"1", "true", "yes", "on"}


def place_lore_relationships(places: list[Place]) -> list[dict[str, str]]:
    relationships: list[dict[str, str]] = []
    known_place_keys = {compact(place.name) for place in places}
    for place in places:
        text = read_text(place.path)
        source_id = lore_source_document_id(place.path)
        for line in place_connections_lines(text):
            if ":" in line:
                name, relationship = line.split(":", 1)
            else:
                name, relationship = line, "reference"
            target_name = name.strip().lstrip("-").strip()
            if not target_name:
                continue
            target_type = "place" if compact(target_name) in known_place_keys or looks_like_place_connection(target_name) else "character"
            relationships.append(
                {
                    "source_id": source_id,
                    "source_name": place.name,
                    "source_type": "source_document",
                    "source_file": str(place.path),
                    "target_id": compact(target_name),
                    "target_name": target_name,
                    "target_type": target_type,
                    "relationship": relationship.strip() or "reference",
                    "evidence": line.strip(),
                }
            )
    return relationships


def place_connections_lines(text: str) -> list[str]:
    sections = text.splitlines()
    lines: list[str] = []
    in_connections = False
    for line in sections:
        stripped = line.strip()
        if stripped.lower().startswith("## "):
            in_connections = stripped.lower() == "## place connections"
            continue
        if in_connections and stripped.startswith("-"):
            lines.append(stripped.lstrip("-").strip())
    return lines


def looks_like_place_connection(name: str) -> bool:
    lowered = name.strip().lower()
    place_suffixes = {
        "academy",
        "bastion",
        "cavern",
        "city",
        "college",
        "coast",
        "court",
        "fortress",
        "forest",
        "guild",
        "hall",
        "harbor",
        "keep",
        "kingdom",
        "library",
        "mage college",
        "monastery",
        "school",
        "sea",
        "shore",
        "temple",
        "tower",
        "tavern",
        "university",
        "village",
    }
    return any(lowered == suffix or lowered.endswith(f" {suffix}") for suffix in place_suffixes)


def display_character_name(character: Character) -> str:
    profile = read_character_profile(character)
    return clean_display_name(profile.name or character.name)


def display_place_name(place: Place) -> str:
    return clean_display_name(markdown_document_title(read_place_markdown(place)) or place.name)


def markdown_document_title(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped.lstrip("#").strip()
    return ""


def clean_display_name(name: str) -> str:
    cleaned = name.replace("_", " ")
    cleaned = cleaned.replace("(Auto Generated)", "")
    cleaned = cleaned.replace("(Generated)", "")
    cleaned = cleaned.replace("(Autogenerated)", "")
    cleaned = cleaned.replace("Auto Generated", "")
    cleaned = cleaned.replace("Generated", "")
    cleaned = cleaned.replace("Autogenerated", "")
    cleaned = " ".join(cleaned.split())
    return cleaned.rstrip(" -:|")
