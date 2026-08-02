# Current Knowledge Graph View Behavior

This document captures the behavior of the knowledge-graph views as they are implemented today in the Streamlit app and the Graphviz rendering helpers. It is intended as a reference for the current UI behavior before the graph layer is refactored.

## Scope

The current implementation renders knowledge-graph views inside the main navigation tabs for Characters, Places, and Session Notes. The visible subviews are selected in the Graphviz rendering layer, and the behavior differs slightly depending on which main tab is active.

## Shared Behavior

- The UI renders graph views through the Graphviz helper module rather than through a dedicated projection API.
- The visible tab names are determined by the current main tab in the helper logic.
- The graph rendering path uses a mix of direct graph data and view-specific filtering functions.
- Empty states are handled with Streamlit info messages such as “Add Place Lore To Use File View.” or “No Session Note Connections Were Found For This File.”
- Some views hide source-document roots in order to reduce duplicate-looking roots in the graph.

## Characters Tab

### Character View
- Shows one subtab per main character node.
- Each subtab includes a selectbox that allows the user to choose a root node for the focused graph.
- The graph shown is a focused “other connections” view centered on the selected node.
- A table of associated connections appears beneath the graph when rows are available.
- The empty state says that no other connections were found for the selected node yet.

### Party View
- Renders a character-focused connection graph based on the character-sheet combined graph.
- The graph is built from the full character-connection graph for the current combined dataset.
- It also renders a relationship detail table with additional connection information.

## Places Tab

### Party View
- Reuses the same party-view rendering path as the Characters tab.
- The behavior is driven by the current graph input rather than by a place-specific rendering branch.

### Location View
- Allows the user to select a place-lore source file from the available place-source-document nodes.
- Source files are discovered from graph nodes where `source_file` is present and the node matches the place-source predicate.
- The dropdown label uses the file name portion of the source path.
- Uses the selected file to build a place graph filtered to that exact source file.
- The graph uses a place-specific column layout and fanout behavior to include linked characters.
- If no file is selected, the UI shows an info message asking the user to add place lore first.
- If the selected file produces no connections, the UI reports that no place-lore connections were found.

### Heading View
- Builds a projected graph from markdown headings and allows the user to select a heading.
- Heading options are populated from markdown subheadings belonging to nodes with `source_file` and that match the place-source predicate.
- The dropdown shows entries as `FileName / H{level}: {heading text}`.
- The view defaults to hiding source-document roots in order to keep the heading-based graph cleaner.
- If no heading is selected, the UI reports that markdown headings are needed before the section view can be used.
- If the selected heading produces no graph characters, the UI reports that no place-lore connections were found for that heading.

### Directory File View
- Uses the same flow as the location view, but swaps in the directory-oriented column layout.
- It still filters by place lore source documents and hides source-document roots by default.
- The file dropdown is populated the same way as the normal location view.
- The intent is to present the same place-lore data in a more structured directory-oriented layout.

## Session Notes Tab

### Party View
- Reuses the same party-view rendering path as the other main tabs.
- It is not a session-note-specific graph view; it is a shared character-connection view.

### Location View
- Allows the user to select a session-note source file from the available session-note graph nodes.
- Source files are discovered from graph nodes where `source_file` is present and the node matches the session-note predicate.
- The dropdown label uses the file name portion of the source path.
- Uses the selected file to build a filtered session-note graph.
- If the user has just imported session notes, the view can preselect the newly imported source file from session state.
- If no source file is selected, the UI asks the user to add session notes first.
- If the selected file produces no connections, the UI reports that no session-note connections were found for that file.

### Directory File View
- Uses the same flow as the session-note location view, but swaps in the directory-oriented column layout.
- It still filters by session-note source documents and hides source-document roots by default.
- The file dropdown is populated the same way as the normal session-note location view.
- It is intended to show the same session-note graph in a more structured directory-oriented presentation.

## Current Divergences

- The behavior is not yet driven by a single canonical projection API.
- The same UI concept is implemented through multiple view branches that differ by source predicate, column layout, and root-hiding settings.
- The rendering logic depends partly on the active main tab rather than a unified graph-view contract.
- Some of the current heuristics rely on source-document detection and node-type checks that are more brittle than the planned canonical graph model.
