from pathlib import Path

import paths as paths
from paths import ROOT_DIR, TEST_FIXTURES_DIRECTORY


def test_default_test_lore_import_directory_points_to_project_fixtures():
    project_root = Path(__file__).resolve().parents[3]

    assert ROOT_DIR == project_root
    assert TEST_FIXTURES_DIRECTORY == project_root / "tests" / "fixtures"
    assert (TEST_FIXTURES_DIRECTORY / "character_sheets" / "Jory_Ravenmark.md").exists()
    assert ROOT_DIR.name == "Campaign_Notes_Manager"
    assert ROOT_DIR.name not in {"src", "persistence"}


def test_refresh_paths_recomputes_derived_paths_from_environment(tmp_path, monkeypatch):
    world_building = tmp_path / "campaign_state"
    monkeypatch.setenv("LOCAL_CHATBOT_WORLD_BUILDING_DIR", str(world_building))
    monkeypatch.delenv("LOCAL_CHATBOT_LORE_DIR", raising=False)
    monkeypatch.delenv("LOCAL_CHATBOT_DOCS_LORE_DIR", raising=False)
    monkeypatch.delenv("LOCAL_CHATBOT_META_DATA_DIR", raising=False)
    monkeypatch.delenv("LOCAL_CHATBOT_DATA_DIR", raising=False)
    monkeypatch.delenv("LOCAL_CHATBOT_CHARACTERS_DIR", raising=False)
    monkeypatch.delenv("LOCAL_CHATBOT_PLACES_DIR", raising=False)
    monkeypatch.delenv("LOCAL_CHATBOT_SESSION_NOTES_DIR", raising=False)

    settings = paths.refresh_paths()

    assert settings.world_building_dir == world_building
    assert paths.LORE_DIR == world_building / "lore"
    assert paths.META_DATA_DIR == world_building / "meta_data"
    assert paths.CHARACTERS_DIR == world_building / "lore" / "character_sheets"
    assert paths.WORLD_BUILDING_IMPORT_DIR == world_building / "import"
    assert paths.WORLD_BUILDING_BACKUP_DIR == world_building / "backup"

    monkeypatch.delenv("LOCAL_CHATBOT_WORLD_BUILDING_DIR", raising=False)
    paths.refresh_paths()
