from src.graph.combined_graph import (
    CombinedCharacterGraph,
    CombinedCharacterNode,
    CombinedRelationshipEdge,
    combined_relationship_dot,
)
from src.rendering.graphviz_rendering import (
    PARTY_VIEW_TAB,
    PLACES_FILE_VIEW_TAB,
    SINGLE_CHARACTER_TAB,
    SESSION_FILE_VIEW_TAB,
    graph_without_lore_source_knots,
    graph_tab_names,
    lore_graph_view_definitions,
    place_lore_connection_rows,
    lore_graph_connection_rows,
    place_lore_graph,
    lore_information_rows,
    session_note_graph,
    markdown_header_lore_graph,
    graph_without_source_document_roots,
    graph_without_markdown_heading_levels,
    project_lore_graph_for_view,
    render_lore_graph,
    LoreGraphViewSelection,
)


def test_graph_tabs_follow_active_main_tab():
    expected_tabs = [SINGLE_CHARACTER_TAB, PARTY_VIEW_TAB, PLACES_FILE_VIEW_TAB, SESSION_FILE_VIEW_TAB]

    assert graph_tab_names("Characters") == expected_tabs
    assert graph_tab_names("Places") == expected_tabs
    assert graph_tab_names("Session Notes") == expected_tabs


def test_lore_view_definitions_standardize_source_and_heading_projection_contracts():
    place_views = lore_graph_view_definitions("Places")
    session_views = lore_graph_view_definitions("Session Notes", default_session_source_file="Session_Notes.md")

    assert set(place_views) == {PLACES_FILE_VIEW_TAB, SESSION_FILE_VIEW_TAB}
    assert set(session_views) == {PLACES_FILE_VIEW_TAB, SESSION_FILE_VIEW_TAB}
    assert place_views[PLACES_FILE_VIEW_TAB].view_name == PLACES_FILE_VIEW_TAB
    assert place_views[PLACES_FILE_VIEW_TAB].source_key == "location_view_source_file"
    assert place_views[PLACES_FILE_VIEW_TAB].heading_key == "location_view_heading"
    assert place_views[PLACES_FILE_VIEW_TAB].supports_heading_filter is True
    assert place_views[PLACES_FILE_VIEW_TAB].supports_directory_hide_options is True
    assert place_views[PLACES_FILE_VIEW_TAB].include_all_heading_option is True
    assert session_views[SESSION_FILE_VIEW_TAB].view_name == SESSION_FILE_VIEW_TAB
    assert session_views[SESSION_FILE_VIEW_TAB].source_key == "session_view_source_file"
    assert session_views[SESSION_FILE_VIEW_TAB].heading_key == "session_view_heading"
    assert session_views[SESSION_FILE_VIEW_TAB].default_source_file == "Session_Notes.md"
    assert session_views[SESSION_FILE_VIEW_TAB].supports_heading_filter is True
    assert session_views[SESSION_FILE_VIEW_TAB].supports_directory_hide_options is True


def test_heading_view_projection_applies_source_file_before_heading_filter(tmp_path):
    atlantia_path = tmp_path / "Atlantia_Lore.md"
    atlantia_path.write_text(
        "\n".join(
            [
                "# Atlantia Lore",
                "Atlantia is home to Jory Ravenmark.",
                "## Harbor",
                "Jory Ravenmark watched the tide from the Harbor.",
            ]
        ),
        encoding="utf-8",
    )
    family_path = tmp_path / "Family_Tree.md"
    family_path.write_text(
        "\n".join(
            [
                "# Family Tree",
                "Atlantia is listed beside Mrs Nightbloom.",
            ]
        ),
        encoding="utf-8",
    )
    graph = CombinedCharacterGraph(
        characters={
            "source_document__atlantia_lore": CombinedCharacterNode(
                id="source_document__atlantia_lore",
                name="Atlantia Lore",
                source_file=str(atlantia_path),
                node_type="source_document",
            ),
            "atlantia": CombinedCharacterNode(
                id="atlantia",
                name="Atlantia",
                source_file=str(atlantia_path),
                node_type="place",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
            "family_tree": CombinedCharacterNode(
                id="family_tree",
                name="Family Tree",
                source_file=str(family_path),
                node_type="source_document",
            ),
            "mrs_nightbloom": CombinedCharacterNode(
                id="mrs_nightbloom",
                name="Mrs Nightbloom",
                source_file="world_building/lore/session_notes/Family_Tree.md",
                node_type="character",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="atlantia",
                relationship_type="place",
                relationship_label="Place",
                evidence=["Atlantia is home to Jory Ravenmark."],
            ),
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="jory_ravenmark",
                relationship_type="home",
                relationship_label="Home",
                evidence=["Jory Ravenmark watched the tide from the Harbor."],
            ),
            CombinedRelationshipEdge(
                source="family_tree",
                target="atlantia",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Atlantia is listed beside Mrs Nightbloom."],
            ),
            CombinedRelationshipEdge(
                source="family_tree",
                target="mrs_nightbloom",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Atlantia is listed beside Mrs Nightbloom."],
            ),
        ],
    )
    heading_id = "source_heading__sourcedocumentatlantialore__line_3__harbor"
    definition = lore_graph_view_definitions("Places")[PLACES_FILE_VIEW_TAB]

    projected = project_lore_graph_for_view(
        graph,
        definition=definition,
        selection=LoreGraphViewSelection(
            view_name=PLACES_FILE_VIEW_TAB,
            source_file=str(atlantia_path),
            heading_id=heading_id,
            hide_source_document_roots=True,
        ),
    )

    assert heading_id in projected.characters
    assert "jory_ravenmark" in projected.characters
    assert "family_tree" not in projected.characters
    assert "mrs_nightbloom" not in projected.characters


def test_place_lore_graph_keeps_source_place_and_character_connections(tmp_path):
    place_lore_path = tmp_path / "Atlantia_Lore.md"
    place_lore_path.write_text(
        "\n".join(
            [
                "# Atlantia Lore",
                "Atlantia is home to Jory Ravenmark.",
                "## Town Overview",
                "Atlantia grew around the harbor, the watch tower, and the roads inland.",
                "## The Harbor",
                "Jory Ravenmark watched the tide from the Harbor.",
                "## The Watch Tower",
                "Mrs Nightbloom kept watch from the Watch Tower.",
                "## Sunstone Mage College",
                "Orin Nightbloom studied at Sunstone Mage College.",
                "### Faculty",
                "Mrs Nightbloom keeps old records here.",
                "#### Ignored Detail",
                "This deeper heading is not shown in the place graph.",
                "Stone and Students are common words here.",
            ]
        ),
        encoding="utf-8",
    )
    family_tree_path = tmp_path / "Family_Tree.md"
    family_tree_path.write_text(
        "\n".join(
            [
                "# Family Tree",
                "Atlantia is listed beside Mrs Nightbloom.",
            ]
        ),
        encoding="utf-8",
    )
    graph = CombinedCharacterGraph(
        characters={
            "source_document__atlantia_lore": CombinedCharacterNode(
                id="source_document__atlantia_lore",
                name="Atlantia Lore",
                source_file=str(place_lore_path),
                node_type="source_document",
            ),
            "atlantia": CombinedCharacterNode(
                id="atlantia",
                name="Atlantia",
                source_file=str(place_lore_path),
                node_type="place",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
            "orin_nightbloom": CombinedCharacterNode(
                id="orin_nightbloom",
                name="Orin Nightbloom",
                source_file="world_building/lore/character_sheets/Orin_Nightbloom.md",
                node_type="character",
            ),
            "sunstone_mage_college": CombinedCharacterNode(
                id="sunstone_mage_college",
                name="Sunstone Mage College",
                source_file=str(place_lore_path),
                node_type="place",
            ),
            "ignis_cult": CombinedCharacterNode(
                id="ignis_cult",
                name="Indigo Cult",
                source_file=str(place_lore_path),
                node_type="group",
            ),
            "justice": CombinedCharacterNode(
                id="justice",
                name="Justice",
                source_file=str(place_lore_path),
                node_type="character",
            ),
            "stone": CombinedCharacterNode(
                id="stone",
                name="Stone",
                source_file=str(place_lore_path),
                node_type="character",
            ),
            "students": CombinedCharacterNode(
                id="students",
                name="Students",
                source_file=str(place_lore_path),
                node_type="character",
            ),
            "family_tree": CombinedCharacterNode(
                id="family_tree",
                name="Family Tree",
                source_file=str(family_tree_path),
                node_type="source_document",
            ),
            "mrs_nightbloom": CombinedCharacterNode(
                id="mrs_nightbloom",
                name="Mrs Nightbloom",
                source_file="world_building/lore/session_notes/Family_Tree.md",
                node_type="character",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="atlantia",
                relationship_type="place",
                relationship_label="Place",
                evidence=["Atlantia is home to Jory Ravenmark."],
            ),
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="jory_ravenmark",
                relationship_type="home",
                relationship_label="Home",
                evidence=["Atlantia is home to Jory Ravenmark."],
            ),
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="jory_ravenmark",
                relationship_type="home",
                relationship_label="Home",
                evidence=["Jory Ravenmark watched the tide from the Harbor."],
            ),
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="mrs_nightbloom",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Mrs Nightbloom kept watch from the Watch Tower."],
            ),
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="orin_nightbloom",
                relationship_type="studied",
                relationship_label="Studied",
                evidence=["Orin Nightbloom studied at Sunstone Mage College."],
            ),
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="sunstone_mage_college",
                relationship_type="contains",
                relationship_label="Contains",
                evidence=["Orin Nightbloom studied at Sunstone Mage College."],
            ),
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="ignis_cult",
                relationship_type="threat",
                relationship_label="Threat",
            ),
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="stone",
                relationship_type="ally",
                relationship_label="Ally",
                evidence=["Stone and Students are common words here."],
            ),
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="students",
                relationship_type="referenced",
                relationship_label="Referenced",
                evidence=["Stone and Students are common words here."],
            ),
            CombinedRelationshipEdge(
                source="orin_nightbloom",
                target="sunstone_mage_college",
                relationship_type="studied",
                relationship_label="Studied",
            ),
            CombinedRelationshipEdge(
                source="family_tree",
                target="atlantia",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Atlantia is listed beside Mrs Nightbloom."],
            ),
            CombinedRelationshipEdge(
                source="family_tree",
                target="mrs_nightbloom",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Atlantia is listed beside Mrs Nightbloom."],
            ),
        ],
    )

    place_graph = place_lore_graph(graph)
    atlantia_heading_id = "source_heading__sourcedocumentatlantialore__line_1__atlantialore"
    harbor_heading_id = "source_heading__sourcedocumentatlantialore__line_5__theharbor"
    watch_tower_heading_id = "source_heading__sourcedocumentatlantialore__line_7__thewatchtower"
    college_heading_id = "source_heading__sourcedocumentatlantialore__line_9__sunstonemagecollege"
    family_heading_id = "source_heading__familytree__line_1__familytree"

    assert set(place_graph.characters) == {
        "source_document__atlantia_lore",
        "family_tree",
        atlantia_heading_id,
        harbor_heading_id,
        watch_tower_heading_id,
        college_heading_id,
        family_heading_id,
        "atlantia",
        "jory_ravenmark",
        "orin_nightbloom",
        "mrs_nightbloom",
    }
    assert {(edge.source, edge.target) for edge in place_graph.edges} == {
        ("source_document__atlantia_lore", atlantia_heading_id),
        (atlantia_heading_id, "atlantia"),
        (atlantia_heading_id, harbor_heading_id),
        (atlantia_heading_id, watch_tower_heading_id),
        (atlantia_heading_id, college_heading_id),
        ("atlantia", harbor_heading_id),
        ("atlantia", watch_tower_heading_id),
        ("atlantia", college_heading_id),
        (atlantia_heading_id, "jory_ravenmark"),
        (harbor_heading_id, "jory_ravenmark"),
        (watch_tower_heading_id, "mrs_nightbloom"),
        (college_heading_id, "orin_nightbloom"),
        ("family_tree", family_heading_id),
        (family_heading_id, "atlantia"),
        (family_heading_id, "mrs_nightbloom"),
    }
    labels_by_edge = {
        (edge.source, edge.target): edge.relationship_label
        for edge in place_graph.edges
    }
    assert labels_by_edge[("source_document__atlantia_lore", atlantia_heading_id)] == ""
    assert labels_by_edge[(atlantia_heading_id, "atlantia")] == ""
    assert labels_by_edge[(atlantia_heading_id, "jory_ravenmark")] == "Home"
    assert labels_by_edge[("atlantia", harbor_heading_id)] == "Contains"
    assert labels_by_edge[("atlantia", watch_tower_heading_id)] == "Contains"
    assert labels_by_edge[("atlantia", college_heading_id)] == "Contains"
    assert labels_by_edge[(family_heading_id, "mrs_nightbloom")] == "Mentions"
    dot = combined_relationship_dot(
        place_graph,
        main_character_ids=set(place_graph.characters),
        graphviz_config={"column_layout": "session_note_lore"},
    )
    assert '"source_document__atlantia_lore" [' not in dot
    assert '"family_tree" [' not in dot
    assert f'"{atlantia_heading_id}" [' in dot
    assert f'"{family_heading_id}" [' in dot
    table_rows = place_lore_connection_rows(place_graph)
    assert {row["Connection Type"] for row in table_rows} == {"Character"}
    assert {row["Connection"] for row in table_rows} == {
        "Jory Ravenmark",
        "Orin Nightbloom",
        "Mrs Nightbloom",
    }
    assert {row["Relationship"] for row in table_rows} == {"Home", "Studied", "Mentions"}
    assert place_graph.characters[atlantia_heading_id].node_type == "note"
    assert place_graph.characters[atlantia_heading_id].is_heading is True
    assert place_graph.characters[atlantia_heading_id].heading_level == 1
    assert place_graph.characters[harbor_heading_id].node_type == "place"
    assert place_graph.characters[harbor_heading_id].is_heading is True
    assert place_graph.characters[harbor_heading_id].heading_level == 2
    assert place_graph.characters[harbor_heading_id].name == "Harbor"
    assert place_graph.characters[watch_tower_heading_id].node_type == "place"
    assert place_graph.characters[watch_tower_heading_id].is_heading is True
    assert place_graph.characters[watch_tower_heading_id].heading_level == 2
    assert place_graph.characters[watch_tower_heading_id].name == "Watch Tower"
    assert place_graph.characters[college_heading_id].node_type == "place"
    assert place_graph.characters[college_heading_id].is_heading is True
    assert place_graph.characters[college_heading_id].heading_level == 2
    note_rows = lore_information_rows(place_graph)
    assert {
        (row["Heading"], row["Summary"])
        for row in note_rows
    } == {
        ("Town Overview", "Atlantia grew around the harbor, the watch tower, and the roads inland."),
        ("Faculty", "Mrs Nightbloom keeps old records here."),
    }
    assert all(node.name != "Faculty" for node in place_graph.characters.values())
    assert all(node.name != "Ignored Detail" for node in place_graph.characters.values())
    assert "justice" not in place_graph.characters
    assert "ignis_cult" not in place_graph.characters
    assert "stone" not in place_graph.characters
    assert "students" not in place_graph.characters

    file_view_graph = place_lore_graph(graph, source_file=str(place_lore_path))
    assert "source_document__atlantia_lore" in file_view_graph.characters
    assert "family_tree" not in file_view_graph.characters
    assert "mrs_nightbloom" in file_view_graph.characters
    directory_file_view_graph = place_lore_graph(
        graph,
        source_file=str(place_lore_path),
        hide_source_document_roots=True,
    )
    assert "source_document__atlantia_lore" not in directory_file_view_graph.characters
    assert "mrs_nightbloom" in directory_file_view_graph.characters

    heading_view_graph = place_lore_graph(graph, heading_id=college_heading_id)
    assert set(heading_view_graph.characters) == {
        "source_document__atlantia_lore",
        atlantia_heading_id,
        "atlantia",
        college_heading_id,
        "orin_nightbloom",
    }
    heading_view_without_root = place_lore_graph(
        graph,
        heading_id=college_heading_id,
        hide_source_document_roots=True,
    )
    assert "source_document__atlantia_lore" not in heading_view_without_root.characters
    assert {
        atlantia_heading_id,
        "atlantia",
        college_heading_id,
        "orin_nightbloom",
    }.issubset(heading_view_without_root.characters)


def test_place_lore_dot_uses_source_heading_place_character_columns():
    graph = CombinedCharacterGraph(
        characters={
            "source_document__atlantia_lore": CombinedCharacterNode(
                id="source_document__atlantia_lore",
                name="Atlantia Lore",
                source_file="world_building/lore/places/Atlantia_Lore.md",
                node_type="source_document",
            ),
            "atlantia": CombinedCharacterNode(
                id="atlantia",
                name="Atlantia",
                source_file="world_building/lore/places/Atlantia_Lore.md",
                node_type="place",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
            "source_heading__atlantia__location": CombinedCharacterNode(
                id="source_heading__atlantia__location",
                name="Harbor",
                source_file="world_building/lore/places/Atlantia_Lore.md",
                node_type="source_heading_place_2",
            ),
            "source_heading__atlantia__districts": CombinedCharacterNode(
                id="source_heading__atlantia__districts",
                name="Districts",
                source_file="world_building/lore/places/Atlantia_Lore.md",
                node_type="source_heading_1",
            ),
            "source_heading__atlantia__faculty": CombinedCharacterNode(
                id="source_heading__atlantia__faculty",
                name="Faculty",
                source_file="world_building/lore/places/Atlantia_Lore.md",
                node_type="source_heading_3",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="source_heading__atlantia__districts",
                relationship_type="heading",
                relationship_label="",
            ),
            CombinedRelationshipEdge(
                source="source_heading__atlantia__districts",
                target="source_heading__atlantia__location",
                relationship_type="heading",
                relationship_label="",
            ),
            CombinedRelationshipEdge(
                source="source_heading__atlantia__location",
                target="source_heading__atlantia__faculty",
                relationship_type="heading",
                relationship_label="",
            ),
            CombinedRelationshipEdge(
                source="source_heading__atlantia__location",
                target="atlantia",
                relationship_type="location",
                relationship_label="Location",
            ),
            CombinedRelationshipEdge(
                source="atlantia",
                target="jory_ravenmark",
                relationship_type="home",
                relationship_label="Home",
            ),
        ],
    )

    dot = combined_relationship_dot(
        graph,
        main_character_ids=set(graph.characters),
        graphviz_config={"column_layout": "place_lore"},
    )

    source_column = dot[dot.index('subgraph "cluster_column_0_source_documents_places"') :]
    heading_1_column = dot[dot.index('subgraph "cluster_column_1_markdown_heading_1"') :]
    heading_2_column = dot[dot.index('subgraph "cluster_column_2_markdown_heading_2"') :]
    heading_3_column = dot[dot.index('subgraph "cluster_column_3_markdown_heading_3"') :]

    assert source_column.index('"source_document__atlantia_lore"') < source_column.index('subgraph "cluster_column_1_markdown_heading_1"')
    assert source_column.index('"atlantia"') < source_column.index('subgraph "cluster_column_1_markdown_heading_1"')
    assert heading_1_column.index('"source_heading__atlantia__districts"') < heading_1_column.index('subgraph "cluster_column_2_markdown_heading_2"')
    assert heading_2_column.index('"source_heading__atlantia__location"') < heading_2_column.index('subgraph "cluster_column_3_markdown_heading_3"')
    assert heading_3_column.index('"source_heading__atlantia__faculty"') < heading_3_column.index('subgraph "cluster_column_4_character_connections"')
    assert '"source_heading__atlantia__location" [label="Harbor", fillcolor="#dcfce7", color="#94a3b8", shape="component"' in dot
    assert (
        'subgraph "cluster_column_4_character_connections" '
        '{ rank=same; style=invis; "graph_column_4"; "jory_ravenmark"; }'
    ) in dot
    assert '"atlantia" -> "jory_ravenmark" [label="Home", tailport=e, headport=w];' in dot


def test_directory_place_lore_dot_keeps_source_documents_in_column_zero():
    graph = CombinedCharacterGraph(
        characters={
            "source_document__atlantia_lore": CombinedCharacterNode(
                id="source_document__atlantia_lore",
                name="Atlantia Lore",
                source_file="world_building/lore/places/Atlantia_Lore.md",
                node_type="source_document",
            ),
            "atlantia": CombinedCharacterNode(
                id="atlantia",
                name="Atlantia",
                source_file="world_building/lore/places/Atlantia_Lore.md",
                node_type="place",
            ),
            "source_heading__atlantia__harbor": CombinedCharacterNode(
                id="source_heading__atlantia__harbor",
                name="Harbor",
                source_file="world_building/lore/places/Atlantia_Lore.md",
                node_type="source_heading_place_2",
            ),
            "source_heading__atlantia__faculty": CombinedCharacterNode(
                id="source_heading__atlantia__faculty",
                name="Faculty",
                source_file="world_building/lore/places/Atlantia_Lore.md",
                node_type="source_heading_3",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="atlantia",
                relationship_type="place",
                relationship_label="",
            ),
            CombinedRelationshipEdge(
                source="atlantia",
                target="source_heading__atlantia__harbor",
                relationship_type="contains",
                relationship_label="Contains",
            ),
            CombinedRelationshipEdge(
                source="source_heading__atlantia__harbor",
                target="source_heading__atlantia__faculty",
                relationship_type="heading",
                relationship_label="",
            ),
            CombinedRelationshipEdge(
                source="source_heading__atlantia__harbor",
                target="jory_ravenmark",
                relationship_type="home",
                relationship_label="Home",
            ),
        ],
    )

    dot = combined_relationship_dot(
        graph,
        main_character_ids=set(graph.characters),
        graphviz_config={"column_layout": "place_lore_directory"},
    )

    source_column = dot[dot.index('subgraph "cluster_column_0_source_documents"') :]
    heading_1_column = dot[dot.index('subgraph "cluster_column_1_markdown_heading_1"') :]
    heading_2_column = dot[dot.index('subgraph "cluster_column_2_markdown_heading_2"') :]
    heading_3_column = dot[dot.index('subgraph "cluster_column_3_markdown_heading_3"') :]

    assert source_column.index('"source_document__atlantia_lore"') < source_column.index('subgraph "cluster_column_1_markdown_heading_1"')
    assert heading_1_column.index('"atlantia"') < heading_1_column.index('subgraph "cluster_column_2_markdown_heading_2"')
    assert heading_2_column.index('"source_heading__atlantia__harbor"') < heading_2_column.index('subgraph "cluster_column_3_markdown_heading_3"')
    assert heading_3_column.index('"source_heading__atlantia__faculty"') < heading_3_column.index('subgraph "cluster_column_4_character_connections"')
    assert '"source_heading__atlantia__harbor" [label="Harbor", fillcolor="#dcfce7", color="#94a3b8", shape="component"' in dot


def test_directory_session_lore_dot_keeps_groups_with_sub_places_and_places_in_heading_one():
    graph = CombinedCharacterGraph(
        characters={
            "session_1": CombinedCharacterNode(
                id="session_1",
                name="Session 1",
                source_file="world_building/lore/session_notes/Session_1.md",
                node_type="source_document",
            ),
            "ravenmark_family": CombinedCharacterNode(
                id="ravenmark_family",
                name="Ravenmark Family",
                source_file="world_building/lore/session_notes/Session_1.md",
                node_type="group",
            ),
            "atlantia": CombinedCharacterNode(
                id="atlantia",
                name="Atlantia",
                source_file="world_building/lore/places/Atlantia_Lore.md",
                node_type="place",
            ),
            "source_heading__session_1__harbor": CombinedCharacterNode(
                id="source_heading__session_1__harbor",
                name="Harbor",
                source_file="world_building/lore/session_notes/Session_1.md",
                node_type="source_heading_place_2",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="session_1",
                target="ravenmark_family",
                relationship_type="mentions",
                relationship_label="",
            ),
            CombinedRelationshipEdge(
                source="session_1",
                target="atlantia",
                relationship_type="place",
                relationship_label="Place",
            ),
            CombinedRelationshipEdge(
                source="atlantia",
                target="source_heading__session_1__harbor",
                relationship_type="contains",
                relationship_label="Contains",
            ),
            CombinedRelationshipEdge(
                source="source_heading__session_1__harbor",
                target="jory_ravenmark",
                relationship_type="mentions",
                relationship_label="Mentions",
            ),
        ],
    )

    dot = combined_relationship_dot(
        graph,
        main_character_ids=set(graph.characters),
        graphviz_config={"column_layout": "session_note_lore_directory"},
    )

    source_column = dot[dot.index('subgraph "cluster_column_0_source_documents"') :]
    heading_1_column = dot[dot.index('subgraph "cluster_column_1_markdown_heading_1"') :]
    heading_2_column = dot[dot.index('subgraph "cluster_column_2_markdown_heading_2"') :]

    assert source_column.index('"session_1"') < source_column.index('subgraph "cluster_column_1_markdown_heading_1"')
    assert heading_1_column.index('"atlantia"') < heading_1_column.index('subgraph "cluster_column_2_markdown_heading_2"')
    assert heading_2_column.index('"ravenmark_family"') < heading_2_column.index('subgraph "cluster_column_3_markdown_heading_3"')
    assert heading_2_column.index('"source_heading__session_1__harbor"') < heading_2_column.index('subgraph "cluster_column_3_markdown_heading_3"')
    labels_by_edge = {
        (edge.source, edge.target): edge.relationship_label
        for edge in graph.edges
    }
    assert labels_by_edge[("session_1", "ravenmark_family")] == ""


def test_directory_session_lore_can_hide_headings_and_keep_context_edges(tmp_path):
    session_dir = tmp_path / "session_notes"
    session_dir.mkdir()
    session_path = session_dir / "Session_Notes_Fixture.md"
    session_path.write_text(
        "\n".join(
            [
                "# Session 4",
                "Tharevon traveled through the Pixi Kingdom.",
                "## Pixi Kingdom",
                "Tharevon met the court.",
                "Mira Vale mapped the Pixi Kingdom roads.",
                "## Indigo Cult",
                "Jory Ravenmark and Neal Lovington investigated the Indigo Cult.",
                "They traced the Indigo Cult to the Moon Gate.",
                "## Moon Blade",
                "Arlen Voss recovered the Moon Blade.",
                "Neal Lovington identified the Moon Blade.",
                "## Empty Cult",
                "The empty cult was named but had no visible character connection.",
            ]
        ),
        encoding="utf-8",
    )
    graph = CombinedCharacterGraph(
        characters={
            "session_notes_fixture": CombinedCharacterNode(
                id="session_notes_fixture",
                name="Session Notes Fixture",
                source_file=str(session_path),
                node_type="source_document",
            ),
            "tharevon": CombinedCharacterNode(
                id="tharevon",
                name="Tharevon",
                source_file="world_building/lore/character_sheets/Tharevon.md",
                node_type="character",
            ),
            "mira_vale": CombinedCharacterNode(
                id="mira_vale",
                name="Mira Vale",
                source_file="world_building/lore/character_sheets/Mira_Vale.md",
                node_type="character",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
            "neal_lovington": CombinedCharacterNode(
                id="neal_lovington",
                name="Neal Lovington",
                source_file="world_building/lore/character_sheets/Neal_Lovington.md",
                node_type="character",
            ),
            "pixi_kingdom": CombinedCharacterNode(
                id="pixi_kingdom",
                name="Pixi Kingdom",
                source_file="world_building/lore/places/Pixi_Kingdom.md",
                node_type="place",
            ),
            "ignis_cult": CombinedCharacterNode(
                id="ignis_cult",
                name="Indigo Cult",
                source_file="world_building/lore/session_notes/Session_Notes_Fixture.md",
                node_type="group",
            ),
            "moon_gate": CombinedCharacterNode(
                id="moon_gate",
                name="Moon Gate",
                source_file="world_building/lore/places/Moon_Gate.md",
                node_type="place",
            ),
            "moon_blade": CombinedCharacterNode(
                id="moon_blade",
                name="Moon Blade",
                source_file="world_building/lore/session_notes/Session_Notes_Fixture.md",
                node_type="artifact",
            ),
            "arlen_voss": CombinedCharacterNode(
                id="arlen_voss",
                name="Arlen Voss",
                source_file="world_building/lore/character_sheets/Arlen_Voss.md",
                node_type="character",
            ),
            "empty_cult": CombinedCharacterNode(
                id="empty_cult",
                name="Empty Cult",
                source_file="world_building/lore/session_notes/Session_Notes_Fixture.md",
                node_type="group",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="session_notes_fixture",
                target="tharevon",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Tharevon traveled through the Pixi Kingdom."],
            ),
            CombinedRelationshipEdge(
                source="session_notes_fixture",
                target="pixi_kingdom",
                relationship_type="place",
                relationship_label="Place",
                evidence=["Tharevon traveled through the Pixi Kingdom."],
            ),
            CombinedRelationshipEdge(
                source="session_notes_fixture",
                target="mira_vale",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Mira Vale mapped the Pixi Kingdom roads."],
            ),
            CombinedRelationshipEdge(
                source="session_notes_fixture",
                target="ignis_cult",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Jory Ravenmark and Neal Lovington investigated the Indigo Cult."],
            ),
            CombinedRelationshipEdge(
                source="session_notes_fixture",
                target="jory_ravenmark",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Jory Ravenmark and Neal Lovington investigated the Indigo Cult."],
            ),
            CombinedRelationshipEdge(
                source="session_notes_fixture",
                target="neal_lovington",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Jory Ravenmark and Neal Lovington investigated the Indigo Cult."],
            ),
            CombinedRelationshipEdge(
                source="session_notes_fixture",
                target="moon_gate",
                relationship_type="place",
                relationship_label="Place",
                evidence=["They traced the Indigo Cult to the Moon Gate."],
            ),
            CombinedRelationshipEdge(
                source="session_notes_fixture",
                target="empty_cult",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["The empty cult was named but had no visible character connection."],
            ),
            CombinedRelationshipEdge(
                source="session_notes_fixture",
                target="moon_blade",
                relationship_type="artifact",
                relationship_label="Artifact",
                evidence=["Arlen Voss recovered the Moon Blade."],
            ),
            CombinedRelationshipEdge(
                source="session_notes_fixture",
                target="arlen_voss",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Arlen Voss recovered the Moon Blade."],
            ),
            CombinedRelationshipEdge(
                source="session_notes_fixture",
                target="neal_lovington",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Neal Lovington identified the Moon Blade."],
            ),
        ],
    )

    projected = markdown_header_lore_graph(
        graph,
        source_file=str(session_path),
        fanout_linked_characters=True,
        hide_source_document_roots=True,
        hidden_heading_levels={1},
    )

    session_heading_id = "source_heading__sessionnotesfixture__line_1__session4"
    labels_by_edge = {
        (edge.source, edge.target): edge.relationship_label
        for edge in projected.edges
    }

    assert session_heading_id not in projected.characters
    assert "pixi_kingdom" in projected.characters
    assert "tharevon" in projected.characters
    assert labels_by_edge[("pixi_kingdom", "tharevon")] == "Session 4"

    all_headings_hidden = markdown_header_lore_graph(
        graph,
        source_file=str(session_path),
        fanout_linked_characters=True,
        hide_source_document_roots=True,
        hidden_heading_levels={1, 2, 3},
    )
    all_hidden_labels_by_edge = {
        (edge.source, edge.target): edge.relationship_label
        for edge in all_headings_hidden.edges
    }

    assert session_heading_id not in all_headings_hidden.characters
    assert "pixi_kingdom" in all_headings_hidden.characters
    assert "tharevon" in all_headings_hidden.characters
    assert "ignis_cult" in all_headings_hidden.characters
    assert "moon_blade" in all_headings_hidden.characters
    assert all_headings_hidden.characters["moon_blade"].node_type == "artifact"
    assert "empty_cult" not in all_headings_hidden.characters
    assert all_hidden_labels_by_edge[("pixi_kingdom", "tharevon")] == "Session 4"
    assert all_hidden_labels_by_edge[("pixi_kingdom", "mira_vale")] == "Pixi Kingdom"
    assert all_hidden_labels_by_edge[("ignis_cult", "jory_ravenmark")] == "Indigo Cult"
    assert all_hidden_labels_by_edge[("ignis_cult", "neal_lovington")] == "Indigo Cult"
    assert all_hidden_labels_by_edge[("ignis_cult", "moon_gate")] == "Indigo Cult"
    assert all_hidden_labels_by_edge[("moon_blade", "arlen_voss")] == "Moon Blade"


def test_session_note_group_heading_and_entity_are_not_rendered_as_duplicate_nodes(tmp_path):
    session_dir = tmp_path / "session_notes"
    session_dir.mkdir()
    session_path = session_dir / "Session_Notes_Fixture.md"
    session_path.write_text(
        "\n".join(
            [
                "# Session 4",
                "The party tracked a faction lead.",
                "## Indigo Cult",
                "Jory Ravenmark and Neal Lovington investigated the Indigo Cult.",
                "They traced the Indigo Cult to the Moon Gate.",
            ]
        ),
        encoding="utf-8",
    )
    graph = CombinedCharacterGraph(
        characters={
            "session_notes_fixture": CombinedCharacterNode(
                id="session_notes_fixture",
                name="Session Notes Fixture",
                source_file=str(session_path),
                node_type="source_document",
            ),
            "indigo_cult": CombinedCharacterNode(
                id="indigo_cult",
                name="Indigo Cult",
                source_file=str(session_path),
                node_type="group",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
            "neal_lovington": CombinedCharacterNode(
                id="neal_lovington",
                name="Neal Lovington",
                source_file="world_building/lore/character_sheets/Neal_Lovington.md",
                node_type="character",
            ),
            "moon_gate": CombinedCharacterNode(
                id="moon_gate",
                name="Moon Gate",
                source_file="world_building/lore/places/Moon_Gate.md",
                node_type="place",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="session_notes_fixture",
                target="indigo_cult",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Jory Ravenmark and Neal Lovington investigated the Indigo Cult."],
            ),
            CombinedRelationshipEdge(
                source="session_notes_fixture",
                target="jory_ravenmark",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Jory Ravenmark and Neal Lovington investigated the Indigo Cult."],
            ),
            CombinedRelationshipEdge(
                source="session_notes_fixture",
                target="neal_lovington",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Jory Ravenmark and Neal Lovington investigated the Indigo Cult."],
            ),
            CombinedRelationshipEdge(
                source="session_notes_fixture",
                target="moon_gate",
                relationship_type="place",
                relationship_label="Place",
                evidence=["They traced the Indigo Cult to the Moon Gate."],
            ),
        ],
    )

    projected = markdown_header_lore_graph(
        graph,
        source_file=str(session_path),
        fanout_linked_characters=True,
        hide_source_document_roots=True,
        hidden_heading_levels={1},
    )
    indigo_nodes = [
        node_id
        for node_id, node in projected.characters.items()
        if node.name == "Indigo Cult"
    ]
    edge_pairs = {(edge.source, edge.target) for edge in projected.edges}

    assert indigo_nodes == ["indigo_cult"]
    assert ("indigo_cult", "jory_ravenmark") in edge_pairs
    assert ("indigo_cult", "neal_lovington") in edge_pairs
    assert ("indigo_cult", "moon_gate") in edge_pairs


def test_directory_session_lore_hide_file_name_preserves_source_bridge_connections():
    graph = CombinedCharacterGraph(
        characters={
            "atlantia_bandits": CombinedCharacterNode(
                id="atlantia_bandits",
                name="Atlantia Bandits",
                source_file="world_building/lore/session_notes/Session_Notes.md",
                node_type="group",
            ),
            "session_notes": CombinedCharacterNode(
                id="session_notes",
                name="Session Notes",
                source_file="world_building/lore/session_notes/Session_Notes.md",
                node_type="source_document",
            ),
            "source_heading__session_notes__session_1": CombinedCharacterNode(
                id="source_heading__session_notes__session_1",
                name="Session 1",
                source_file="world_building/lore/session_notes/Session_Notes.md",
                node_type="source_heading_1",
            ),
            "source_heading__session_notes__session_2": CombinedCharacterNode(
                id="source_heading__session_notes__session_2",
                name="Session 2",
                source_file="world_building/lore/session_notes/Session_Notes.md",
                node_type="source_heading_1",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
            "orin_nightbloom": CombinedCharacterNode(
                id="orin_nightbloom",
                name="Orin Nightbloom",
                source_file="world_building/lore/character_sheets/Orin_Nightbloom.md",
                node_type="character",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="atlantia_bandits",
                target="session_notes",
                relationship_type="mentions",
                relationship_label="Mentions",
            ),
            CombinedRelationshipEdge(
                source="session_notes",
                target="source_heading__session_notes__session_1",
                relationship_type="heading",
                relationship_label="",
            ),
            CombinedRelationshipEdge(
                source="source_heading__session_notes__session_1",
                target="jory_ravenmark",
                relationship_type="mentions",
                relationship_label="Mentions",
            ),
            CombinedRelationshipEdge(
                source="session_notes",
                target="source_heading__session_notes__session_2",
                relationship_type="heading",
                relationship_label="",
            ),
            CombinedRelationshipEdge(
                source="source_heading__session_notes__session_2",
                target="orin_nightbloom",
                relationship_type="mentions",
                relationship_label="Mentions",
            ),
        ],
    )

    projected = graph_without_source_document_roots(graph)
    labels_by_edge = {
        (edge.source, edge.target): edge.relationship_label
        for edge in projected.edges
    }

    assert "session_notes" not in projected.characters
    assert labels_by_edge[("atlantia_bandits", "source_heading__session_notes__session_1")] == "Session Notes"
    assert labels_by_edge[("atlantia_bandits", "source_heading__session_notes__session_2")] == "Session Notes"
    assert labels_by_edge[("source_heading__session_notes__session_1", "jory_ravenmark")] == "Mentions"
    assert labels_by_edge[("source_heading__session_notes__session_2", "orin_nightbloom")] == "Mentions"

    headings_hidden = graph_without_markdown_heading_levels(projected, {1, 2, 3})
    hidden_labels_by_edge = {
        (edge.source, edge.target): edge.relationship_label
        for edge in headings_hidden.edges
    }

    assert "source_heading__session_notes__session_1" not in headings_hidden.characters
    assert "source_heading__session_notes__session_2" not in headings_hidden.characters
    assert hidden_labels_by_edge[("atlantia_bandits", "jory_ravenmark")] == "Session 1"
    assert hidden_labels_by_edge[("atlantia_bandits", "orin_nightbloom")] == "Session 2"


def test_hidden_session_headings_preserve_connection_table_evidence():
    graph = CombinedCharacterGraph(
        characters={
            "source_heading__session_notes__july_2024": CombinedCharacterNode(
                id="source_heading__session_notes__july_2024",
                name="July 2024",
                source_file="world_building/lore/session_notes/Session_Notes.md",
                node_type="source_heading_1",
            ),
            "source_heading__session_notes__orchard": CombinedCharacterNode(
                id="source_heading__session_notes__orchard",
                name="Feasting Orchard",
                source_file="world_building/lore/session_notes/Session_Notes.md",
                node_type="source_heading_2",
            ),
            "mog": CombinedCharacterNode(
                id="mog",
                name="Mog",
                source_file="world_building/lore/character_sheets/Mog.md",
                node_type="character",
            ),
            "morningstar": CombinedCharacterNode(
                id="morningstar",
                name="Morningstar",
                source_file="world_building/lore/character_sheets/Morningstar.md",
                node_type="character",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="source_heading__session_notes__july_2024",
                target="source_heading__session_notes__orchard",
                relationship_type="heading",
                relationship_label="",
            ),
            CombinedRelationshipEdge(
                source="source_heading__session_notes__orchard",
                target="mog",
                relationship_type="mentions",
                relationship_label="Mentioned",
                evidence=["Mog went to the Feasting Orchard to participate and win the First Fairycake Eating Competition."],
            ),
            CombinedRelationshipEdge(
                source="source_heading__session_notes__orchard",
                target="morningstar",
                relationship_type="mentions",
                relationship_label="Mentioned",
                evidence=["Morningstar joined Mog at the Feasting Orchard."],
            ),
        ],
    )

    projected = graph_without_markdown_heading_levels(graph, {1, 2, 3})
    rows = lore_graph_connection_rows(projected)

    assert rows
    assert {row["Character"] for row in rows} == {"Mog", "Morningstar"}
    assert "July 2024" not in {row["Character"] for row in rows}
    assert "Feasting Orchard" not in {row["Character"] for row in rows}
    assert any("First Fairycake Eating Competition" in row["Evidence"] for row in rows)


def test_hiding_h1_preserves_edges_to_visible_h2_and_h3_descendants():
    graph = CombinedCharacterGraph(
        characters={
            "session_notes": CombinedCharacterNode(
                id="session_notes",
                name="Session Notes",
                source_file="world_building/lore/session_notes/Session_Notes.md",
                node_type="source_document",
            ),
            "source_heading__session_notes__session_1": CombinedCharacterNode(
                id="source_heading__session_notes__session_1",
                name="Session 1",
                source_file="world_building/lore/session_notes/Session_Notes.md",
                node_type="source_heading_1",
            ),
            "source_heading__session_notes__bandits": CombinedCharacterNode(
                id="source_heading__session_notes__bandits",
                name="Atlantia Bandits",
                source_file="world_building/lore/session_notes/Session_Notes.md",
                node_type="source_heading_group_2",
            ),
            "source_heading__session_notes__ambush": CombinedCharacterNode(
                id="source_heading__session_notes__ambush",
                name="Harbor Ambush",
                source_file="world_building/lore/session_notes/Session_Notes.md",
                node_type="source_heading_3",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="session_notes",
                target="source_heading__session_notes__session_1",
                relationship_type="heading",
                relationship_label="",
            ),
            CombinedRelationshipEdge(
                source="source_heading__session_notes__session_1",
                target="source_heading__session_notes__bandits",
                relationship_type="heading",
                relationship_label="",
            ),
            CombinedRelationshipEdge(
                source="source_heading__session_notes__bandits",
                target="source_heading__session_notes__ambush",
                relationship_type="heading",
                relationship_label="",
            ),
            CombinedRelationshipEdge(
                source="source_heading__session_notes__ambush",
                target="jory_ravenmark",
                relationship_type="mentions",
                relationship_label="Mentions",
            ),
        ],
    )

    projected = graph_without_markdown_heading_levels(graph, {1})
    labels_by_edge = {
        (edge.source, edge.target): edge.relationship_label
        for edge in projected.edges
    }

    assert "source_heading__session_notes__session_1" not in projected.characters
    assert "source_heading__session_notes__bandits" in projected.characters
    assert "source_heading__session_notes__ambush" in projected.characters
    assert labels_by_edge[("session_notes", "source_heading__session_notes__bandits")] == "Session 1"
    assert labels_by_edge[("session_notes", "source_heading__session_notes__ambush")] == "Session 1"
    assert labels_by_edge[("source_heading__session_notes__ambush", "jory_ravenmark")] == "Mentions"


def test_source_heading_artifact_nodes_use_artifact_shape():
    graph = CombinedCharacterGraph(
        characters={
            "source_heading__session_notes__relics": CombinedCharacterNode(
                id="source_heading__session_notes__relics",
                name="Recovered Relics",
                source_file="world_building/lore/session_notes/Session_Notes.md",
                node_type="source_heading_artifact_2",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="source_heading__session_notes__relics",
                target="jory_ravenmark",
                relationship_type="mentions",
                relationship_label="Mentioned",
            ),
        ],
    )

    dot = combined_relationship_dot(graph)

    assert (
        '"source_heading__session_notes__relics" [label="Recovered Relics", '
        'fillcolor="#fce7f3", color="#94a3b8", shape="hexagon"'
    ) in dot


def test_hiding_file_name_and_h1_preserves_all_direct_h1_connections():
    graph = CombinedCharacterGraph(
        characters={
            "atlantia_bandits": CombinedCharacterNode(
                id="atlantia_bandits",
                name="Atlantia Bandits",
                source_file="world_building/lore/session_notes/Session_Notes.md",
                node_type="group",
            ),
            "session_notes": CombinedCharacterNode(
                id="session_notes",
                name="Session Notes",
                source_file="world_building/lore/session_notes/Session_Notes.md",
                node_type="source_document",
            ),
            "source_heading__session_notes__session_1": CombinedCharacterNode(
                id="source_heading__session_notes__session_1",
                name="Session 1",
                source_file="world_building/lore/session_notes/Session_Notes.md",
                node_type="source_heading_1",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
            "orin_nightbloom": CombinedCharacterNode(
                id="orin_nightbloom",
                name="Orin Nightbloom",
                source_file="world_building/lore/character_sheets/Orin_Nightbloom.md",
                node_type="character",
            ),
            "neal_lovington": CombinedCharacterNode(
                id="neal_lovington",
                name="Neal Lovington",
                source_file="world_building/lore/character_sheets/Neal_Lovington.md",
                node_type="character",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="atlantia_bandits",
                target="session_notes",
                relationship_type="mentions",
                relationship_label="Mentions",
            ),
            CombinedRelationshipEdge(
                source="session_notes",
                target="source_heading__session_notes__session_1",
                relationship_type="heading",
                relationship_label="",
            ),
            CombinedRelationshipEdge(
                source="source_heading__session_notes__session_1",
                target="jory_ravenmark",
                relationship_type="mentions",
                relationship_label="Mentions",
            ),
            CombinedRelationshipEdge(
                source="source_heading__session_notes__session_1",
                target="orin_nightbloom",
                relationship_type="mentions",
                relationship_label="Mentions",
            ),
            CombinedRelationshipEdge(
                source="source_heading__session_notes__session_1",
                target="neal_lovington",
                relationship_type="mentions",
                relationship_label="Mentions",
            ),
        ],
    )

    file_hidden = graph_without_source_document_roots(graph)
    projected = graph_without_markdown_heading_levels(file_hidden, {1})
    labels_by_edge = {
        (edge.source, edge.target): edge.relationship_label
        for edge in projected.edges
    }

    assert "session_notes" not in projected.characters
    assert "source_heading__session_notes__session_1" not in projected.characters
    assert labels_by_edge[("atlantia_bandits", "jory_ravenmark")] == "Session 1"
    assert labels_by_edge[("atlantia_bandits", "orin_nightbloom")] == "Session 1"
    assert labels_by_edge[("atlantia_bandits", "neal_lovington")] == "Session 1"


def test_selected_h1_filter_still_preserves_all_edges_when_h1_is_hidden(tmp_path):
    session_dir = tmp_path / "session_notes"
    session_dir.mkdir()
    session_path = session_dir / "Session_Notes.md"
    session_path.write_text(
        "\n".join(
            [
                "# Session 1",
                "Jory Ravenmark met Orin Nightbloom and Neal Lovington.",
            ]
        ),
        encoding="utf-8",
    )
    graph = CombinedCharacterGraph(
        characters={
            "atlantia_bandits": CombinedCharacterNode(
                id="atlantia_bandits",
                name="Atlantia Bandits",
                source_file=str(session_path),
                node_type="group",
            ),
            "session_notes": CombinedCharacterNode(
                id="session_notes",
                name="Session Notes",
                source_file=str(session_path),
                node_type="source_document",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
            "orin_nightbloom": CombinedCharacterNode(
                id="orin_nightbloom",
                name="Orin Nightbloom",
                source_file="world_building/lore/character_sheets/Orin_Nightbloom.md",
                node_type="character",
            ),
            "neal_lovington": CombinedCharacterNode(
                id="neal_lovington",
                name="Neal Lovington",
                source_file="world_building/lore/character_sheets/Neal_Lovington.md",
                node_type="character",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="atlantia_bandits",
                target="session_notes",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Jory Ravenmark met Orin Nightbloom and Neal Lovington."],
            ),
            CombinedRelationshipEdge(
                source="session_notes",
                target="jory_ravenmark",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Jory Ravenmark met Orin Nightbloom and Neal Lovington."],
            ),
            CombinedRelationshipEdge(
                source="session_notes",
                target="orin_nightbloom",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Jory Ravenmark met Orin Nightbloom and Neal Lovington."],
            ),
            CombinedRelationshipEdge(
                source="session_notes",
                target="neal_lovington",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Jory Ravenmark met Orin Nightbloom and Neal Lovington."],
            ),
        ],
    )
    selected_h1_id = "source_heading__sessionnotes__line_1__session1"

    projected = markdown_header_lore_graph(
        graph,
        source_file=str(session_path),
        heading_id=selected_h1_id,
        fanout_linked_characters=True,
        hide_source_document_roots=True,
        hidden_heading_levels={1},
    )
    labels_by_edge = {
        (edge.source, edge.target): edge.relationship_label
        for edge in projected.edges
    }

    assert selected_h1_id not in projected.characters
    assert labels_by_edge[("atlantia_bandits", "jory_ravenmark")] == "Session 1"
    assert labels_by_edge[("atlantia_bandits", "orin_nightbloom")] == "Session 1"
    assert labels_by_edge[("atlantia_bandits", "neal_lovington")] == "Session 1"


def test_directory_session_lore_hide_file_name_removes_misclassified_session_notes_source(tmp_path):
    session_dir = tmp_path / "session_notes"
    session_dir.mkdir()
    session_path = session_dir / "Session_Notes.md"
    session_path.write_text("# Session Notes\n\nTharevon traveled through the Pixi Kingdom.", encoding="utf-8")
    graph = CombinedCharacterGraph(
        characters={
            "session_notes": CombinedCharacterNode(
                id="session_notes",
                name="Session Notes",
                source_file=str(session_path),
                node_type="character",
            ),
            "tharevon": CombinedCharacterNode(
                id="tharevon",
                name="Tharevon",
                source_file="world_building/lore/character_sheets/Tharevon.md",
                node_type="character",
            ),
            "pixi_kingdom": CombinedCharacterNode(
                id="pixi_kingdom",
                name="Pixi Kingdom",
                source_file="world_building/lore/places/Pixi_Kingdom.md",
                node_type="place",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="session_notes",
                target="tharevon",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Tharevon traveled through the Pixi Kingdom."],
            ),
            CombinedRelationshipEdge(
                source="session_notes",
                target="pixi_kingdom",
                relationship_type="place",
                relationship_label="Place",
                evidence=["Tharevon traveled through the Pixi Kingdom."],
            ),
        ],
    )

    projected = markdown_header_lore_graph(
        graph,
        source_file=str(session_path),
        fanout_linked_characters=True,
        hide_source_document_roots=True,
    )

    assert "session_notes" not in projected.characters
    assert "tharevon" in projected.characters
    assert "pixi_kingdom" in projected.characters


def test_session_note_lore_graph_uses_headings_groups_characters_and_places(tmp_path):
    session_dir = tmp_path / "session_notes"
    session_dir.mkdir()
    session_path = session_dir / "Family_Tree.md"
    side_session_path = session_dir / "Side_Notes.md"
    session_path.write_text(
        "\n".join(
            [
                "# Family Tree",
                "The Ravenmark Family keeps watch over Atlantia.",
                "## Ravenmark Trouble",
                "Jory Ravenmark found trouble in Atlantia.",
                "### Empty Aside",
                "Nothing extracted here.",
            ]
        ),
        encoding="utf-8",
    )
    side_session_path.write_text("# Side Notes\n\nJory Ravenmark visits Atlantia.", encoding="utf-8")
    graph = CombinedCharacterGraph(
        characters={
            "family_tree": CombinedCharacterNode(
                id="family_tree",
                name="Family Tree",
                source_file=str(session_path),
                node_type="source_document",
            ),
            "ravenmark_family": CombinedCharacterNode(
                id="ravenmark_family",
                name="Ravenmark Family",
                source_file=str(session_path),
                node_type="group",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
            "mary_ravenmark": CombinedCharacterNode(
                id="mary_ravenmark",
                name="Mary Ravenmark",
                source_file="world_building/lore/character_sheets/Mary_Ravenmark.md",
                node_type="character",
            ),
            "atlantia": CombinedCharacterNode(
                id="atlantia",
                name="Atlantia",
                source_file="world_building/lore/places/Atlantia_Lore.md",
                node_type="place",
            ),
            "side_notes": CombinedCharacterNode(
                id="side_notes",
                name="Side Notes",
                source_file=str(side_session_path),
                node_type="source_document",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="family_tree",
                target="ravenmark_family",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["The Ravenmark Family keeps watch over Atlantia."],
            ),
            CombinedRelationshipEdge(
                source="family_tree",
                target="jory_ravenmark",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Jory Ravenmark found trouble in Atlantia."],
            ),
            CombinedRelationshipEdge(
                source="family_tree",
                target="atlantia",
                relationship_type="place",
                relationship_label="Place",
                evidence=["Jory Ravenmark found trouble in Atlantia."],
            ),
            CombinedRelationshipEdge(
                source="side_notes",
                target="jory_ravenmark",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Jory Ravenmark visits Atlantia."],
            ),
            CombinedRelationshipEdge(
                source="ravenmark_family",
                target="mary_ravenmark",
                relationship_type="family",
                relationship_label="Family",
                evidence=["Mary Ravenmark is linked to the Ravenmark Family."],
            ),
        ],
    )

    lore_graph = markdown_header_lore_graph(graph)
    family_heading_id = "source_heading__familytree__line_1__familytree"
    trouble_heading_id = "source_heading__familytree__line_3__ravenmarktrouble"

    assert set(lore_graph.characters) == {
        "family_tree",
        "side_notes",
        "ravenmark_family",
        "jory_ravenmark",
        "atlantia",
        family_heading_id,
        trouble_heading_id,
        "source_heading__sidenotes__line_1__sidenotes",
    }
    assert {(edge.source, edge.target) for edge in lore_graph.edges} == {
        ("family_tree", family_heading_id),
        (family_heading_id, "ravenmark_family"),
        (family_heading_id, trouble_heading_id),
        (trouble_heading_id, "jory_ravenmark"),
        (trouble_heading_id, "atlantia"),
        ("side_notes", "source_heading__sidenotes__line_1__sidenotes"),
        ("source_heading__sidenotes__line_1__sidenotes", "jory_ravenmark"),
    }
    assert all(node.name != "Empty Aside" for node in lore_graph.characters.values())

    dot = combined_relationship_dot(
        lore_graph,
        main_character_ids=set(lore_graph.characters),
        graphviz_config={"column_layout": "session_note_lore"},
    )
    assert 'subgraph "cluster_column_0_source_documents"' in dot
    assert 'subgraph "cluster_column_2_markdown_heading_2"' in dot
    assert 'subgraph "cluster_column_4_character_connections"' in dot
    assert '"family_tree" [' not in dot
    assert '"side_notes" [' not in dot
    assert f'"{family_heading_id}" [' in dot
    assert '"jory_ravenmark"' in dot
    assert '"atlantia"' in dot
    heading_2_column = dot[dot.index('subgraph "cluster_column_2_markdown_heading_2"') :]
    assert heading_2_column.index('"ravenmark_family"') < heading_2_column.index('subgraph "cluster_column_3_markdown_heading_3"')
    assert "mary_ravenmark" not in lore_graph.characters

    file_view_graph = markdown_header_lore_graph(
        graph,
        source_file=str(session_path),
        fanout_linked_characters=True,
    )
    assert "family_tree" in file_view_graph.characters
    assert "side_notes" not in file_view_graph.characters
    assert "mary_ravenmark" in file_view_graph.characters
    assert ("ravenmark_family", "mary_ravenmark") in {
        (edge.source, edge.target)
        for edge in file_view_graph.edges
    }
    directory_file_view_graph = markdown_header_lore_graph(
        graph,
        source_file=str(session_path),
        fanout_linked_characters=True,
        hide_source_document_roots=True,
    )
    assert "family_tree" not in directory_file_view_graph.characters
    assert family_heading_id in directory_file_view_graph.characters
    assert "side_notes" not in directory_file_view_graph.characters
    assert "mary_ravenmark" in directory_file_view_graph.characters
    assert all(
        edge.source != "family_tree" and edge.target != "family_tree"
        for edge in directory_file_view_graph.edges
    )

    heading_view_graph = markdown_header_lore_graph(graph, heading_id=trouble_heading_id)
    assert set(heading_view_graph.characters) == {
        "family_tree",
        family_heading_id,
        trouble_heading_id,
        "jory_ravenmark",
        "atlantia",
    }
    assert "ravenmark_family" not in heading_view_graph.characters


def test_session_note_directory_projection_deduplicates_family_tree_h1_from_extracted_entities(tmp_path):
    session_dir = tmp_path / "session_notes"
    session_dir.mkdir()
    session_path = session_dir / "Family_Tree.md"
    session_path.write_text(
        "\n".join(
            [
                "# Family Tree",
                "These notes collect family history around Atlantia.",
                "## The Ravenmark Family",
                "Jory Ravenmark and Mary Ravenmark are discussed here.",
            ]
        ),
        encoding="utf-8",
    )
    graph = CombinedCharacterGraph(
        characters={
            "family_tree": CombinedCharacterNode(
                id="family_tree",
                name="Family Tree",
                source_file=str(session_path),
                node_type="source_document",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file=str(session_path),
                node_type="character",
            ),
            "mary_ravenmark": CombinedCharacterNode(
                id="mary_ravenmark",
                name="Mary Ravenmark",
                source_file=str(session_path),
                node_type="character",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="family_tree",
                target="jory_ravenmark",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Jory Ravenmark and Mary Ravenmark are discussed here."],
            ),
            CombinedRelationshipEdge(
                source="family_tree",
                target="mary_ravenmark",
                relationship_type="mentions",
                relationship_label="Mentions",
                evidence=["Jory Ravenmark and Mary Ravenmark are discussed here."],
            ),
        ],
    )

    projected = markdown_header_lore_graph(
        graph,
        source_file=str(session_path),
        fanout_linked_characters=True,
        hide_source_document_roots=True,
    )

    family_tree_headings = [
        node
        for node in projected.characters.values()
        if node.name == "Family Tree" and node.is_heading
    ]
    assert len(family_tree_headings) == 1
    assert "source_heading__joryravenmark__line_1__familytree" not in projected.characters
    assert "source_heading__maryravenmark__line_1__familytree" not in projected.characters
    assert "jory_ravenmark" in projected.characters
    assert "mary_ravenmark" in projected.characters


def test_session_note_graph_keeps_only_session_note_connections():
    graph = CombinedCharacterGraph(
        characters={
            "family_tree": CombinedCharacterNode(
                id="family_tree",
                name="Family Tree",
                source_file="world_building/lore/session_notes/2026-07-19_Family_Tree.md",
                node_type="source_document",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
            "source_document__atlantia_lore": CombinedCharacterNode(
                id="source_document__atlantia_lore",
                name="Atlantia Lore",
                source_file="world_building/lore/places/Atlantia_Lore.md",
                node_type="source_document",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="family_tree",
                target="jory_ravenmark",
                relationship_type="mentions",
                relationship_label="Mentions",
            ),
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="jory_ravenmark",
                relationship_type="home",
                relationship_label="Home",
            ),
        ],
    )

    filtered = session_note_graph(graph)

    assert set(filtered.characters) == {"family_tree", "jory_ravenmark"}
    assert [(edge.source, edge.target) for edge in filtered.edges] == [("family_tree", "jory_ravenmark")]


def test_duplicate_source_document_nodes_are_collapsed_in_rendered_lore_graph():
    graph = CombinedCharacterGraph(
        characters={
            "family_tree_1": CombinedCharacterNode(
                id="family_tree_1",
                name="Family Tree",
                source_file="world_building/lore/session_notes/Family_Tree.md",
                node_type="source_document",
            ),
            "family_tree_2": CombinedCharacterNode(
                id="family_tree_2",
                name="Family Tree",
                source_file="world_building/lore/session_notes/Family_Tree.md",
                node_type="source_document",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="family_tree_1",
                target="jory_ravenmark",
                relationship_type="mentions",
                relationship_label="Mentions",
            ),
            CombinedRelationshipEdge(
                source="family_tree_2",
                target="jory_ravenmark",
                relationship_type="mentions",
                relationship_label="Mentions",
            ),
        ],
    )

    render_lore_graph(graph, label_font_color="#000000", column_layout="session_note_lore")

    assert sum(1 for node in graph.characters.values() if node.node_type == "source_document" and node.name == "Family Tree") == 1
    assert len(graph.edges) == 1


def test_structured_knowledge_view_hides_source_document_knots():
    graph = CombinedCharacterGraph(
        characters={
            "source_document__atlantia_lore": CombinedCharacterNode(
                id="source_document__atlantia_lore",
                name="Atlantia Lore",
                source_file="world_building/lore/places/Atlantia_Lore.md",
                node_type="source_document",
            ),
            "jory_ravenmark": CombinedCharacterNode(
                id="jory_ravenmark",
                name="Jory Ravenmark",
                source_file="world_building/lore/character_sheets/Jory_Ravenmark.md",
                node_type="character",
            ),
        },
        edges=[
            CombinedRelationshipEdge(
                source="source_document__atlantia_lore",
                target="jory_ravenmark",
                relationship_type="home",
                relationship_label="Home",
            ),
        ],
    )

    filtered = graph_without_lore_source_knots(graph)

    assert filtered.characters == {}
    assert filtered.edges == []
