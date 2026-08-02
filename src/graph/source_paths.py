from __future__ import annotations

from pathlib import Path


def normalize_source_file(path: str | Path, *, root: str | Path | None = None) -> str:
    source = Path(str(path).replace("\\", "/")).expanduser()
    if not source.is_absolute() and root is not None:
        source = Path(root).expanduser() / source
    normalized = source.resolve()
    if root is not None:
        root_path = Path(root).expanduser().resolve()
        try:
            normalized = normalized.relative_to(root_path)
        except ValueError:
            pass
    return normalized.as_posix()


def source_file_key(path: str | Path, *, root: str | Path | None = None) -> str:
    return normalize_source_file(path, root=root).casefold()
