from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Callable

import streamlit as st

from src.graph.combined_graph import (
    CombinedCharacterGraph,
    CombinedCharacterNode,
    CombinedRelationshipEdge,
    clean_evidence_text,
    combined_relationship_dot,
    combined_relationship_rows,
    compact,
    dedupe_combined_edges,
    is_heading_node,
    is_lore_source_node,
    is_session_notes_node,
    other_connection_rows,
    other_connections_graph,
)
from src.graph.graphviz_config import load_graphviz_config
from src.graph.presentation import RelationshipGraphPresentation
from src.persistence.storage import read_markdown


@dataclass(frozen=True)
class KnowledgeGraphView:
    key: str
    label: str


@dataclass(frozen=True)
class LoreGraphViewDefinition:
    view_name: str
    source_predicate: Callable[[CombinedCharacterNode], bool]
    projection: Callable[..., CombinedCharacterGraph]
    column_layout: str
    graphviz_config_key: str
    source_empty_message: str
    graph_empty_message: str
    source_key: str
    heading_key: str | None = None
    heading_empty_message: str = ""
    show_lore_notes: bool = False
    hide_source_document_roots: bool = False
    fanout_linked_characters: bool = True
    supports_heading_filter: bool = False
    supports_directory_hide_options: bool = False
    include_all_heading_option: bool = False
    default_source_file: str | None = None


@dataclass(frozen=True)
class LoreGraphViewSelection:
    view_name: str
    source_file: str
    heading_id: str | None = None
    hidden_heading_levels: set[int] | None = None
    hide_source_document_roots: bool = False


@dataclass(frozen=True)
class MarkdownSubheading:
    id: str
    text: str
    level: int
    line_index: int
    parent_id: str


SINGLE_CHARACTER_TAB = "Character View"
PARTY_VIEW_TAB = "Party View"
FILE_VIEW_TAB = "File View"
SESSION_VIEW_TAB = "Section View"
DIRECTORY_FILE_VIEW_TAB = "Directory View"
DIRECTORY_VIEW_TAB = DIRECTORY_FILE_VIEW_TAB
PLACES_HEADING_VIEW_TAB = "Heading View"
PLACES_FILE_VIEW_TAB = "Location View"
SESSION_HEADING_VIEW_TAB = "Heading View"
SESSION_FILE_VIEW_TAB = "Session View"
FULL_KNOWLEDGE_GRAPH_TAB = "Full Knowledge Graph"
GRAPH_VIEW_TABS = [
    SINGLE_CHARACTER_TAB,
    PARTY_VIEW_TAB,
    PLACES_FILE_VIEW_TAB,
    SESSION_FILE_VIEW_TAB,
]

DIRECTORY_SESSION_VIEW_TAB = "Directory Section View"

STRUCTURED_CHARACTER_VIEW = KnowledgeGraphView(
    key="character_view",
    label="Character View",
)
CHARACTER_DATA_ONLY_VIEW = KnowledgeGraphView(
    key="party_view_fixture",
    label="Character Data Only",
)
LORE_GRAPH_CONFIG = KnowledgeGraphView(
    key="heading_view",
    label="Lore Graph",
)
SESSION_MONTH_VIEW = KnowledgeGraphView(
    key="full_structured_graph",
    label="Month Selection",
)
STRUCTURED_KNOWLEDGE_VIEW = KnowledgeGraphView(
    key="full_knowledge_graph",
    label=FULL_KNOWLEDGE_GRAPH_TAB,
)

def graph_tab_names(active_main_tab: str, *, include_full_knowledge_graph: bool = False) -> list[str]:
    tabs = list(GRAPH_VIEW_TABS)
    if include_full_knowledge_graph:
        tabs.append(FULL_KNOWLEDGE_GRAPH_TAB)
    return tabs


def lore_graph_view_definitions(active_main_tab: str, *, default_session_source_file: str | None = None) -> dict[str, LoreGraphViewDefinition]:
    return {
        PLACES_FILE_VIEW_TAB: LoreGraphViewDefinition(
            view_name=PLACES_FILE_VIEW_TAB,
            source_predicate=is_place_source_document_node,
            projection=place_lore_graph,
            column_layout="place_lore_directory",
            graphviz_config_key="location_view",
            source_empty_message="Add Place Lore To Use Location View.",
            heading_empty_message="Add Markdown Headings To Place Lore To Use Location View.",
            graph_empty_message="No Place Lore Connections Were Found For This File.",
            source_key="location_view_source_file",
            heading_key="location_view_heading",
            hide_source_document_roots=True,
            supports_heading_filter=True,
            supports_directory_hide_options=True,
            include_all_heading_option=True,
        ),
        SESSION_FILE_VIEW_TAB: LoreGraphViewDefinition(
            view_name=SESSION_FILE_VIEW_TAB,
            source_predicate=is_session_note_node,
            projection=markdown_header_lore_graph,
            column_layout="session_note_lore_directory",
            graphviz_config_key="session_view",
            source_empty_message="Add Session Notes To Use Session View.",
            heading_empty_message="Add Markdown Headings To Session Notes To Use Session View.",
            graph_empty_message="No Session Note Connections Were Found For This File.",
            source_key="session_view_source_file",
            heading_key="session_view_heading",
            hide_source_document_roots=True,
            supports_heading_filter=True,
            supports_directory_hide_options=True,
            include_all_heading_option=True,
            default_source_file=default_session_source_file,
        ),
    }


DISALLOWED_PLACE_GRAPH_CHARACTER_KEYS = {"family", "stone", "students"}
PLACE_GRAPH_MARKDOWN_HEADING_RE = re.compile(r"^(?P<marker>#{1,3})\s+(?P<text>.*?)\s*#*\s*$")
PLACE_HEADING_SUFFIXES = {
    "Academy",
    "Bastion",
    "Cavern",
    "City",
    "College",
    "Coast",
    "Court",
    "Fortress",
    "Forest",
    "Guild",
    "Hall",
    "Halls",
    "Harbor",
    "Keep",
    "Kingdom",
    "Library",
    "Mage College",
    "Monastery",
    "School",
    "Sea",
    "Shore",
    "Shores",
    "Temple",
    "Tower",
    "Tavern",
    "University",
    "Village",
}
GROUP_HEADING_SUFFIXES = {
    "Council",
    "Cult",
    "Family",
    "Guild",
    "Order",
}
ARTIFACT_HEADING_SUFFIXES = {
    "Amulet",
    "Blade",
    "Book",
    "Crown",
    "Gem",
    "Key",
    "Lantern",
    "Map",
    "Mask",
    "Orb",
    "Relic",
    "Ring",
    "Scroll",
    "Shard",
    "Sigil",
    "Staff",
    "Stone",
    "Sword",
}
SEMANTIC_LORE_NODE_TYPES = {"place", "group", "artifact"}


def render_knowledge_graph_tabs(
    *,
    combined: CombinedCharacterGraph,
    character_sheet_combined: CombinedCharacterGraph,
    character_sheet_detail_rows: list[dict[str, str]],
    party_view: RelationshipGraphPresentation,
    character_nodes: list[CombinedCharacterNode],
    main_character_ids: set[str],
    main_place_ids: set[str],
    graph_revision: int,
    label_font_color: str,
    active_main_tab: str = "Characters",
    include_full_knowledge_graph: bool = False,
) -> None:
    pending_import_source_file = st.session_state.pop("session_notes_imported_source_file", None)
    lore_view_definitions = lore_graph_view_definitions(
        active_main_tab,
        default_session_source_file=pending_import_source_file,
    )
    tab_names = graph_tab_names(
        active_main_tab,
        include_full_knowledge_graph=include_full_knowledge_graph,
    )
    tabs = st.tabs(tab_names)
    for tab, tab_name in zip(tabs, tab_names):
        with tab:
            if tab_name == SINGLE_CHARACTER_TAB:
                render_single_character_tab(
                    combined=combined,
                    character_nodes=character_nodes,
                    main_character_ids=main_character_ids,
                    main_place_ids=main_place_ids,
                    graph_revision=graph_revision,
                    label_font_color=label_font_color,
                )
            elif tab_name == PARTY_VIEW_TAB:
                render_party_view_tab(party_view, label_font_color)
            elif tab_name in lore_view_definitions:
                render_lore_graph_view(
                    combined,
                    definition=lore_view_definitions[tab_name],
                    main_character_ids=main_character_ids,
                    label_font_color=label_font_color,
                )
            elif tab_name == FULL_KNOWLEDGE_GRAPH_TAB:
                render_full_knowledge_graph_view(
                    combined=combined,
                    main_character_ids=main_character_ids,
                    main_place_ids=main_place_ids,
                    label_font_color=label_font_color,
                )

def render_single_character_tab(
    *,
    combined: CombinedCharacterGraph,
    character_nodes: list[CombinedCharacterNode],
    main_character_ids: set[str],
    main_place_ids: set[str],
    graph_revision: int,
    label_font_color: str,
) -> None:
    if not character_nodes:
        st.info("Add Main Character Or Place Lore To See Graph Roots.")
        return
    render_structured_character_view(
        combined,
        character_nodes,
        graph_revision,
        main_character_ids,
        main_place_ids,
        label_font_color,
        load_graphviz_config(STRUCTURED_CHARACTER_VIEW.key),
    )


def render_party_view_tab(
    presentation: RelationshipGraphPresentation,
    label_font_color: str,
) -> None:
    render_presented_relationship_graph(presentation, label_font_color)


def render_lore_graph_view(
    combined: CombinedCharacterGraph,
    *,
    definition: LoreGraphViewDefinition,
    main_character_ids: set[str] | None = None,
    label_font_color: str,
) -> None:
    st.subheader(definition.view_name)
    selection = render_lore_graph_view_controls(combined, definition=definition)
    if selection is None:
        return
    projected_graph = project_lore_graph_for_view(combined, definition=definition, selection=selection)
    if not projected_graph.characters:
        st.info(definition.graph_empty_message)
        return
    render_lore_graph(
        projected_graph,
        label_font_color=label_font_color,
        column_layout=definition.column_layout,
        graphviz_config_key=definition.graphviz_config_key,
        main_character_ids=main_character_ids,
        show_lore_notes=definition.show_lore_notes,
        hide_source_document_roots=selection.hide_source_document_roots,
    )


def render_lore_graph_view_controls(
    graph: CombinedCharacterGraph,
    *,
    definition: LoreGraphViewDefinition,
) -> LoreGraphViewSelection | None:
    selected_source_file = render_lore_file_filter(
        graph,
        source_predicate=definition.source_predicate,
        label="Source File",
        key=definition.source_key,
        default_source_file=definition.default_source_file,
    )
    if selected_source_file is None:
        st.info(definition.source_empty_message)
        return None
    hide_source_document_roots = definition.hide_source_document_roots
    hidden_heading_levels: set[int] = set()
    if definition.supports_directory_hide_options:
        hide_source_document_roots, hidden_heading_levels = render_session_directory_hide_options(
            key=f"{definition.source_key}_hidden_elements",
            default_hide_file_name=definition.hide_source_document_roots,
        )
    selected_heading_id = None
    if definition.supports_heading_filter:
        source_graph = project_lore_graph(
            graph,
            projection=definition.projection,
            source_file=selected_source_file,
            fanout_linked_characters=definition.fanout_linked_characters,
            hide_source_document_roots=hide_source_document_roots,
            hidden_heading_levels=hidden_heading_levels,
        )
        selected_heading_id = render_lore_heading_filter(
            graph,
            source_predicate=definition.source_predicate,
            label="Heading Selected",
            key=definition.heading_key or f"{definition.source_key}_heading",
            projected_graph=source_graph,
            include_all_option=definition.include_all_heading_option,
            all_option_label=f"{Path(selected_source_file).name}",
        )
        if selected_heading_id == "":
            selected_heading_id = None
        if selected_heading_id is None and not definition.include_all_heading_option:
            st.info(definition.heading_empty_message)
            return None
    return LoreGraphViewSelection(
        view_name=definition.view_name,
        source_file=selected_source_file,
        heading_id=selected_heading_id,
        hidden_heading_levels=hidden_heading_levels,
        hide_source_document_roots=hide_source_document_roots,
    )


def project_lore_graph_for_view(
    graph: CombinedCharacterGraph,
    *,
    definition: LoreGraphViewDefinition,
    selection: LoreGraphViewSelection,
) -> CombinedCharacterGraph:
    return project_lore_graph(
        graph,
        projection=definition.projection,
        source_file=selection.source_file,
        heading_id=selection.heading_id,
        fanout_linked_characters=definition.fanout_linked_characters,
        hide_source_document_roots=selection.hide_source_document_roots,
        hidden_heading_levels=selection.hidden_heading_levels or set(),
    )


def project_lore_graph(
    graph: CombinedCharacterGraph,
    *,
    projection: Callable[..., CombinedCharacterGraph],
    source_file: str | None,
    heading_id: str | None = None,
    fanout_linked_characters: bool,
    hide_source_document_roots: bool,
    hidden_heading_levels: set[int] | None = None,
) -> CombinedCharacterGraph:
    projection_kwargs: dict[str, Any] = {
        "source_file": source_file,
        "heading_id": heading_id,
        "fanout_linked_characters": fanout_linked_characters,
        "hide_source_document_roots": hide_source_document_roots,
    }
    if projection is markdown_header_lore_graph:
        projection_kwargs["hidden_heading_levels"] = hidden_heading_levels or set()
    projected_graph = projection(graph, **projection_kwargs)
    if projection is not markdown_header_lore_graph and hidden_heading_levels:
        projected_graph = graph_without_markdown_heading_levels(projected_graph, hidden_heading_levels)
    return projected_graph


def render_place_file_view_tab(
    *,
    combined: CombinedCharacterGraph,
    label_font_color: str,
    column_layout: str = "place_lore",
    title: str = PLACES_FILE_VIEW_TAB,
    key: str = "place_lore_file_view_source_file",
    show_lore_notes: bool = False,
    hide_source_document_roots: bool = False,
) -> None:
    render_lore_graph_view(
        combined,
        definition=LoreGraphViewDefinition(
            view_name=title,
            source_predicate=is_place_source_document_node,
            projection=place_lore_graph,
            column_layout=column_layout,
            graphviz_config_key="location_view",
            source_empty_message="Add Place Lore To Use File View.",
            graph_empty_message="No Place Lore Connections Were Found For This File.",
            source_key=key,
            show_lore_notes=show_lore_notes,
            hide_source_document_roots=hide_source_document_roots,
        ),
        label_font_color=label_font_color,
    )


def render_place_heading_view_tab(
    *,
    combined: CombinedCharacterGraph,
    label_font_color: str,
    column_layout: str = "place_lore",
    title: str = SESSION_VIEW_TAB,
    key: str = "place_lore_session_view_heading",
    show_lore_notes: bool = True,
    hide_source_document_roots=True,
) -> None:
    render_lore_graph_view(
        combined,
        definition=LoreGraphViewDefinition(
            view_name=title,
            source_predicate=is_place_source_document_node,
            projection=place_lore_graph,
            column_layout=column_layout,
            graphviz_config_key="location_view",
            source_empty_message="Add Place Lore To Use Heading View.",
            heading_empty_message="Add Markdown Headings To Place Lore To Use Heading View.",
            graph_empty_message="No Place Lore Connections Were Found For This Heading.",
            source_key=f"{key}_source_file",
            heading_key=key,
            show_lore_notes=show_lore_notes,
            hide_source_document_roots=hide_source_document_roots,
            supports_heading_filter=True,
        ),
        label_font_color=label_font_color,
    )


def render_lore_graph(
    lore_graph: CombinedCharacterGraph,
    *,
    label_font_color: str,
    column_layout: str,
    graphviz_config_key: str = LORE_GRAPH_CONFIG.key,
    main_character_ids: set[str] | None = None,
    show_lore_notes: bool = False,
    hide_source_document_roots: bool = False,
) -> None:
    graphviz_config = {
        **load_graphviz_config(graphviz_config_key),
        "column_layout": column_layout,
    }
    deduplicate_source_document_nodes(lore_graph)
    note_rows = lore_information_rows(lore_graph) if show_lore_notes else []
    render_relationship_graph(
        lore_graph,
        main_character_ids=main_character_ids,
        label_font_color=label_font_color,
        graphviz_config=graphviz_config,
        relationship_rows=place_lore_connection_rows(lore_graph),
        lore_note_rows=note_rows,
        hide_source_document_roots=hide_source_document_roots
    )


def render_session_file_view_tab(
    *,
    combined: CombinedCharacterGraph,
    label_font_color: str,
    column_layout: str = "session_note_lore",
    title: str = FILE_VIEW_TAB,
    key: str = "session_lore_file_view_source_file",
    show_lore_notes: bool = False,
    hide_source_document_roots: bool = True,
) -> None:
    pending_import_source_file = st.session_state.pop("session_notes_imported_source_file", None)
    render_lore_graph_view(
        combined,
        definition=LoreGraphViewDefinition(
            view_name=title,
            source_predicate=is_session_note_node,
            projection=markdown_header_lore_graph,
            column_layout=column_layout,
            graphviz_config_key="session_view",
            source_empty_message="Add Session Notes To Use File View.",
            graph_empty_message="No Session Note Connections Were Found For This File.",
            source_key=key,
            show_lore_notes=show_lore_notes,
            hide_source_document_roots=hide_source_document_roots,
            supports_directory_hide_options=column_layout == "session_note_lore_directory",
            default_source_file=pending_import_source_file,
        ),
        label_font_color=label_font_color,
    )


def render_session_heading_view_tab(
    *,
    combined: CombinedCharacterGraph,
    label_font_color: str,
    column_layout: str = "session_note_lore",
    title: str = SESSION_VIEW_TAB,
    key: str = "session_lore_session_view_heading",
    show_lore_notes: bool = True,
    hide_source_document_roots: bool = True,
) -> None:
    render_lore_graph_view(
        combined,
        definition=LoreGraphViewDefinition(
            view_name=title,
            source_predicate=is_session_note_node,
            projection=markdown_header_lore_graph,
            column_layout=column_layout,
            graphviz_config_key="session_view",
            source_empty_message="Add Session Notes To Use Heading View.",
            heading_empty_message="Add Markdown Headings To Session Notes To Use Heading View.",
            graph_empty_message="No Session Note Connections Were Found For This Heading.",
            source_key=f"{key}_source_file",
            heading_key=f"{key}_heading",
            show_lore_notes=show_lore_notes,
            hide_source_document_roots=hide_source_document_roots,
            supports_heading_filter=True,
        ),
        label_font_color=label_font_color,
    )


def render_session_note_graph_tab(
    *,
    combined: CombinedCharacterGraph,
    main_character_ids: set[str],
    graph_revision: int,
    label_font_color: str,
) -> None:
    st.subheader(SESSION_MONTH_VIEW.label)
    session_graph = session_note_graph(combined)
    if not session_graph.characters:
        st.info("Add Session Notes To See The Session Note Graph.")
        return
    month_options = session_note_month_options(session_graph)
    selected_month = st.selectbox(
        "Month",
        month_options,
        key=f"session_note_graph_month_{graph_revision}",
    )
    month_graph = filter_session_note_graph_by_month(session_graph, selected_month)
    graphviz_config = load_graphviz_config(SESSION_MONTH_VIEW.key)
    session_source_ids = {
        node_id
        for node_id, node in month_graph.characters.items()
        if is_session_note_node(node)
    }
    render_relationship_graph(
        month_graph,
        main_character_ids=main_character_ids | session_source_ids,
        label_font_color=label_font_color,
        graphviz_config=graphviz_config,
    )


def render_structured_character_view(
    combined: CombinedCharacterGraph,
    character_nodes: list[CombinedCharacterNode],
    graph_revision: int,
    main_character_ids: set[str],
    main_place_ids: set[str],
    label_font_color: str,
    graphviz_config: dict[str, Any],
) -> None:
    character_tabs = st.tabs([node.name for node in character_nodes])
    for tab, node in zip(character_tabs, character_nodes):
        with tab:
            character_id = node.id
            node_options = combined_graph_root_node_options(character_nodes)
            node_labels = list(node_options)
            default_node_index = node_labels.index(node.name) if node.name in node_options else 0
            selected_node_label = st.selectbox(
                f"Graph Node For {node.name}",
                node_labels,
                index=default_node_index,
                key=f"combined_graph_node_{character_id}_{graph_revision}",
            )
            selected_node_id = node_options[selected_node_label]
            focused_graph = other_connections_graph(combined, selected_node_id)
            associated_rows = other_connection_rows(combined, selected_node_id)
            st.graphviz_chart(
                combined_relationship_dot(
                    focused_graph,
                    selected_node_id,
                    main_character_ids=main_character_ids,
                    main_place_ids=main_place_ids,
                    label_font_color=label_font_color,
                    graphviz_config=graphviz_config,
                ),
                width="stretch",
            )
            if associated_rows:
                st.subheader("Connections")
                st.table(associated_rows, hide_index=True, width="stretch")
            else:
                st.info("No Other Connections Were Found For This Node Yet.")


def render_presented_relationship_graph(
    presentation: RelationshipGraphPresentation,
    label_font_color: str,
) -> None:
    if not presentation.has_graph:
        st.info(presentation.empty_message)
        return
    render_relationship_graph(
        presentation.graph,
        main_character_ids=presentation.main_character_ids,
        main_place_ids=presentation.main_place_ids,
        label_font_color=label_font_color,
        graphviz_config=load_graphviz_config(presentation.graphviz_config_key),
        relationship_rows=presentation.relationship_rows,
    )


def render_full_knowledge_graph_view(
    *,
    combined: CombinedCharacterGraph,
    main_character_ids: set[str],
    main_place_ids: set[str],
    label_font_color: str,
) -> None:
    st.subheader(STRUCTURED_KNOWLEDGE_VIEW.label)
    if not combined.characters:
        st.info("Add Lore To See The Full Knowledge Graph.")
        return
    hide_source_files = st.checkbox(
        "Hide File Name",
        key="full_knowledge_graph_hidden_elements_file_name",
        value=False,
    )
    graph = full_knowledge_graph(
        combined,
        hide_source_files=hide_source_files,
    )
    render_relationship_graph(
        graph,
        main_character_ids=main_character_ids,
        main_place_ids=main_place_ids,
        label_font_color=label_font_color,
        graphviz_config=load_graphviz_config(STRUCTURED_KNOWLEDGE_VIEW.key),
    )


def full_knowledge_graph(
    graph: CombinedCharacterGraph,
    *,
    hide_source_files: bool = False,
) -> CombinedCharacterGraph:
    projected_graph = graph
    if hide_source_files:
        projected_graph = graph_without_source_document_roots(projected_graph)
    return graph_without_all_markdown_headings(projected_graph)


def graph_without_all_markdown_headings(graph: CombinedCharacterGraph) -> CombinedCharacterGraph:
    return graph_without_markdown_heading_nodes(
        graph,
        {
            node_id
            for node_id, node in graph.characters.items()
            if is_markdown_heading_node(node)
        },
    )


def render_structured_knowledge_view(
    combined: CombinedCharacterGraph,
    main_character_ids: set[str],
    main_place_ids: set[str],
    label_font_color: str,
    graphviz_config: dict[str, Any],
) -> None:
    render_relationship_graph(
        graph_without_lore_source_knots(combined),
        main_character_ids=main_character_ids,
        main_place_ids=main_place_ids,
        label_font_color=label_font_color,
        graphviz_config=graphviz_config,
    )


def render_relationship_graph(
    graph: CombinedCharacterGraph,
    *,
    main_character_ids: set[str] | None = None,
    main_place_ids: set[str] | None = None,
    label_font_color: str,
    graphviz_config: dict[str, Any],
    relationship_rows: list[dict[str, str]] | None = None,
    lore_note_rows: list[dict[str, str]] | None = None,
    hide_source_document_roots: bool = False,
) -> None:
    st.graphviz_chart(
        combined_relationship_dot(
            graph,
            main_character_ids=main_character_ids,
            main_place_ids=main_place_ids,
            label_font_color=label_font_color,
            graphviz_config=graphviz_config,
            hide_source_document_roots=hide_source_document_roots
        ),
        width="stretch",
    )
    if lore_note_rows:
        st.subheader("Lore Notes")
        st.table(lore_note_rows, hide_index=True, width="stretch")
    rows = relationship_rows if relationship_rows is not None else lore_graph_connection_rows(graph)
    if rows:
        st.subheader("Connections")
        st.table(rows, hide_index=True, width="stretch")

def render_lore_file_filter(
    graph: CombinedCharacterGraph,
    *,
    source_predicate: Callable[[CombinedCharacterNode], bool],
    label: str,
    key: str,
    default_source_file: str | None = None,
) -> str | None:
    options = lore_source_file_options(graph, source_predicate)
    if not options:
        return None
    labels = [option[0] for option in options]
    option_map = dict(options)
    selected_label = None
    default_index = 0
    if default_source_file is not None:
        normalized_default = normalized_lore_source_file(default_source_file)
        for index, option in enumerate(options):
            if normalized_lore_source_file(option[1]) == normalized_default:
                default_index = index
                selected_label = option[0]
                break
    if selected_label is not None:
        st.session_state[key] = selected_label
    selected_label = st.selectbox(label, labels, index=default_index, key=key)
    return option_map[selected_label]


def render_lore_heading_filter(
    graph: CombinedCharacterGraph,
    *,
    source_predicate: Callable[[CombinedCharacterNode], bool],
    label: str,
    key: str,
    projected_graph: CombinedCharacterGraph | None = None,
    include_all_option: bool = False,
    all_option_label: str = "All Elements",
) -> str | None:
    options = lore_heading_options(graph, source_predicate, projected_graph=projected_graph)
    if not options and not include_all_option:
        return None
    if include_all_option:
        options = [(all_option_label, "")] + options
    selected_label = st.selectbox(label, [option[0] for option in options], key=key)
    return dict(options)[selected_label]


def render_session_directory_hide_options(
    *,
    key: str,
    default_hide_file_name: bool,
) -> tuple[bool, set[int]]:
    columns = st.columns(4)
    with columns[0]:
        hide_file_name = st.checkbox(
            "Hide File Name",
            value=default_hide_file_name,
            key=f"{key}_file_name",
        )
    hidden_levels: set[int] = set()
    for column, level in zip(columns[1:], (1, 2, 3)):
        with column:
            if st.checkbox(f"Hide H{level} Headings", key=f"{key}_h{level}"):
                hidden_levels.add(level)
    return hide_file_name, hidden_levels


def lore_source_file_options(
    graph: CombinedCharacterGraph,
    source_predicate: Callable[[CombinedCharacterNode], bool],
) -> list[tuple[str, str]]:
    options = []
    for node in graph.characters.values():
        # Accept any node that has a source_file and matches the predicate.
        # Some imports create session-note related nodes that are not typed
        # as `source_document` but still reference a source file. Include
        # those so the file dropdown reflects actual files in lore.
        if not node.source_file or not source_predicate(node):
            continue
        source_path = Path(node.source_file)
        label = source_path.name or node.name
        options.append((label, node.source_file))
    return sorted(set(options), key=lambda item: item[0].lower())


def lore_heading_options(
    graph: CombinedCharacterGraph,
    source_predicate: Callable[[CombinedCharacterNode], bool],
    *,
    projected_graph: CombinedCharacterGraph | None = None,
) -> list[tuple[str, str]]:
    options = []
    allowed_heading_ids = None
    if projected_graph is not None:
        allowed_heading_ids = {
            node_id
            for node_id, node in projected_graph.characters.items()
            if is_markdown_heading_node(node)
        }
    source_ids = {
        node_id
        for node_id, node in graph.characters.items()
        if is_lore_projection_source_node(node, source_predicate)
    }
    for source_id, headings in markdown_subheadings_by_source(graph, source_ids).items():
        source = graph.characters[source_id]
        source_label = Path(source.source_file).name or source.name
        for heading in headings:
            if allowed_heading_ids is not None and heading.id not in allowed_heading_ids:
                semantic_type = markdown_heading_entity_type(heading.text, graph)
                display_name = semantic_heading_display_name(heading.text) if semantic_type else heading.text
                semantic_replacement_visible = (
                    semantic_type is not None
                    and projected_graph is not None
                    and any(
                        node.node_type == semantic_type and compact(node.name) == compact(display_name)
                        for node in projected_graph.characters.values()
                    )
                )
                if not semantic_replacement_visible:
                    continue
            options.append((f"{source_label} / H{heading.level}: {heading.text}", heading.id))
    return sorted(options, key=lambda item: item[0].lower())


def place_lore_graph(
    graph: CombinedCharacterGraph,
    *,
    source_file: str | None = None,
    heading_id: str | None = None,
    fanout_linked_characters: bool = False,
    hide_source_document_roots: bool = False,
) -> CombinedCharacterGraph:
    place_ids = {
        node_id
        for node_id, node in graph.characters.items()
        if node.node_type == "place" and not is_lore_source_node(node)
    }
    if not place_ids:
        return CombinedCharacterGraph()

    place_document_ids = {
        source_id
        for edge in graph.edges
        for source_id in edge_source_ids_for_place(edge, graph, place_ids)
    }
    source_document_ids = {
        node_id
        for node_id, node in graph.characters.items()
        if node_id in place_document_ids and is_lore_source_node(node)
    }
    if source_file is not None:
        source_document_ids = filter_source_document_ids_by_file(graph, source_document_ids, source_file)
        place_document_ids = place_document_ids & source_document_ids
    source_to_place_ids = place_ids_by_source_document(graph, source_document_ids, place_ids)
    root_place_ids = {
        place_id
        for source_place_ids in source_to_place_ids.values()
        for place_id in source_place_ids
    }
    connected_ids = set(source_document_ids)
    source_headings = markdown_subheadings_by_source(graph, source_document_ids)
    projected_nodes: dict[str, CombinedCharacterNode] = {}
    projected_edges: list[CombinedRelationshipEdge] = []
    semantic_heading_ids_by_source: dict[str, set[str]] = {}
    for source_id, headings in source_headings.items():
        source = graph.characters[source_id]
        for heading in headings:
            semantic_type = markdown_heading_entity_type(heading.text, graph)
            display_name = semantic_heading_display_name(heading.text) if semantic_type else heading.text
            projected_nodes[heading.id] = CombinedCharacterNode(
                id=heading.id,
                name=display_name,
                source_file=source.source_file,
                node_type=semantic_type or "note",
                is_heading=True,
                heading_level=heading.level,
            )
            if semantic_type in SEMANTIC_LORE_NODE_TYPES:
                semantic_heading_ids_by_source.setdefault(source_id, set()).add(heading.id)
                if semantic_type == "place":
                    root_place_ids.add(heading.id)
            connected_ids.add(heading.id)
            append_projected_edge(
                projected_edges,
                CombinedRelationshipEdge(
                    source=heading.parent_id or source_id,
                    target=heading.id,
                    relationship_type="heading",
                    relationship_label="",
                ),
            )
    append_place_heading_root_edges(
        graph,
        projected_nodes,
        source_to_place_ids,
        semantic_heading_ids_by_source,
        connected_ids,
        projected_edges,
    )
    for edge in graph.edges:
        if not edge_connects(edge, place_document_ids, place_ids):
            continue
        source_id = edge.source if edge.source in place_document_ids else edge.target
        place_id = edge.target if edge.source in place_document_ids else edge.source
        source = graph.characters.get(source_id)
        if is_lore_source_node(source):
            place = graph.characters.get(place_id)
            heading = markdown_subheading_for_edge(source, source_headings.get(source_id, []), edge, place)
            edge_source = heading.id if heading is not None else source_id
            edge_target = semantic_heading_for_node(place, heading, projected_nodes) or place_id
            connected_ids.add(edge_target)
            if edge_target == place_id:
                connected_ids.add(place_id)
            if (
                edge_source == edge_target
                and heading is not None
                and edge_target in projected_nodes
                and not has_non_heading_edge_to(projected_edges, edge_target)
            ):
                append_projected_edge(
                    projected_edges,
                    CombinedRelationshipEdge(
                        source=source_id,
                        target=edge_target,
                        relationship_type=edge.relationship_type,
                        relationship_label=edge.relationship_label,
                        evidence=list(edge.evidence),
                        bidirectional=edge.bidirectional,
                    ),
                )
            elif edge_source != edge_target:
                append_projected_edge(
                    projected_edges,
                    CombinedRelationshipEdge(
                        source=edge_source,
                        target=edge_target,
                        relationship_type=edge.relationship_type,
                        relationship_label="" if heading is not None else edge.relationship_label,
                        evidence=list(edge.evidence),
                        bidirectional=edge.bidirectional,
                    ),
                )
        else:
            adjacent = graph.characters.get(edge.target if edge.source in place_ids else edge.source)
            if adjacent is not None and adjacent.node_type == "character" and is_disallowed_place_graph_character(adjacent):
                continue
            append_projected_edge(projected_edges, place_character_edge_from_place(edge, graph, place_ids))
    for edge in graph.edges:
        if edge.source in place_ids or edge.target in place_ids:
            source = graph.characters.get(edge.source)
            target = graph.characters.get(edge.target)
            if is_lore_source_node(source):
                continue
            if is_lore_source_node(target):
                continue
            place_id = edge.source if edge.source in place_ids else edge.target
            if source_file is not None and place_id not in root_place_ids:
                continue
            adjacent = target if edge.source in place_ids else source
            if adjacent is not None and adjacent.node_type == "character" and is_disallowed_place_graph_character(adjacent):
                continue
            connected_ids.update({edge.source, edge.target})
    if fanout_linked_characters:
        append_linked_character_fanout(
            graph,
            root_ids=root_place_ids,
            connected_ids=connected_ids,
            projected_edges=projected_edges,
            include_character=lambda node: not is_disallowed_place_graph_character(node),
        )
    for edge in graph.edges:
        if edge.source not in source_document_ids and edge.target not in source_document_ids:
            continue
        source_id = edge.source if edge.source in source_document_ids else edge.target
        adjacent_id = edge.target if edge.source in source_document_ids else edge.source
        adjacent = graph.characters.get(adjacent_id)
        if adjacent is None or adjacent.node_type != "character":
            continue
        if is_disallowed_place_graph_character(adjacent):
            continue
        heading = markdown_subheading_for_edge(
            graph.characters[source_id],
            source_headings.get(source_id, []),
            edge,
            adjacent,
        )
        if heading is None:
            character_source_ids = source_to_place_ids[source_id]
        else:
            semantic_heading_id = nearest_semantic_heading_id(heading, projected_nodes, source_headings.get(source_id, []))
            character_source_ids = {semantic_heading_id or heading.id}
        if not character_source_ids:
            continue
        connected_ids.add(adjacent_id)
        for character_source_id in character_source_ids:
            projected_edge = CombinedRelationshipEdge(
                source=character_source_id,
                target=adjacent_id,
                relationship_type=edge.relationship_type,
                relationship_label=edge.relationship_label,
                evidence=list(edge.evidence),
                bidirectional=edge.bidirectional,
            )
            character_source = projected_nodes.get(character_source_id, graph.characters.get(character_source_id))
            if character_source is not None and character_source.node_type in {"group", "artifact"}:
                projected_edge = projected_lore_context_edge(
                    source=character_source_id,
                    target=adjacent_id,
                    nodes={**graph.characters, **projected_nodes},
                    relationship_type=edge.relationship_type,
                    relationship_label=edge.relationship_label,
                    evidence=list(edge.evidence),
                    bidirectional=edge.bidirectional,
                )
            append_projected_edge(projected_edges, projected_edge)
    semantic_heading_by_entity_id_map = semantic_heading_by_original_entity_id(graph, projected_nodes)
    projected_edges = retarget_semantic_heading_edges(projected_edges, semantic_heading_by_entity_id_map)
    connected_ids = {
        semantic_heading_by_entity_id_map.get(node_id, node_id)
        for node_id in connected_ids
    }
    projected_edges = prune_unassociated_markdown_headings(
        connected_ids,
        projected_nodes,
        projected_edges,
        graph.characters,
    )
    connected_ids = connected_ids & node_ids_in_edges(projected_edges)
    projected_graph = CombinedCharacterGraph(
        characters={
            **{
                node_id: node
                for node_id, node in graph.characters.items()
                if node_id in connected_ids and node.node_type in {"source_document", "note", "place", "group", "artifact", "character"}
            },
            **projected_nodes,
        },
        edges=[
            edge
            for edge in projected_edges
            if edge.source in connected_ids and edge.target in connected_ids
        ],
    )
    if hide_source_document_roots:
        projected_graph = graph_without_source_document_roots(projected_graph)
    return filter_lore_graph_by_heading(projected_graph, heading_id) if heading_id is not None else projected_graph


def markdown_header_lore_graph(
    graph: CombinedCharacterGraph,
    *,
    source_file: str | None = None,
    heading_id: str | None = None,
    fanout_linked_characters: bool = False,
    hide_source_document_roots: bool = False,
    hidden_heading_levels: set[int] | None = None,
    hidden_heading_ids: set[str] | None = None,
) -> CombinedCharacterGraph:
    source_document_ids = {
        node_id
        for node_id, node in graph.characters.items()
        if is_lore_projection_source_node(node, is_session_note_node)
        or is_lore_projection_source_node(node, is_place_source_document_node)
    }
    if source_file is not None:
        source_document_ids = filter_source_document_ids_by_file(graph, source_document_ids, source_file)
    if not source_document_ids:
        return CombinedCharacterGraph()
    connected_ids = set(source_document_ids)
    source_headings = markdown_subheadings_by_source(graph, source_document_ids)
    projected_nodes: dict[str, CombinedCharacterNode] = {}
    projected_edges: list[CombinedRelationshipEdge] = []
    root_lore_ids: set[str] = set()
    semantic_entity_id_by_heading_id: dict[str, str] = {}
    for source_id, headings in source_headings.items():
        source = graph.characters[source_id]
        for heading in headings:
            semantic_type = markdown_heading_entity_type(heading.text, graph)
            display_name = semantic_heading_display_name(heading.text) if semantic_type else heading.text
            heading_target_id = matching_semantic_entity_id(graph, display_name, semantic_type, source.source_file)
            if heading_target_id:
                semantic_entity_id_by_heading_id[heading.id] = heading_target_id
                root_lore_ids.add(heading_target_id)
                connected_ids.add(heading_target_id)
            else:
                heading_target_id = heading.id
                projected_nodes[heading.id] = CombinedCharacterNode(
                    id=heading.id,
                    name=display_name,
                    source_file=source.source_file,
                    node_type=semantic_type or "note",
                    is_heading=True,
                    heading_level=heading.level,
                )
                if semantic_type in SEMANTIC_LORE_NODE_TYPES:
                    root_lore_ids.add(heading.id)
                connected_ids.add(heading.id)
            append_projected_edge(
                projected_edges,
                CombinedRelationshipEdge(
                    source=heading.parent_id or source_id,
                    target=heading_target_id,
                    relationship_type="heading",
                    relationship_label="",
                ),
            )
    for edge in graph.edges:
        if edge.source not in source_document_ids and edge.target not in source_document_ids:
            continue
        source_id = edge.source if edge.source in source_document_ids else edge.target
        adjacent_id = edge.target if edge.source in source_document_ids else edge.source
        adjacent = graph.characters.get(adjacent_id)
        if adjacent is None or adjacent.node_type not in {"character", "place", "group", "artifact"}:
            continue
        if adjacent.node_type in SEMANTIC_LORE_NODE_TYPES:
            root_lore_ids.add(adjacent_id)
        heading = markdown_subheading_for_edge(
            graph.characters[source_id],
            source_headings.get(source_id, []),
            edge,
            adjacent,
        )
        connected_ids.add(adjacent_id)
        edge_source = heading.id if heading is not None else source_id
        if heading is not None:
            edge_source = semantic_entity_id_by_heading_id.get(heading.id, edge_source)
        if adjacent.node_type == "character" and heading is not None:
            edge_source = (
                semantic_entity_id_by_heading_id.get(heading.id)
                or nearest_semantic_heading_id(heading, projected_nodes, source_headings.get(source_id, []))
                or edge_source
            )
        if edge_source == adjacent_id:
            continue
        relationship_label = edge.relationship_label if adjacent.node_type in {"character", "place", "artifact"} else ""
        if (
            heading is not None
            and heading.id in semantic_entity_id_by_heading_id
            and heading.level in (hidden_heading_levels or set())
        ):
            relationship_label = semantic_heading_display_name(heading.text)
        append_projected_edge(
            projected_edges,
            projected_lore_context_edge(
                source=edge_source,
                target=adjacent_id,
                nodes={**graph.characters, **projected_nodes},
                relationship_type=edge.relationship_type,
                relationship_label=relationship_label,
                evidence=list(edge.evidence),
                bidirectional=edge.bidirectional,
            ),
        )
    if fanout_linked_characters:
        append_linked_character_fanout(
            graph,
            root_ids=root_lore_ids,
            connected_ids=connected_ids,
            projected_edges=projected_edges,
        )
    projected_edges = prune_unassociated_markdown_headings(
        connected_ids,
        projected_nodes,
        projected_edges,
        graph.characters,
    )
    projected_edges = prune_unassociated_semantic_heading_entities(
        connected_ids,
        set(semantic_entity_id_by_heading_id.values()),
        projected_edges,
        graph.characters,
        projected_nodes,
    )
    projected_graph = CombinedCharacterGraph(
        characters={
            **{
                node_id: node
                for node_id, node in graph.characters.items()
                if node_id in connected_ids and node.node_type in {"source_document", "note", "group", "place", "artifact", "character"}
            },
            **projected_nodes,
        },
        edges=[
            edge
            for edge in projected_edges
            if edge.source in connected_ids and edge.target in connected_ids
        ],
    )
    if hide_source_document_roots:
        projected_graph = graph_without_source_document_roots(projected_graph)
    if heading_id is not None:
        projected_graph = filter_lore_graph_by_heading(projected_graph, heading_id)
    projected_graph = graph_without_markdown_heading_levels(projected_graph, hidden_heading_levels or set())
    return graph_without_markdown_heading_nodes(projected_graph, hidden_heading_ids or set())


def graph_without_source_document_roots(graph: CombinedCharacterGraph) -> CombinedCharacterGraph:
    hidden_ids = {
        node_id
        for node_id, node in graph.characters.items()
        if is_lore_source_node(node)
    }
    visible_characters = {
        node_id: node
        for node_id, node in graph.characters.items()
        if node_id not in hidden_ids
    }
    replacement_edges = [
        edge
        for edge in graph.edges
        if edge.source in visible_characters and edge.target in visible_characters
    ]
    for hidden_id in sorted(hidden_ids, key=lambda item: graph.characters[item].name.lower()):
        hidden_node = graph.characters[hidden_id]
        visible_parents = visible_boundary_nodes(
            graph,
            hidden_id,
            hidden_ids,
            direction="incoming",
        )
        visible_children = visible_boundary_nodes(
            graph,
            hidden_id,
            hidden_ids,
            direction="outgoing",
        )
        for parent_id in visible_parents:
            for child_id in visible_children:
                if parent_id == child_id:
                    continue
                append_projected_edge(
                    replacement_edges,
                    CombinedRelationshipEdge(
                        source=parent_id,
                        target=child_id,
                        relationship_type="source",
                        relationship_label=hidden_node.name,
                    ),
                )
    return CombinedCharacterGraph(
        characters=visible_characters,
        edges=[
            edge
            for edge in replacement_edges
            if edge.source in visible_characters and edge.target in visible_characters
        ],
    )


def graph_without_markdown_heading_levels(
    graph: CombinedCharacterGraph,
    hidden_levels: set[int],
) -> CombinedCharacterGraph:
    hidden_heading_ids = {
        node_id
        for node_id, node in graph.characters.items()
        if (markdown_heading_level(node) or 0) in hidden_levels
    }
    return graph_without_markdown_heading_nodes(graph, hidden_heading_ids)


def graph_without_markdown_heading_nodes(
    graph: CombinedCharacterGraph,
    hidden_heading_ids: set[str],
) -> CombinedCharacterGraph:
    hidden_heading_ids = {
        node_id
        for node_id in hidden_heading_ids
        if is_markdown_heading_node(graph.characters.get(node_id))
    }
    if not hidden_heading_ids:
        return graph
    visible_nodes = {
        node_id: node
        for node_id, node in graph.characters.items()
        if node_id not in hidden_heading_ids
    }
    replacement_edges = [
        edge
        for edge in graph.edges
        if edge.source in visible_nodes and edge.target in visible_nodes
    ]
    for heading_id in sorted(hidden_heading_ids, key=lambda item: graph.characters[item].name.lower()):
        heading = graph.characters[heading_id]
        visible_parents = visible_markdown_boundary_nodes(
            graph,
            heading_id,
            hidden_heading_ids,
            direction="incoming",
        )
        visible_children = visible_markdown_boundary_nodes(
            graph,
            heading_id,
            hidden_heading_ids,
            direction="outgoing",
        )
        visible_children.extend(visible_markdown_descendant_headings(graph, heading_id, visible_nodes))
        visible_children = list(dict.fromkeys(visible_children))
        for parent_id in visible_parents:
            for child_id in visible_children:
                if parent_id == child_id:
                    continue
                append_projected_edge(
                    replacement_edges,
                    projected_lore_context_edge(
                        source=parent_id,
                        target=child_id,
                        nodes=visible_nodes,
                        relationship_type="heading",
                        relationship_label=hidden_heading_bridge_label(heading, visible_nodes.get(child_id)),
                        evidence=hidden_heading_bridge_evidence(graph, heading_id, hidden_heading_ids, parent_id, child_id),
                    ),
                )
        contextual_children = direct_visible_non_heading_children(graph, heading_id, visible_nodes)
        for source_id, target_id in contextual_heading_child_pairs(visible_nodes, contextual_children):
            append_projected_edge(
                replacement_edges,
                CombinedRelationshipEdge(
                    source=source_id,
                    target=target_id,
                    relationship_type="context",
                    relationship_label=hidden_heading_bridge_label(
                        heading,
                        semantic_hidden_heading_bridge_node(heading, visible_nodes.get(source_id), visible_nodes.get(target_id)),
                    ),
                    evidence=hidden_heading_bridge_evidence(graph, heading_id, hidden_heading_ids, source_id, target_id),
                ),
            )
    visible_edges = [
        edge
        for edge in replacement_edges
        if edge.source in visible_nodes and edge.target in visible_nodes and edge.source != edge.target
    ]
    connected_ids = node_ids_in_edges(visible_edges)
    return CombinedCharacterGraph(
        characters={
            node_id: node
            for node_id, node in visible_nodes.items()
            if node_id in connected_ids
        },
        edges=visible_edges,
    )


def hidden_heading_bridge_label(
    heading: CombinedCharacterNode,
    visible_node: CombinedCharacterNode | None,
) -> str:
    if (
        visible_node is not None
        and semantic_heading_entity_type(heading) == visible_node.node_type
        and compact(heading.name) == compact(visible_node.name)
    ):
        return ""
    return heading.name


def semantic_hidden_heading_bridge_node(
    heading: CombinedCharacterNode,
    source: CombinedCharacterNode | None,
    target: CombinedCharacterNode | None,
) -> CombinedCharacterNode | None:
    semantic_type = semantic_heading_entity_type(heading)
    for node in (source, target):
        if node is not None and node.node_type == semantic_type and compact(node.name) == compact(heading.name):
            return node
    return None


def visible_markdown_boundary_nodes(
    graph: CombinedCharacterGraph,
    heading_id: str,
    hidden_heading_ids: set[str],
    *,
    direction: str,
) -> list[str]:
    return visible_boundary_nodes(
        graph,
        heading_id,
        hidden_heading_ids,
        direction=direction,
    )


def visible_markdown_descendant_headings(
    graph: CombinedCharacterGraph,
    heading_id: str,
    visible_nodes: dict[str, CombinedCharacterNode],
) -> list[str]:
    descendants: list[str] = []
    pending = [heading_id]
    visited = {heading_id}
    while pending:
        current_id = pending.pop(0)
        for edge in graph.edges:
            if edge.relationship_type != "heading" or edge.source != current_id or edge.target in visited:
                continue
            visited.add(edge.target)
            target = graph.characters.get(edge.target)
            if not is_markdown_heading_node(target):
                continue
            if edge.target in visible_nodes:
                descendants.append(edge.target)
            pending.append(edge.target)
    return list(dict.fromkeys(descendants))


def visible_boundary_nodes(
    graph: CombinedCharacterGraph,
    hidden_id: str,
    hidden_ids: set[str],
    *,
    direction: str,
) -> list[str]:
    pending = [hidden_id]
    visited = {hidden_id}
    boundary: list[str] = []
    while pending:
        current_id = pending.pop(0)
        for edge in graph.edges:
            next_id = ""
            if direction == "incoming" and edge.target == current_id:
                next_id = edge.source
            elif direction == "outgoing" and edge.source == current_id:
                next_id = edge.target
            if not next_id or next_id in visited:
                continue
            visited.add(next_id)
            if next_id in hidden_ids:
                pending.append(next_id)
            else:
                boundary.append(next_id)
    return list(dict.fromkeys(boundary))


def direct_visible_non_heading_children(
    graph: CombinedCharacterGraph,
    heading_id: str,
    visible_nodes: dict[str, CombinedCharacterNode],
) -> list[str]:
    children: list[str] = []
    children.extend(semantic_visible_nodes_for_hidden_heading(graph, heading_id, visible_nodes))
    for edge in graph.edges:
        if edge.source != heading_id or edge.target not in visible_nodes:
            continue
        if is_markdown_heading_node(visible_nodes.get(edge.target)):
            continue
        children.append(edge.target)
    return list(dict.fromkeys(children))


def semantic_visible_nodes_for_hidden_heading(
    graph: CombinedCharacterGraph,
    heading_id: str,
    visible_nodes: dict[str, CombinedCharacterNode],
) -> list[str]:
    heading = graph.characters.get(heading_id)
    semantic_type = semantic_heading_entity_type(heading)
    if heading is None or semantic_type is None:
        return []
    heading_key = compact(heading.name)
    return [
        node_id
        for node_id, node in visible_nodes.items()
        if node.node_type == semantic_type and compact(node.name) == heading_key
    ]


def hidden_heading_bridge_evidence(
    graph: CombinedCharacterGraph,
    heading_id: str,
    hidden_heading_ids: set[str],
    parent_id: str,
    child_id: str,
) -> list[str]:
    context_ids = hidden_heading_subtree_ids(graph, heading_id, hidden_heading_ids)
    relevant_ids = {*context_ids, parent_id, child_id}
    evidence: list[str] = []
    for edge in graph.edges:
        if edge.source not in relevant_ids or edge.target not in relevant_ids:
            continue
        if not ({edge.source, edge.target} & context_ids):
            continue
        for item in edge.evidence:
            if item and item not in evidence:
                evidence.append(item)
    return evidence


def hidden_heading_subtree_ids(
    graph: CombinedCharacterGraph,
    heading_id: str,
    hidden_heading_ids: set[str],
) -> set[str]:
    subtree = {heading_id}
    pending = [heading_id]
    while pending:
        current_id = pending.pop(0)
        for edge in graph.edges:
            if edge.relationship_type != "heading" or edge.source != current_id:
                continue
            if edge.target not in hidden_heading_ids or edge.target in subtree:
                continue
            subtree.add(edge.target)
            pending.append(edge.target)
    return subtree


def contextual_heading_child_pairs(
    nodes: dict[str, CombinedCharacterNode],
    child_ids: list[str],
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for source_id in child_ids:
        source = nodes.get(source_id)
        if source is None or source.node_type not in SEMANTIC_LORE_NODE_TYPES:
            continue
        for target_id in child_ids:
            target = nodes.get(target_id)
            if (
                target_id == source_id
                or target is None
                or target.node_type not in {"character", "place", "group", "artifact", "family"}
            ):
                continue
            pairs.append(lore_context_edge_direction(source_id, target_id, nodes))
    if pairs:
        return pairs
    for source_id in child_ids:
        source = nodes.get(source_id)
        if source is None or source.node_type != "character":
            continue
        for target_id in child_ids:
            target = nodes.get(target_id)
            if target_id == source_id or target is None or target.node_type != "character":
                continue
            pairs.append((source_id, target_id))
    return pairs


def deduplicate_source_document_nodes(graph: CombinedCharacterGraph) -> None:
    remapped_ids: dict[str, str] = {}
    canonical_by_key: dict[tuple[str, str, str], str] = {}
    for node_id, node in list(graph.characters.items()):
        if node.node_type != "source_document":
            continue
        key = (
            node.node_type,
            compact(node.name),
            normalized_lore_source_file(node.source_file),
        )
        canonical_id = canonical_by_key.setdefault(key, node_id)
        if canonical_id != node_id:
            remapped_ids[node_id] = canonical_id
    if not remapped_ids:
        return
    graph.characters = {
        node_id: node
        for node_id, node in graph.characters.items()
        if node_id not in remapped_ids
    }
    for edge in graph.edges:
        edge.source = remapped_ids.get(edge.source, edge.source)
        edge.target = remapped_ids.get(edge.target, edge.target)
    dedupe_combined_edges(graph)


def markdown_heading_level(node: CombinedCharacterNode | None) -> int | None:
    if node is None:
        return None
    if node.is_heading:
        return node.heading_level or 1
    match = re.fullmatch(r"source_heading(?:_(?:place|group|artifact))?_(?P<level>\d+)", node.node_type)
    return int(match.group("level")) if match else None


def append_linked_character_fanout(
    graph: CombinedCharacterGraph,
    *,
    root_ids: set[str],
    connected_ids: set[str],
    projected_edges: list[CombinedRelationshipEdge],
    include_character: Callable[[CombinedCharacterNode], bool] | None = None,
) -> None:
    if not root_ids:
        return
    for edge in graph.edges:
        if edge.source not in root_ids and edge.target not in root_ids:
            continue
        root_id = edge.source if edge.source in root_ids else edge.target
        adjacent_id = edge.target if edge.source in root_ids else edge.source
        adjacent = graph.characters.get(adjacent_id)
        if adjacent is None or adjacent.node_type != "character":
            continue
        if include_character is not None and not include_character(adjacent):
            continue
        connected_ids.update({root_id, adjacent_id})
        append_projected_edge(
            projected_edges,
            projected_lore_context_edge(
                source=root_id,
                target=adjacent_id,
                nodes=graph.characters,
                relationship_type=edge.relationship_type,
                relationship_label=edge.relationship_label,
                evidence=list(edge.evidence),
                bidirectional=edge.bidirectional,
            ),
        )


def projected_lore_context_edge(
    *,
    source: str,
    target: str,
    nodes: dict[str, CombinedCharacterNode],
    relationship_type: str,
    relationship_label: str,
    evidence: list[str] | None = None,
    bidirectional: bool = False,
) -> CombinedRelationshipEdge:
    directed_source, directed_target = lore_context_edge_direction(source, target, nodes)
    return CombinedRelationshipEdge(
        source=directed_source,
        target=directed_target,
        relationship_type=relationship_type,
        relationship_label=relationship_label,
        evidence=evidence or [],
        bidirectional=bidirectional,
    )


def lore_context_edge_direction(
    source: str,
    target: str,
    nodes: dict[str, CombinedCharacterNode],
) -> tuple[str, str]:
    source_node = nodes.get(source)
    target_node = nodes.get(target)
    if source_node is not None and target_node is not None:
        if source_node.node_type in SEMANTIC_LORE_NODE_TYPES and target_node.node_type == "character":
            return target, source
    return source, target


def filter_lore_graph_by_heading(graph: CombinedCharacterGraph, heading_id: str) -> CombinedCharacterGraph:
    if heading_id not in graph.characters:
        return CombinedCharacterGraph()
    heading_ids = {
        node_id
        for node_id, node in graph.characters.items()
        if is_markdown_heading_node(node)
    }
    content_heading_ids = {heading_id}
    changed = True
    while changed:
        changed = False
        for edge in graph.edges:
            if edge.relationship_type == "heading" and edge.source in content_heading_ids and edge.target in heading_ids:
                if edge.target not in content_heading_ids:
                    content_heading_ids.add(edge.target)
                    changed = True
    kept_ids = set(content_heading_ids)
    changed = True
    while changed:
        changed = False
        for edge in graph.edges:
            if edge.relationship_type == "heading" and edge.target in kept_ids:
                if edge.source not in kept_ids:
                    kept_ids.add(edge.source)
                    changed = True
    for edge in graph.edges:
        if edge.source in content_heading_ids and edge.target not in heading_ids:
            kept_ids.add(edge.target)
        if edge.target in content_heading_ids and edge.source not in heading_ids:
            kept_ids.add(edge.source)
    return CombinedCharacterGraph(
        characters={
            node_id: node
            for node_id, node in graph.characters.items()
            if node_id in kept_ids
        },
        edges=[
            edge
            for edge in graph.edges
            if edge.source in kept_ids and edge.target in kept_ids
        ],
    )


def filter_source_document_ids_by_file(
    graph: CombinedCharacterGraph,
    source_document_ids: set[str],
    source_file: str,
) -> set[str]:
    normalized_source_file = normalized_lore_source_file(source_file)
    return {
        source_id
        for source_id in source_document_ids
        if normalized_lore_source_file(graph.characters[source_id].source_file) == normalized_source_file
    }


def normalized_lore_source_file(source_file: str) -> str:
    return source_file.replace("\\", "/")


def markdown_subheadings_by_source(
    graph: CombinedCharacterGraph,
    source_ids: set[str],
) -> dict[str, list[MarkdownSubheading]]:
    return {
        source_id: markdown_subheadings_for_source(graph.characters[source_id])
        for source_id in sorted(source_ids)
        if source_id in graph.characters
    }


def markdown_subheadings_for_source(source: CombinedCharacterNode) -> list[MarkdownSubheading]:
    source_path = Path(source.source_file)
    if not source_path.exists():
        return []
    try:
        lines = read_markdown(source_path).splitlines()
    except OSError:
        return []
    headings: list[MarkdownSubheading] = []
    for line_index, line in enumerate(lines):
        match = PLACE_GRAPH_MARKDOWN_HEADING_RE.match(line.strip())
        if match is None:
            continue
        text = match.group("text").strip()
        if not text:
            continue
        level = len(match.group("marker"))
        heading_id = source_heading_node_id(source.id, line_index, text)
        headings.append(
            MarkdownSubheading(
                id=heading_id,
                text=text,
                level=level,
                line_index=line_index,
                parent_id=markdown_heading_parent_id(source.id, headings, level),
            )
        )
    return headings


def markdown_heading_parent_id(
    source_id: str,
    previous_headings: list[MarkdownSubheading],
    level: int,
) -> str:
    for heading in reversed(previous_headings):
        if heading.level < level:
            return heading.id
    return source_id


def markdown_subheading_for_edge(
    source: CombinedCharacterNode,
    headings: list[MarkdownSubheading],
    edge: CombinedRelationshipEdge,
    target: CombinedCharacterNode | None,
) -> MarkdownSubheading | None:
    if not headings:
        return None
    line_index = source_line_index_for_edge(source, edge, target)
    if line_index is not None:
        preceding = [heading for heading in headings if heading.line_index <= line_index]
        if preceding:
            return preceding[-1]
    if target is not None:
        target_key = compact(target.name)
        for heading in headings:
            if compact(heading.text) == target_key:
                return heading
    return headings[0]


def source_line_index_for_edge(
    source: CombinedCharacterNode,
    edge: CombinedRelationshipEdge,
    target: CombinedCharacterNode | None,
) -> int | None:
    source_path = Path(source.source_file)
    if not source_path.exists():
        return None
    try:
        lines = read_markdown(source_path).splitlines()
    except OSError:
        return None
    snippets = [item.strip() for item in edge.evidence if item.strip()]
    if target is not None:
        snippets.append(target.name)
    for snippet in snippets:
        line_index = line_index_for_snippet(lines, snippet)
        if line_index is not None:
            return line_index
    return None


def line_index_for_snippet(lines: list[str], snippet: str) -> int | None:
    normalized_snippet = " ".join(snippet.split())
    for index, line in enumerate(lines):
        if snippet in line or normalized_snippet in " ".join(line.split()):
            return index
    source_text = "\n".join(lines)
    position = source_text.find(snippet)
    if position < 0:
        return None
    return source_text[:position].count("\n")


def source_heading_node_id(source_id: str, line_index: int, text: str) -> str:
    return f"source_heading__{compact(source_id)}__line_{line_index + 1}__{compact(text or 'heading')}"


def markdown_heading_node_type(level: int, semantic_type: str | None = None) -> str:
    if semantic_type in SEMANTIC_LORE_NODE_TYPES:
        return f"source_heading_{semantic_type}_{level}"
    return f"source_heading_{level}"


def markdown_heading_entity_type(text: str, graph: CombinedCharacterGraph) -> str | None:
    display_name = semantic_heading_display_name(text)
    display_key = compact(display_name)
    for node in graph.characters.values():
        if (
            not node.is_source
            and compact(node.name) == display_key
            and node.node_type in SEMANTIC_LORE_NODE_TYPES
        ):
            return node.node_type
    if looks_like_artifact_heading(display_name):
        return "artifact"
    if looks_like_group_heading(display_name):
        return "group"
    if looks_like_place_heading(display_name):
        return "place"
    return None


def matching_semantic_entity_id(
    graph: CombinedCharacterGraph,
    display_name: str,
    semantic_type: str | None,
    source_file: str,
) -> str | None:
    if semantic_type not in SEMANTIC_LORE_NODE_TYPES:
        return None
    display_key = compact(display_name)
    matches = [
        node_id
        for node_id, node in graph.characters.items()
        if node.node_type == semantic_type and compact(node.name) == display_key
    ]
    if not matches:
        return None
    normalized_source = normalized_lore_source_file(source_file)
    for node_id in matches:
        if normalized_lore_source_file(graph.characters[node_id].source_file) == normalized_source:
            return node_id
    return sorted(matches)[0]


def semantic_heading_display_name(text: str) -> str:
    return re.sub(r"^(?:the|a|an)\s+", "", text.strip(), flags=re.IGNORECASE).strip()


def looks_like_place_heading(text: str) -> bool:
    words = text.split()
    if not words:
        return False
    lowered = text.lower()
    return any(
        lowered == suffix.lower() or lowered.endswith(f" {suffix.lower()}")
        for suffix in PLACE_HEADING_SUFFIXES
    )


def looks_like_group_heading(text: str) -> bool:
    lowered = text.lower()
    return any(
        lowered == suffix.lower() or lowered.endswith(f" {suffix.lower()}")
        for suffix in GROUP_HEADING_SUFFIXES
    )


def looks_like_artifact_heading(text: str) -> bool:
    lowered = text.lower()
    return any(
        lowered == suffix.lower() or lowered.endswith(f" {suffix.lower()}")
        for suffix in ARTIFACT_HEADING_SUFFIXES
    )


def semantic_heading_for_node(
    node: CombinedCharacterNode | None,
    heading: MarkdownSubheading | None,
    projected_nodes: dict[str, CombinedCharacterNode],
) -> str | None:
    if node is None or heading is None:
        return None
    heading_node = projected_nodes.get(heading.id)
    if heading_node is None:
        return None
    if semantic_heading_entity_type(heading_node) != node.node_type:
        return None
    if compact(heading_node.name) != compact(node.name):
        return None
    return heading_node.id


def nearest_semantic_heading_id(
    heading: MarkdownSubheading,
    projected_nodes: dict[str, CombinedCharacterNode],
    headings: list[MarkdownSubheading],
) -> str | None:
    heading_by_id = {item.id: item for item in headings}
    current_id = heading.id
    while current_id:
        node = projected_nodes.get(current_id)
        if semantic_heading_entity_type(node) in SEMANTIC_LORE_NODE_TYPES:
            return current_id
        current_heading = heading_by_id.get(current_id)
        current_id = current_heading.parent_id if current_heading is not None else ""
    return None


def semantic_heading_entity_type(node: CombinedCharacterNode | None) -> str | None:
    if node is None:
        return None
    if node.is_heading:
        return node.node_type if node.node_type in SEMANTIC_LORE_NODE_TYPES else None
    match = re.fullmatch(r"source_heading_(?P<entity>place|group|artifact)_\d+", node.node_type)
    return match.group("entity") if match else None


def append_place_heading_root_edges(
    graph: CombinedCharacterGraph,
    projected_nodes: dict[str, CombinedCharacterNode],
    source_to_place_ids: dict[str, set[str]],
    semantic_heading_ids_by_source: dict[str, set[str]],
    connected_ids: set[str],
    projected_edges: list[CombinedRelationshipEdge],
) -> None:
    for source_id, heading_ids in semantic_heading_ids_by_source.items():
        root_place_ids = {
            place_id
            for place_id in source_to_place_ids.get(source_id, set())
            if graph.characters.get(place_id) is not None
            and is_source_root_place(graph.characters[place_id], graph.characters.get(source_id))
        }
        for root_place_id in root_place_ids:
            root_place = graph.characters[root_place_id]
            for heading_id in heading_ids:
                heading_node = projected_nodes.get(heading_id)
                if heading_node is None or semantic_heading_entity_type(heading_node) != "place":
                    continue
                if compact(root_place.name) == compact(heading_node.name):
                    continue
                connected_ids.update({root_place_id, heading_id})
                append_projected_edge(
                    projected_edges,
                    CombinedRelationshipEdge(
                        source=root_place_id,
                        target=heading_id,
                        relationship_type="contains",
                        relationship_label="Contains",
                    ),
                )


def semantic_heading_by_original_entity_id(
    graph: CombinedCharacterGraph,
    projected_nodes: dict[str, CombinedCharacterNode],
) -> dict[str, str]:
    heading_ids_by_key: dict[tuple[str, str], list[str]] = {}
    for heading_id, heading in projected_nodes.items():
        if semantic_heading_entity_type(heading) not in SEMANTIC_LORE_NODE_TYPES:
            continue
        heading_ids_by_key.setdefault((heading.node_type, compact(heading.name)), []).append(heading_id)
    mapped: dict[str, str] = {}
    for entity_id, entity in graph.characters.items():
        if entity.is_source or entity.node_type not in SEMANTIC_LORE_NODE_TYPES:
            continue
        heading_ids = heading_ids_by_key.get((entity.node_type, compact(entity.name)), [])
        if not heading_ids:
            continue
        entity_source = normalized_lore_source_file(entity.source_file)
        same_source_heading_ids = [
            heading_id
            for heading_id in heading_ids
            if normalized_lore_source_file(projected_nodes[heading_id].source_file) == entity_source
        ]
        mapped[entity_id] = sorted(same_source_heading_ids or heading_ids)[0]
    return mapped


def retarget_semantic_heading_edges(
    edges: list[CombinedRelationshipEdge],
    semantic_heading_by_entity_id_map: dict[str, str],
) -> list[CombinedRelationshipEdge]:
    retargeted: list[CombinedRelationshipEdge] = []
    for edge in edges:
        source = semantic_heading_by_entity_id_map.get(edge.source, edge.source)
        target = semantic_heading_by_entity_id_map.get(edge.target, edge.target)
        if source == target:
            continue
        append_projected_edge(
            retargeted,
            CombinedRelationshipEdge(
                source=source,
                target=target,
                relationship_type=edge.relationship_type,
                relationship_label=edge.relationship_label,
                evidence=list(edge.evidence),
                bidirectional=edge.bidirectional,
            ),
        )
    return retargeted


def has_non_heading_edge_to(edges: list[CombinedRelationshipEdge], target_id: str) -> bool:
    return any(edge.target == target_id and edge.relationship_type != "heading" for edge in edges)


def is_source_root_place(place: CombinedCharacterNode, source: CombinedCharacterNode | None) -> bool:
    if source is None:
        return False
    source_stem = compact(Path(source.source_file).stem)
    source_name = compact(source.name)
    place_name = compact(place.name)
    return bool(place_name and (place_name in source_stem or place_name in source_name))


def node_ids_in_edges(edges: list[CombinedRelationshipEdge]) -> set[str]:
    return {edge.source for edge in edges} | {edge.target for edge in edges}


def place_lore_connection_rows(graph: CombinedCharacterGraph) -> list[dict[str, str]]:
    character_connection_graph = CombinedCharacterGraph(
        characters=graph.characters,
        edges=[
            edge
            for edge in graph.edges
            if edge_has_character_connection(edge, graph)
        ],
    )
    return combined_relationship_rows(character_connection_graph)


def lore_graph_connection_rows(graph: CombinedCharacterGraph) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for edge in graph.edges:
        source = graph.characters.get(edge.source)
        target = graph.characters.get(edge.target)
        subject, connection = relationship_row_subject_and_connection(source, target)
        if subject is None or connection is None:
            continue
        for evidence in edge.evidence:
            compacted_evidence = clean_evidence_text(evidence)
            if not compacted_evidence:
                continue
            rows.append(
                {
                    "Character": subject.name,
                    "Relationship": edge.relationship_label,
                    "Connection": connection.name,
                    "Connection Type": connection_type_label(connection),
                    "Evidence": compacted_evidence,
                }
            )
    return rows


def relationship_row_subject_and_connection(
    source: CombinedCharacterNode | None,
    target: CombinedCharacterNode | None,
) -> tuple[CombinedCharacterNode | None, CombinedCharacterNode | None]:
    if source is None or target is None:
        return None, None
    source_structural = is_lore_source_node(source) or is_markdown_heading_node(source)
    target_structural = is_lore_source_node(target) or is_markdown_heading_node(target)
    if source_structural and target_structural:
        return None, None
    if source_structural:
        return target, source
    if target_structural:
        return source, target
    if source.node_type == "character":
        return source, target
    if target.node_type == "character":
        return target, source
    return source, target


def connection_type_label(node: CombinedCharacterNode) -> str:
    if is_lore_source_node(node):
        return "Source"
    if is_markdown_heading_node(node):
        return "Section"
    return node.node_type.title()


def lore_information_rows(graph: CombinedCharacterGraph) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    source_nodes = [
        node
        for node in graph.characters.values()
        if node.node_type == "source_document"
    ]
    for source in sorted(source_nodes, key=lambda node: node.name.lower()):
        for heading, description in descriptive_heading_summaries(source, graph):
            rows.append(
                {
                    "Source": Path(source.source_file).name or source.name,
                    "Heading": heading,
                    "Summary": description,
                }
            )
    return rows


def descriptive_heading_summaries(
    source: CombinedCharacterNode,
    graph: CombinedCharacterGraph,
) -> list[tuple[str, str]]:
    source_path = Path(source.source_file)
    if not source_path.exists():
        return []
    try:
        lines = read_markdown(source_path).splitlines()
    except OSError:
        return []
    headings = markdown_subheadings_for_source(source)
    rows: list[tuple[str, str]] = []
    for index, heading in enumerate(headings):
        if heading.level <= 1:
            continue
        if markdown_heading_entity_type(heading.text, graph) is not None:
            continue
        next_line_index = headings[index + 1].line_index if index + 1 < len(headings) else len(lines)
        description = first_human_sentence(lines[heading.line_index + 1 : next_line_index])
        if description:
            rows.append((heading.text, description))
    return rows


def first_human_sentence(lines: list[str]) -> str:
    text = " ".join(
        line.strip()
        for line in lines
        if line.strip()
        and not line.lstrip().startswith("|")
        and not re.fullmatch(r":?-{2,}:?(?:\s+\|+\s*:?-{2,}:?)*", line.strip())
    )
    if not text:
        return ""
    match = re.search(r"(.+?[.!?])(?:\s|$)", text)
    sentence = match.group(1) if match else text
    return clean_evidence_text(sentence)


def edge_has_character_connection(edge: CombinedRelationshipEdge, graph: CombinedCharacterGraph) -> bool:
    source = graph.characters.get(edge.source)
    target = graph.characters.get(edge.target)
    return source is not None and target is not None and (
        source.node_type == "character" or target.node_type == "character"
    )


def is_markdown_heading_node(node: CombinedCharacterNode | None) -> bool:
    return is_heading_node(node)


def prune_unassociated_markdown_headings(
    connected_ids: set[str],
    projected_nodes: dict[str, CombinedCharacterNode],
    projected_edges: list[CombinedRelationshipEdge],
    original_nodes: dict[str, CombinedCharacterNode],
) -> list[CombinedRelationshipEdge]:
    heading_ids = {
        node_id
        for node_id, node in projected_nodes.items()
        if is_markdown_heading_node(node)
    }
    if not heading_ids:
        return projected_edges
    parent_by_heading: dict[str, str] = {}
    associated_heading_ids: set[str] = set()
    all_nodes = {**original_nodes, **projected_nodes}
    for edge in projected_edges:
        if edge.relationship_type == "heading" and edge.target in heading_ids:
            parent_by_heading[edge.target] = edge.source
        source_is_heading = edge.source in heading_ids
        target_is_heading = edge.target in heading_ids
        if source_is_heading == target_is_heading:
            continue
        adjacent_id = edge.target if source_is_heading else edge.source
        adjacent = all_nodes.get(adjacent_id)
        if adjacent is None or adjacent.node_type == "source_document":
            continue
        associated_heading_ids.add(edge.source if source_is_heading else edge.target)
    kept_heading_ids = set(associated_heading_ids)
    pending = list(associated_heading_ids)
    while pending:
        heading_id = pending.pop()
        parent_id = parent_by_heading.get(heading_id)
        if parent_id in heading_ids and parent_id not in kept_heading_ids:
            kept_heading_ids.add(parent_id)
            pending.append(parent_id)
    removed_heading_ids = heading_ids - kept_heading_ids
    for heading_id in removed_heading_ids:
        connected_ids.discard(heading_id)
        projected_nodes.pop(heading_id, None)
    return [
        edge
        for edge in projected_edges
        if edge.source not in removed_heading_ids and edge.target not in removed_heading_ids
    ]


def prune_unassociated_semantic_heading_entities(
    connected_ids: set[str],
    semantic_entity_ids: set[str],
    projected_edges: list[CombinedRelationshipEdge],
    original_nodes: dict[str, CombinedCharacterNode],
    projected_nodes: dict[str, CombinedCharacterNode],
) -> list[CombinedRelationshipEdge]:
    if not semantic_entity_ids:
        return projected_edges
    all_nodes = {**original_nodes, **projected_nodes}
    associated_entity_ids: set[str] = set()
    for edge in projected_edges:
        for entity_id, adjacent_id in ((edge.source, edge.target), (edge.target, edge.source)):
            if entity_id not in semantic_entity_ids:
                continue
            adjacent = all_nodes.get(adjacent_id)
            if adjacent is not None and adjacent.node_type in {"character", "place", "artifact"}:
                associated_entity_ids.add(entity_id)
    removed_entity_ids = semantic_entity_ids - associated_entity_ids
    for entity_id in removed_entity_ids:
        connected_ids.discard(entity_id)
    return [
        edge
        for edge in projected_edges
        if edge.source not in removed_entity_ids and edge.target not in removed_entity_ids
    ]


def append_projected_edge(edges: list[CombinedRelationshipEdge], edge: CombinedRelationshipEdge) -> None:
    key = (
        edge.source,
        edge.target,
        edge.relationship_type,
        edge.relationship_label,
    )
    for existing in edges:
        existing_key = (
            existing.source,
            existing.target,
            existing.relationship_type,
            existing.relationship_label,
        )
        if existing_key != key:
            continue
        for evidence in edge.evidence:
            if evidence and evidence not in existing.evidence:
                existing.evidence.append(evidence)
        return
    edges.append(edge)


def is_disallowed_place_graph_character(node: CombinedCharacterNode) -> bool:
    return compact(node.id) in DISALLOWED_PLACE_GRAPH_CHARACTER_KEYS or compact(node.name) in DISALLOWED_PLACE_GRAPH_CHARACTER_KEYS


def edge_source_ids_for_place(
    edge: CombinedRelationshipEdge,
    graph: CombinedCharacterGraph,
    place_ids: set[str],
) -> set[str]:
    if edge.source in place_ids and edge.target in graph.characters:
        return {edge.target}
    if edge.target in place_ids and edge.source in graph.characters:
        return {edge.source}
    return set()


def place_character_edge_from_place(
    edge: CombinedRelationshipEdge,
    graph: CombinedCharacterGraph,
    place_ids: set[str],
) -> CombinedRelationshipEdge:
    if edge.source in place_ids:
        place_id = edge.source
        character_id = edge.target
    elif edge.target in place_ids:
        place_id = edge.target
        character_id = edge.source
    else:
        return edge
    character = graph.characters.get(character_id)
    if character is None or character.node_type != "character":
        return edge
    return CombinedRelationshipEdge(
        source=place_id,
        target=character_id,
        relationship_type=edge.relationship_type,
        relationship_label=edge.relationship_label,
        evidence=list(edge.evidence),
        bidirectional=edge.bidirectional,
    )


def place_ids_by_source_document(
    graph: CombinedCharacterGraph,
    source_ids: set[str],
    place_ids: set[str],
) -> dict[str, set[str]]:
    source_to_place_ids: dict[str, set[str]] = {source_id: set() for source_id in source_ids}
    source_files = {
        source_id: graph.characters[source_id].source_file.replace("\\", "/")
        for source_id in source_ids
        if source_id in graph.characters
    }
    for source_id, source_file in source_files.items():
        for place_id in place_ids:
            place = graph.characters.get(place_id)
            if place is not None and place.source_file.replace("\\", "/") == source_file:
                source_to_place_ids[source_id].add(place_id)
    for edge in graph.edges:
        for source_id in source_ids:
            for place_id in place_ids:
                if edge_connects(edge, {source_id}, {place_id}):
                    source_to_place_ids[source_id].add(place_id)
    return source_to_place_ids


def session_note_graph(graph: CombinedCharacterGraph) -> CombinedCharacterGraph:
    return graph_for_sources(graph, is_session_note_node)


def graph_for_sources(
    graph: CombinedCharacterGraph,
    source_predicate: Callable[[CombinedCharacterNode], bool],
) -> CombinedCharacterGraph:
    source_ids = {
        node_id
        for node_id, node in graph.characters.items()
        if source_predicate(node)
    }
    if not source_ids:
        return CombinedCharacterGraph()
    visible_ids = set(source_ids)
    visible_edges = []
    for edge in graph.edges:
        if edge.source in source_ids or edge.target in source_ids:
            visible_edges.append(edge)
            visible_ids.update({edge.source, edge.target})
    return CombinedCharacterGraph(
        characters={
            node_id: node
            for node_id, node in graph.characters.items()
            if node_id in visible_ids and node.node_type in {"character", "place", "artifact", "source_document"}
        },
        edges=[
            edge
            for edge in visible_edges
            if edge.source in visible_ids and edge.target in visible_ids
        ],
    )


def graph_without_lore_source_knots(graph: CombinedCharacterGraph) -> CombinedCharacterGraph:
    visible_characters = {
        node_id: node
        for node_id, node in graph.characters.items()
        if not is_hidden_full_knowledge_source_node(node)
    }
    visible_edges = [
        edge
        for edge in graph.edges
        if edge.source in visible_characters and edge.target in visible_characters
    ]
    connected_ids = {edge.source for edge in visible_edges} | {edge.target for edge in visible_edges}
    return CombinedCharacterGraph(
        characters={
            node_id: node
            for node_id, node in visible_characters.items()
            if node_id in connected_ids
        },
        edges=visible_edges,
    )


def combined_graph_root_node_options(nodes: list[CombinedCharacterNode]) -> dict[str, str]:
    return {node.name: node.id for node in nodes}


def session_note_month_options(graph: CombinedCharacterGraph) -> list[str]:
    months = {
        session_note_month(node)
        for node in graph.characters.values()
        if is_session_note_node(node)
    }
    return ["All Months", *sorted(months)]


def filter_session_note_graph_by_month(graph: CombinedCharacterGraph, month: str) -> CombinedCharacterGraph:
    if month == "All Months":
        return graph
    source_ids = {
        node_id
        for node_id, node in graph.characters.items()
        if is_session_note_node(node) and session_note_month(node) == month
    }
    if not source_ids:
        return CombinedCharacterGraph()
    visible_ids = set(source_ids)
    visible_edges = []
    for edge in graph.edges:
        if edge.source in source_ids or edge.target in source_ids:
            visible_edges.append(edge)
            visible_ids.update({edge.source, edge.target})
    return CombinedCharacterGraph(
        characters={node_id: node for node_id, node in graph.characters.items() if node_id in visible_ids},
        edges=visible_edges,
    )


def session_note_month(node: CombinedCharacterNode) -> str:
    source_text = f"{node.source_file} {node.name}"
    match = re.search(r"(?P<year>20\d{2})[-_](?P<month>0[1-9]|1[0-2])", source_text)
    if match:
        return f"{match.group('year')}-{match.group('month')}"
    return "Undated"


def is_hidden_full_knowledge_source_node(node: CombinedCharacterNode | None) -> bool:
    if is_lore_source_node(node):
        return True
    if node is None or node.node_type != "place":
        return False
    source_file = node.source_file.replace("\\", "/")
    if not is_place_lore_path(Path(source_file)):
        return False
    return compact(node.name) == compact(Path(source_file).stem)


def is_place_lore_node(node: CombinedCharacterNode) -> bool:
    source_file = node.source_file.replace("\\", "/")
    return is_place_lore_path(Path(source_file)) or (is_lore_source_node(node) and "/places/" in source_file.lower())


def is_place_source_document_node(node: CombinedCharacterNode) -> bool:
    source_file = node.source_file.replace("\\", "/")
    return is_lore_source_node(node) and is_place_lore_path(Path(source_file))


def is_lore_projection_source_node(
    node: CombinedCharacterNode,
    source_predicate: Callable[[CombinedCharacterNode], bool],
) -> bool:
    return bool(node.source_file and is_lore_source_node(node) and source_predicate(node))


def edge_connects(edge, left_ids: set[str], right_ids: set[str]) -> bool:
    return (edge.source in left_ids and edge.target in right_ids) or (
        edge.target in left_ids and edge.source in right_ids
    )


def is_session_note_node(node: CombinedCharacterNode) -> bool:
    if is_lore_source_node(node) or node.node_type == "character":
        source_file = node.source_file.replace("\\", "/").lower()
        return (
            "/session_notes/" in source_file
            or source_file.endswith("/session_notes.md")
            or compact(Path(source_file).stem) in {"sessionnote", "sessionnotes"}
        )
    return is_session_notes_node(node)


def is_place_lore_path(path: Path) -> bool:
    return "places" in path.parts
