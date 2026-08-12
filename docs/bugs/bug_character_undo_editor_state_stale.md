# Character Undo Leaves Editor Textbox Stale

## Status
Resolved

## Reproduction
1. Open the app with character lore available.
2. Create or open a character.
3. Edit the character summary and save.
4. Edit the summary again and save.
5. Click `Undo Changes`.

## Expected
The visible `Summary` textbox refreshes to the restored summary after the undo completes.

## Actual
The app displays `Character Changes Undone.`, but the visible `Summary` textbox can still show the pre-undo edited value.

## Test Evidence
`tests/e2e/test_character_sheet_roundtrip_ui.py::test_ui_creates_loads_and_undoes_character_changes` fails because the textbox value remains `Della is a reckless scout tonight.` after undo, instead of returning to `Della is a careful scout with brass lockpicks.`

## Notes
This was identified while enabling and repairing test-suite coverage. The character editor now refreshes revisioned widget keys after save and undo operations.
