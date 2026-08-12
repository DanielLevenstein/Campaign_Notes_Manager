from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"
CHARACTER_SHEETS_FIXTURE_DIR = TEST_FIXTURES_DIR / "character_sheets"
PLACES_FIXTURE_DIR = TEST_FIXTURES_DIR / "places"
SESSION_NOTES_FIXTURE_DIR = TEST_FIXTURES_DIR / "session_notes"
LEGACY_SESSION_NOTES_FIXTURE_DIR = TEST_FIXTURES_DIR / "legacy_session_notes"
LEGACY_SESSION_NOTES_TXT = LEGACY_SESSION_NOTES_FIXTURE_DIR / "Session_Notes.txt"

LORE_IMPORT_CHARACTER_FILES = tuple(sorted(CHARACTER_SHEETS_FIXTURE_DIR.glob("*.md")))
LORE_IMPORT_PLACE_FILES = tuple(sorted(PLACES_FIXTURE_DIR.glob("*.md")))
LORE_IMPORT_SESSION_NOTE_FILES = tuple(
    sorted(
        path
        for pattern in ("*.md", "*.txt")
        for path in SESSION_NOTES_FIXTURE_DIR.glob(pattern)
    )
)
LORE_IMPORT_METADATA_FILES = tuple(
    sorted(path for path in (TEST_FIXTURES_DIR / "meta_data").glob("*") if path.is_file())
)
