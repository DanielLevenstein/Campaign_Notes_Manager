from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from src.graph.schema import SCHEMA_VERSION
from src.persistence.storage import read_markdown


@dataclass(frozen=True)
class BackstoryDocument:
    character_id: str
    source_file: str
    raw_text: str
    source_hash: str
    schema_version: str = SCHEMA_VERSION


def load_backstory(source_file: Path | str, character_id: str | None = None) -> BackstoryDocument:
    path = Path(source_file)
    raw_text = read_markdown(path)
    return BackstoryDocument(
        character_id=character_id or path.stem,
        source_file=str(path),
        raw_text=raw_text,
        source_hash=hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
    )
