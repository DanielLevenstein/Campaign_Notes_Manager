from __future__ import annotations

import pytest

from src.extraction.extraction import extract_character_graph
from src.graph.combined_graph import build_combined_character_graph
from src.graph.projections import derived_lore_relationships, place_source_rows
from src.ingest.ingest import load_backstory
from src.persistence.lore_documents import Character, Place
from tests.support.test_paths import (
    CHARACTER_SHEETS_FIXTURE_DIR,
    PLACES_FIXTURE_DIR,
    SESSION_NOTES_FIXTURE_DIR,
)


XFAIL_REASON = "Expected node contract is not fully met; remove xfail after node canonicalization fixes land."

# These constants mirror tests/fixtures/Expected_Nodes.md, which is a source
# note compiled from the other fixtures rather than runtime test data.
EXPECTED_PARTY_CHARACTERS = {
    "Jory Ravenmark",
    "Neal Lovington",
    "Orin Nightbloom",
}
EXPECTED_MAIN_PLACES = {
    "Atlantia",
    "The Harbor",
    "The Watch Tower",
}
EXPECTED_MAIN_ARTIFACTS = {
    "Moon Blade",
    "Moon Gate",
}
EXPECTED_MINOR_ARTIFACTS = {
    "silver key", # From session 1,
    "Scroll Case",  # with a cracked seal From session 4
    "damaged mural", # at the base of the tower from session 5
    "secret door", # hidden behind the damaged mural from session 5
}


def expected_combined_graph():
    characters = [
        Character(name=path.stem, path=path)
        for path in sorted(CHARACTER_SHEETS_FIXTURE_DIR.glob("*.md"))
    ]
    places = [
        Place(name=path.stem, path=path)
        for path in sorted(PLACES_FIXTURE_DIR.glob("*.md"))
    ]
    lore_paths = [
        *sorted(CHARACTER_SHEETS_FIXTURE_DIR.glob("*.md")),
        *sorted(PLACES_FIXTURE_DIR.glob("*.md")),
        *sorted(SESSION_NOTES_FIXTURE_DIR.glob("*.md")),
    ]
    graphs = [
        extract_character_graph(load_backstory(path, character_id=path.stem))
        for path in lore_paths
    ]
    return build_combined_character_graph(
        graphs,
        place_sources=place_source_rows(places),
        lore_relationships=derived_lore_relationships(
            characters=characters,
            places=places,
            graphs=graphs,
            lore_paths=lore_paths,
        ),
    )


def node_names_by_type(node_type: str) -> set[str]:
    graph = expected_combined_graph()
    return {
        node.name
        for node in graph.characters.values()
        if node.node_type == node_type and not node.is_source
    }


def test_expected_party_character_nodes_are_present():
    assert EXPECTED_PARTY_CHARACTERS <= node_names_by_type("character")


@pytest.mark.xfail(reason=XFAIL_REASON)
def test_expected_main_place_nodes_are_present():
    assert EXPECTED_MAIN_PLACES <= node_names_by_type("place")


@pytest.mark.xfail(reason=XFAIL_REASON)
def test_expected_artifact_nodes_are_present():
    assert (EXPECTED_MAIN_ARTIFACTS | EXPECTED_MINOR_ARTIFACTS) <= node_names_by_type("artifact")
