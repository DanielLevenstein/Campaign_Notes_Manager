from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from src.extraction.config import CharacterExtractionConfig, load_character_extraction_config


SESSION_ENTITY_CONFIG = load_character_extraction_config()
ENTITY_PATTERN = re.compile(SESSION_ENTITY_CONFIG.session_entity_pattern)
GROUP_PATTERN = re.compile(SESSION_ENTITY_CONFIG.session_group_pattern, flags=re.IGNORECASE)
FAMILY_HEADING_PATTERN = re.compile(SESSION_ENTITY_CONFIG.session_family_heading_pattern, re.MULTILINE)
SENTENCE_PATTERN = re.compile(SESSION_ENTITY_CONFIG.session_sentence_pattern)
MARKDOWN_HEADING_PATTERN = re.compile(r"^(?P<marker>#{1,6})\s+(?P<text>.*?)\s*#*\s*$")


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


@dataclass(frozen=True)
class EvidenceContext:
    source_line: int
    heading_stack: list[dict[str, str | int]]
    context_anchor_id: str
    visible_ancestor_context_ids: dict[str, str]


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
) -> list[dict[str, Any]]:
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

    evidence_contexts = evidence_contexts_by_sentence(text)
    relationships = family_heading_relationships(source_id, source_name, source_type, source_file, text)
    selected_candidates = [*characters, *places, *groups, *artifacts]
    for candidate in selected_candidates:
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
                    "relationship_kind": "context_anchor",
                    "evidence": evidence,
                    **relationship_context_fields(evidence_contexts.get(evidence)),
                }
            )
    relationships.extend(
        direct_context_relationships(
            selected_candidates,
            source_file=source_file,
            evidence_contexts=evidence_contexts,
        )
    )
    return relationships


def direct_context_relationships(
    candidates: list[EntityCandidate],
    *,
    source_file: str,
    evidence_contexts: dict[str, EvidenceContext],
) -> list[dict[str, Any]]:
    by_evidence: dict[str, list[EntityCandidate]] = {}
    for candidate in candidates:
        for evidence in candidate.evidence:
            by_evidence.setdefault(evidence, []).append(candidate)

    relationships: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for evidence, evidence_candidates in by_evidence.items():
        unique_candidates = list({compact(candidate.name): candidate for candidate in evidence_candidates}.values())
        if len(unique_candidates) < 2:
            continue
        for source_candidate in unique_candidates:
            for target_candidate in unique_candidates:
                if source_candidate is target_candidate:
                    continue
                if source_candidate.entity_type != "character":
                    continue
                if target_candidate.entity_type == "character":
                    continue
                key = (compact(source_candidate.name), compact(target_candidate.name), evidence)
                if key in seen:
                    continue
                seen.add(key)
                relationships.append(
                    {
                        "source_id": compact(source_candidate.name),
                        "source_name": source_candidate.name,
                        "source_type": source_candidate.entity_type,
                        "source_file": source_file,
                        "target_id": compact(target_candidate.name),
                        "target_name": target_candidate.name,
                        "target_type": target_candidate.entity_type,
                        "relationship": "Mentioned With",
                        "relationship_kind": "direct_context",
                        "evidence": evidence,
                        **relationship_context_fields(evidence_contexts.get(evidence), include_heading_stack=False),
                    }
                )
    return relationships


def relationship_context_fields(
    context: EvidenceContext | None,
    *,
    include_heading_stack: bool = True,
) -> dict[str, Any]:
    if context is None:
        return {}
    fields: dict[str, Any] = {
        "source_line": context.source_line,
        "context_anchor_id": context.context_anchor_id,
    }
    if include_heading_stack:
        fields["heading_stack"] = context.heading_stack
        fields["visible_ancestor_context_ids"] = context.visible_ancestor_context_ids
    return fields


def evidence_contexts_by_sentence(text: str) -> dict[str, EvidenceContext]:
    contexts: dict[str, EvidenceContext] = {}
    heading_stack: list[dict[str, str | int]] = []
    for line_number, line in enumerate(text.replace("\r\n", "\n").splitlines(), start=1):
        heading = MARKDOWN_HEADING_PATTERN.match(line.strip())
        if heading:
            level = len(heading.group("marker"))
            heading_text = heading.group("text").strip()
            heading_stack = [
                item for item in heading_stack if isinstance(item["level"], int) and item["level"] < level
            ]
            heading_stack.append(
                {
                    "level": level,
                    "text": heading_text,
                    "id": source_heading_id(level, heading_text),
                }
            )
            continue
        for sentence in split_sentences(line):
            contexts.setdefault(
                sentence,
                EvidenceContext(
                    source_line=line_number,
                    heading_stack=list(heading_stack),
                    context_anchor_id=context_anchor_id(heading_stack),
                    visible_ancestor_context_ids=visible_ancestor_context_ids(heading_stack),
                ),
            )
    return contexts


def source_heading_id(level: int, text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return f"source_heading_{level}_{slug}"


def context_anchor_id(heading_stack: list[dict[str, str | int]]) -> str:
    if not heading_stack:
        return ""
    return str(heading_stack[-1]["id"])


def visible_ancestor_context_ids(heading_stack: list[dict[str, str | int]]) -> dict[str, str]:
    return {
        f"hide_h{level}": str(visible_heading["id"])
        for level in (1, 2, 3)
        if (visible_heading := visible_heading_for_hidden_level(heading_stack, level)) is not None
    }


def visible_heading_for_hidden_level(
    heading_stack: list[dict[str, str | int]],
    hidden_level: int,
) -> dict[str, str | int] | None:
    visible = [
        heading
        for heading in heading_stack
        if isinstance(heading["level"], int) and heading["level"] < hidden_level
    ]
    return visible[-1] if visible else None


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
