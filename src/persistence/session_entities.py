from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from src.extraction.config import CharacterExtractionConfig, load_character_extraction_config


SESSION_ENTITY_CONFIG = load_character_extraction_config()
ENTITY_PATTERN = re.compile(SESSION_ENTITY_CONFIG.session_entity_pattern)
GROUP_PATTERN = re.compile(SESSION_ENTITY_CONFIG.session_group_pattern, flags=re.IGNORECASE)
FAMILY_HEADING_PATTERN = re.compile(SESSION_ENTITY_CONFIG.session_family_heading_pattern, re.MULTILINE)
SENTENCE_PATTERN = re.compile(SESSION_ENTITY_CONFIG.session_sentence_pattern)


@dataclass
class EntityCandidate:
    name: str
    entity_type: str
    count: int = 0
    evidence: list[str] = field(default_factory=list)
    known: bool = False

    @property
    def score(self) -> int:
        return (100 if self.known else 0) + self.count * 5 + (8 if " " in self.name else 0)


def derived_lore_entity_relationships(
    source_id: str,
    source_name: str,
    source_type: str,
    source_file: str,
    text: str,
    known_character_names: list[str] | None = None,
    known_place_names: list[str] | None = None,
    max_characters: int | None = None,
    max_places: int | None = None,
    max_groups: int | None = None,
    max_artifacts: int | None = None,
) -> list[dict[str, str]]:
    config = session_entity_config()
    max_characters = max_characters if max_characters is not None else config.session_max_derived_characters
    max_places = max_places if max_places is not None else config.session_max_derived_places
    max_groups = max_groups if max_groups is not None else config.session_max_derived_groups
    max_artifacts = max_artifacts if max_artifacts is not None else config.session_max_derived_artifacts
    candidates = extract_lore_entity_candidates(
        text,
        known_character_names=known_character_names or [],
        known_place_names=known_place_names or [],
    )
    characters = sorted(
        [candidate for candidate in candidates if candidate.entity_type == "character"],
        key=lambda candidate: (-candidate.score, candidate.name.lower()),
    )[:max_characters]
    places = sorted(
        [candidate for candidate in candidates if candidate.entity_type == "place"],
        key=lambda candidate: (-candidate.score, candidate.name.lower()),
    )[:max_places]
    groups = sorted(
        [candidate for candidate in candidates if candidate.entity_type == "group"],
        key=lambda candidate: (-candidate.score, candidate.name.lower()),
    )[:max_groups]
    artifacts = sorted(
        [candidate for candidate in candidates if candidate.entity_type == "artifact"],
        key=lambda candidate: (-candidate.score, candidate.name.lower()),
    )[:max_artifacts]

    relationships = family_heading_relationships(source_id, source_name, source_type, source_file, text)
    for candidate in [*characters, *places, *groups, *artifacts]:
        relationship = {
            "character": "Mentioned",
            "place": "Location",
            "group": "Mentioned",
            "artifact": "Artifact",
        }.get(candidate.entity_type, "Mentioned")
        evidence_items = candidate.evidence or [""]
        for evidence in evidence_items:
            relationships.append(
                {
                    "source_id": source_id,
                    "source_name": source_name,
                    "source_type": source_type,
                    "source_file": source_file,
                    "target_id": compact(candidate.name),
                    "target_name": candidate.name,
                    "target_type": candidate.entity_type,
                    "relationship": relationship,
                    "evidence": evidence,
                }
            )
    return relationships


def family_heading_relationships(
    source_id: str,
    source_name: str,
    source_type: str,
    source_file: str,
    text: str,
) -> list[dict[str, str]]:
    relationships: list[dict[str, str]] = []
    seen: set[str] = set()
    for match in FAMILY_HEADING_PATTERN.finditer(text):
        family_name = canonical_family_name(match.group("name"))
        key = compact(family_name)
        if key in seen:
            continue
        seen.add(key)
        relationships.append(
            {
                "source_id": source_id,
                "source_name": source_name,
                "source_type": source_type,
                "source_file": source_file,
                "target_id": f"family_{key}",
                "target_name": f"{family_name} Family",
                "target_type": "family",
                "relationship": "Family",
                "evidence": match.group(0).strip().lstrip("#").strip(),
            }
        )
    return relationships


def canonical_family_name(name: str) -> str:
    cleaned = clean_candidate(name).title()
    return session_entity_config().session_canonical_family_names.get(compact(cleaned), cleaned)


def extract_lore_entity_candidates(
    text: str,
    known_character_names: list[str] | None = None,
    known_place_names: list[str] | None = None,
) -> list[EntityCandidate]:
    known_characters = {compact(name): name for name in known_character_names or []}
    known_places = {compact(name): name for name in known_place_names or []}
    candidate_text = text_without_markdown_headings(text)
    counts: Counter[str] = Counter()
    display_names: dict[str, str] = {}
    aliases_by_key: dict[str, set[str]] = {}
    group_counts: Counter[str] = Counter()
    group_display_names: dict[str, str] = {}
    group_aliases_by_key: dict[str, set[str]] = {}
    for raw_group in group_candidates(candidate_text):
        group_name = canonical_group_name(raw_group)
        key = compact(group_name)
        group_display_names.setdefault(key, group_name)
        group_aliases_by_key.setdefault(key, set()).update({raw_group, group_name})
        group_counts[key] += 1
    for raw_candidate in ENTITY_PATTERN.findall(normalize_honorific_periods(candidate_text)):
        raw_name = clean_candidate(raw_candidate)
        candidate = canonical_entity_name(raw_name)
        if not is_candidate_entity(candidate):
            continue
        key = compact(candidate)
        if key in group_counts:
            continue
        display_names.setdefault(key, known_characters.get(key) or known_places.get(key) or candidate)
        aliases_by_key.setdefault(key, set()).update({raw_name, candidate, display_names[key]})
        counts[key] += 1

    sentences = split_sentences(candidate_text)
    candidates: list[EntityCandidate] = []
    for key, count in group_counts.items():
        name = group_display_names[key]
        candidates.append(
            EntityCandidate(
                name=name,
                entity_type="group",
                count=count,
                evidence=evidence_for_entity(sentences, name, group_aliases_by_key.get(key, set())),
                known=False,
            )
        )
    for key, count in counts.items():
        name = display_names[key]
        if key in known_places or looks_like_place(name):
            entity_type = "place"
        elif looks_like_artifact(name):
            entity_type = "artifact"
        else:
            entity_type = "character"
        if entity_type == "character" and key not in known_characters and count < minimum_character_mentions(name):
            continue
        candidate = EntityCandidate(
            name=name,
            entity_type=entity_type,
            count=count,
            evidence=evidence_for_entity(
                sentences,
                name,
                aliases_by_key.get(key, set()),
                include_short_aliases=entity_type != "artifact",
            ),
            known=key in known_characters or key in known_places,
        )
        candidates.append(candidate)
    return candidates


def text_without_markdown_headings(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def group_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    for match in GROUP_PATTERN.finditer(normalize_honorific_periods(text)):
        raw_group = match.group(0)
        if compact(raw_group) in {"cult", "thecult"}:
            continue
        cleaned = clean_candidate(raw_group)
        if cleaned and cleaned not in candidates:
            candidates.append(cleaned)
    return candidates


def canonical_group_name(name: str) -> str:
    cleaned = " ".join(name.replace("’", "'").split()).strip(" .,:;!?")
    match = re.match(r"^(?:the\s+)?cult\s+of\s+([A-Za-z]+)$", cleaned, flags=re.IGNORECASE)
    if match:
        return f"{match.group(1).title()} Cult"
    match = re.match(r"^(?:the\s+)?([A-Za-z]+)\s+cult$", cleaned, flags=re.IGNORECASE)
    if match:
        return f"{match.group(1).title()} Cult"
    return cleaned.title()


def minimum_character_mentions(name: str) -> int:
    return 1 if " " in name else 2


def clean_candidate(value: str) -> str:
    cleaned = " ".join(value.replace("’", "'").replace("`", "'").split())
    cleaned = re.sub(r"^(Mr|Mrs|Ms|Mx|Dr)([A-Z])", r"\1 \2", cleaned)
    return re.sub(r"\s+", " ", cleaned.strip(" .,:;!?"))


def is_candidate_entity(value: str) -> bool:
    config = session_entity_config()
    parts = value.split()
    if not parts:
        return False
    if parts[0] in config.session_non_entity_starts:
        return False
    if value in config.session_generic_entities:
        return False
    if any(part in config.session_rejected_name_parts for part in parts):
        return False
    if any(part.lower() == "bickering" for part in parts):
        return False
    if "Session" in parts:
        return False
    if len(value) <= 2:
        return False
    return True


def canonical_entity_name(name: str) -> str:
    return session_entity_config().session_canonical_names.get(compact(name), name)


def looks_like_place(name: str) -> bool:
    place_words = session_entity_config().session_place_words
    lowered = name.lower()
    return any(word in lowered for word in place_words)


def looks_like_artifact(name: str) -> bool:
    artifact_words = session_entity_config().session_artifact_words
    lowered = name.lower()
    return any(lowered == word or lowered.endswith(f" {word}") for word in artifact_words)


def session_entity_config() -> CharacterExtractionConfig:
    return load_character_extraction_config()


def evidence_for_entity(
    sentences: list[str],
    name: str,
    aliases: set[str] | None = None,
    *,
    include_short_aliases: bool = True,
) -> list[str]:
    refs = {name, *(aliases or set())}
    if include_short_aliases:
        honorifics = {word.lower().rstrip(".") for word in session_entity_config().honorific_words}
        for alias in list(refs):
            parts = alias.split()
            if len(parts) > 1 and parts[0].lower().rstrip(".") not in honorifics:
                refs.add(parts[0])
    return [
        sentence
        for sentence in sentences
        if any(re.search(rf"\b{re.escape(ref)}\b", sentence, re.IGNORECASE) for ref in refs)
    ]


def split_sentences(text: str) -> list[str]:
    sentences = []
    for match in SENTENCE_PATTERN.findall(normalize_honorific_periods(text.replace("\r\n", "\n"))):
        sentence = " ".join(match.strip().split())
        if sentence:
            sentences.append(sentence)
    return sentences


def normalize_honorific_periods(text: str) -> str:
    return re.sub(r"\b(Mr|Mrs|Ms|Mx|Dr)\.", r"\1", text)


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())
