# Session Note Upload E2E Can Lose The Staged File

## Status
Resolved

## Summary
Session note upload e2e tests intermittently reach the app-level validation error `Choose A Markdown Or Text File Before Uploading.` even after Playwright has attached a file to the Streamlit file uploader. The failure appears most often when running the whole session-notes e2e module and is not consistently reproducible when the same tests run in isolation.

## Evidence
- The file uploader alternates between two Streamlit states:
  - a staged `upload Upload` button with no visible filename
  - an attached filename with `Remove <file>` and no staged upload button
- In failing full-module runs, the test can click `Upload Session Note` while the app reports no file is available, despite prior `set_input_files(...)`.
- Several bounded retries and reload recovery paths reduce but do not eliminate the issue.

## Suspected Cause
The tests often upload files created inside the app's configured lore tree. Streamlit may rerun while the watched directory changes, causing the file uploader widget state to reset between Playwright attaching the file and the app-level upload click.

## Suggested Follow-Up
Move upload-source fixtures outside watched lore/session-note directories for these e2e tests, or add a dedicated test fixture path for upload sources under an unwatched temporary directory.

## Fix Summary
Session-note e2e fixtures now provide a dedicated `upload_sources` directory outside the app's watched lore/session-note tree. Upload tests that create mutable source files write there before attaching them to the Streamlit file uploader.

The recursive reload recovery path in `import_session_note_file` was removed after the upload source path was moved out of watched directories.

## Test Evidence
- `tests/e2e/test_session_notes_ui.py::test_ui_imports_uploaded_session_notes_as_one_markdown_file`
- `tests/e2e/test_session_notes_ui.py::test_ui_import_dialog_keeps_month_year_dates_and_hides_h4_headings`
