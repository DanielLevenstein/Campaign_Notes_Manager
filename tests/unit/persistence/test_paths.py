from pathlib import Path

from src.persistence.paths import ROOT_DIR, TEST_FIXTURES_DIRECTORY


def test_default_test_lore_import_directory_points_to_project_fixtures():
    project_root = Path(__file__).resolve().parents[3]

    assert ROOT_DIR == project_root
    assert TEST_FIXTURES_DIRECTORY == project_root / "tests" / "fixtures"
    assert (TEST_FIXTURES_DIRECTORY / "character_sheets" / "Jory_Ravenmark.md").exists()
