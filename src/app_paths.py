from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parent


def find_project_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "streamlit_app.py").exists() and (candidate / "tests" / "fixtures").exists():
            return candidate
    return SOURCE_ROOT.parent


ROOT_DIR = find_project_root(SOURCE_ROOT)
CONFIG_DIR = ROOT_DIR / "config"
TEST_FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures"
WORLD_BUILDING_DIR = ROOT_DIR / "world_building"
WORLD_BUILDING_IMPORT_DIR = WORLD_BUILDING_DIR / "import"
WORLD_BUILDING_BACKUP_DIR = WORLD_BUILDING_DIR / "backup"
META_DATA_DIR = WORLD_BUILDING_DIR / "meta_data"
LORE_DIR = WORLD_BUILDING_DIR / "lore"
DOCS_LORE_DIR = LORE_DIR
CHARACTERS_DIR = LORE_DIR / "character_sheets"
PLACES_DIR = LORE_DIR / "places"
SESSION_NOTES_DIR = LORE_DIR / "session_notes"
GENERATED_LORE_DIR = LORE_DIR / "generated"
GENERATED_CHARACTER_SHEETS_DIR = GENERATED_LORE_DIR / "character_sheets"
CHARACTER_GRAPHS_DIR = META_DATA_DIR / "character_graph"
CHARACTER_METADATA_DIR = META_DATA_DIR / "character_metadata"


@dataclass(frozen=True)
class PathSettings:
    world_building_dir: Path
    world_building_import_dir: Path
    world_building_backup_dir: Path
    meta_data_dir: Path
    lore_dir: Path
    docs_lore_dir: Path
    characters_dir: Path
    places_dir: Path
    session_notes_dir: Path
    generated_lore_dir: Path
    generated_character_sheets_dir: Path
    character_graphs_dir: Path
    character_metadata_dir: Path


def env_path(name: str, default: Path | str) -> Path:
    value = os.environ.get(name)
    return Path(value if value else default).expanduser().resolve()


def first_env_path(names: tuple[str, ...], default: Path | str) -> Path:
    for name in names:
        value = os.environ.get(name)
        if value:
            return Path(value).expanduser().resolve()
    return Path(default).expanduser().resolve()


def load_path_settings() -> PathSettings:
    world_building_dir = env_path("LOCAL_CHATBOT_WORLD_BUILDING_DIR", ROOT_DIR / "world_building")
    lore_dir = first_env_path(
        ("LOCAL_CHATBOT_LORE_DIR", "LOCAL_CHATBOT_DOCS_LORE_DIR"),
        world_building_dir / "lore",
    )
    meta_data_dir = first_env_path(
        ("LOCAL_CHATBOT_META_DATA_DIR", "LOCAL_CHATBOT_DATA_DIR"),
        world_building_dir / "meta_data",
    )
    generated_lore_dir = env_path("LOCAL_CHATBOT_GENERATED_LORE_DIR", lore_dir)
    return PathSettings(
        world_building_dir=world_building_dir,
        world_building_import_dir=env_path("LOCAL_CHATBOT_WORLD_BUILDING_IMPORT_DIR", world_building_dir / "import"),
        world_building_backup_dir=env_path("LOCAL_CHATBOT_WORLD_BUILDING_BACKUP_DIR", world_building_dir / "backup"),
        meta_data_dir=meta_data_dir,
        lore_dir=lore_dir,
        docs_lore_dir=lore_dir,
        characters_dir=env_path("LOCAL_CHATBOT_CHARACTERS_DIR", lore_dir / "character_sheets"),
        places_dir=env_path("LOCAL_CHATBOT_PLACES_DIR", lore_dir / "places"),
        session_notes_dir=env_path("LOCAL_CHATBOT_SESSION_NOTES_DIR", lore_dir / "session_notes"),
        generated_lore_dir=generated_lore_dir,
        generated_character_sheets_dir=env_path(
            "LOCAL_CHATBOT_GENERATED_CHARACTER_SHEETS_DIR",
            generated_lore_dir / "character_sheets",
        ),
        character_graphs_dir=env_path("LOCAL_CHATBOT_CHARACTER_GRAPHS_DIR", meta_data_dir / "character_graph"),
        character_metadata_dir=env_path("LOCAL_CHATBOT_CHARACTER_METADATA_DIR", meta_data_dir / "character_metadata"),
    )


def refresh_paths() -> PathSettings:
    settings = load_path_settings()
    globals().update(
        {
            "WORLD_BUILDING_DIR": settings.world_building_dir,
            "WORLD_BUILDING_IMPORT_DIR": settings.world_building_import_dir,
            "WORLD_BUILDING_BACKUP_DIR": settings.world_building_backup_dir,
            "META_DATA_DIR": settings.meta_data_dir,
            "LORE_DIR": settings.lore_dir,
            "DOCS_LORE_DIR": settings.docs_lore_dir,
            "CHARACTERS_DIR": settings.characters_dir,
            "PLACES_DIR": settings.places_dir,
            "SESSION_NOTES_DIR": settings.session_notes_dir,
            "GENERATED_LORE_DIR": settings.generated_lore_dir,
            "GENERATED_CHARACTER_SHEETS_DIR": settings.generated_character_sheets_dir,
            "CHARACTER_GRAPHS_DIR": settings.character_graphs_dir,
            "CHARACTER_METADATA_DIR": settings.character_metadata_dir,
        }
    )
    return settings


refresh_paths()


def ensure_base_dirs() -> None:
    WORLD_BUILDING_DIR.mkdir(parents=True, exist_ok=True)
    WORLD_BUILDING_IMPORT_DIR.mkdir(parents=True, exist_ok=True)
    WORLD_BUILDING_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    META_DATA_DIR.mkdir(parents=True, exist_ok=True)
    LORE_DIR.mkdir(parents=True, exist_ok=True)
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    PLACES_DIR.mkdir(parents=True, exist_ok=True)
    SESSION_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_LORE_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_CHARACTER_SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    CHARACTER_METADATA_DIR.mkdir(parents=True, exist_ok=True)
    CHARACTER_GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
