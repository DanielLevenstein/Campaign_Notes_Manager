from __future__ import annotations

from dataclasses import dataclass, field

from character_graph.combined_graph import CombinedCharacterGraph, full_character_connection_graph
from src.graph.projections import CombinedGraphProjection


@dataclass(frozen=True)
class RelationshipGraphPresentation:
    graph: CombinedCharacterGraph
    relationship_rows: list[dict[str, str]] = field(default_factory=list)
    main_character_ids: set[str] = field(default_factory=set)
    main_place_ids: set[str] = field(default_factory=set)
    graphviz_config_key: str = ""
    empty_message: str = "No graph connections were found."

    @property
    def has_graph(self) -> bool:
        return bool(self.graph.characters)


def party_view_presentation(projection: CombinedGraphProjection) -> RelationshipGraphPresentation:
    return RelationshipGraphPresentation(
        graph=full_character_connection_graph(projection.character_sheet_combined),
        relationship_rows=projection.character_sheet_detail_rows,
        main_character_ids=projection.main_character_ids,
        graphviz_config_key="party_view_fixture",
        empty_message="Add Character Sheets To See Party Connections.",
    )
