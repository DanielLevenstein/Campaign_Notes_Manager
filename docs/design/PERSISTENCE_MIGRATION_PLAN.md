# Persistence Migration Plan

The v2 source root should have one real persistence implementation:

```text
src/persistence/storage.py
```

Legacy modules should delegate to `src.persistence.storage` instead of duplicating file IO logic.

## Current Roles

- `src/persistence/storage.py`: canonical low-level persistence implementation for Markdown, text, JSON, bytes, graph file paths, graph serialization, graph loading, and deletes.
- `src/persistence/sqlite_store.py`: canonical low-level SQLite connection helper for embedded graph database access.
- `language_model/lore_documents.py`: legacy domain/application service module. It still owns character/place/profile parsing and save workflows, but low-level file IO and graph persistence should call `src.persistence.storage`.

## Migration Path

1. Keep `src.persistence.storage` as the only implementation of file and graph persistence helpers.
2. Import graph persistence helpers from `src.persistence.storage` directly.
3. Split `language_model.lore_documents` by responsibility:
   - character/place dataclasses and profile operations move to `src/writing`
   - Markdown parsing/transformation moves to `src/transformation`
   - graph regeneration orchestration moves to `src/graph`
   - raw file operations remain in `src/persistence`
4. Move tests with each migrated responsibility:
   - pure persistence tests stay under `tests/unit/persistence`
   - legacy adapter tests remain until the adapter is removed
   - cross-module save/regenerate workflows move to `tests/integration`
5. Delete legacy domain adapters only after all imports have moved to the new package boundary.

## Guardrails

- Do not add new direct `Path.write_text`, `Path.write_bytes`, or `Path.unlink` calls in migrated code.
- UI write and undo flows must go through domain services or `src.persistence` helpers.
- Graph views should read persisted graph metadata files and only regenerate through persistence/domain services when metadata is missing.
- Embedded graph database access should go through `src.persistence.sqlite_store`.
- Do not persist synthetic graph edges.
- Keep graph metadata paths mirrored under `world_building/meta_data`.
- Preserve existing UI behavior while moving responsibilities out of `language_model.lore_documents`.
