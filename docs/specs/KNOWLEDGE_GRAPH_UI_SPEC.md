# Knowledge Graph Views
- Move knowledge graph code into a helper module called graphviz_rendering.py
- Split graph rendering into four tabs [Characters Graph, Place Graph, Session Note Graph, Full Graph]

Move all graph views to their own top-level streamlit tab and create sub views below them based on the specs below.

## Characters Graph
Views [Single Character, Party View]
Column 0: Family Names
Column 1: Main Characters
Column 2: Secondary Characters & places

## Places Graph
Views [Location View, Heading View]
- File View allows the user to view lore items from a single source file
- Section View allows users to view lore items from a single Markdown heading
  - For session views hide headings which have no root nodes associated with them. 

Column 0: Source Documents 
Column 1: Markdown Heading 1 & Main Place Names
Column 2: Markdown Heading 2 & Sub Places
Column 3: Markdown Heading 3 & Sub Places
Column 4: Character Connections

Sort all connections within each column by the number of connections with the edges with the most connections displayed first.
Display all graph connections as a straight line and enforce that columns are maintained.
Table of connections should only show edges with character connections

## Session Notes Graph
Views [Location View, Directory File View]
- File View allows the user to view lore items from a single source file
- Section View allows users to view lore items from a single Markdown heading
  - For session views hide headings which have no root nodes associated with them. 

Column 0: Source Documents
Column 1: Markdown Heading 1 & Place Name
Column 2: Markdown Heading 2, Sub Places, & Groups
Column 3: Markdown Heading 3
Column 4: Character Connections

- Spec Update: Move groups to Column 2 with sub places.

Sort all connections within each column by the number of connections with the edges with the most connections displayed first.
Display all graph connections as a straight line and enforce that columns are maintained.
Table of connections should only show edges with character connections

## Heading View
Views [Places, Session Notes]
Uses the same UI as session Notes Graph but allows the user to select what sub-heading they would like to see in the UI. 
Currently only available in party tab.

## Full Structured Graph
Views [Places, Session Notes]
- Column 0: Places, groups, and family names
- Column 1: Main characters
- Column 2: Secondary characters, secondary places, families, and groups

Full Structured Graph uses `full_structured_graph`, hides lore source-document knots, and renders relationship lines with straight routing so edge labels remain visually attached to their owning edges.
Family-name nodes use the trapezoid shape in Full Structured Graph while keeping the family color.

# Coming Soon 
## Node Deduplication
Views [Character Deduplication, Place Deduplication, Node Removal]
Freeform graph with all headings and source documents hidden.

See [NODE_DEDUPLICATION_DESIGN.md](NODE_DEDUPLICATION_DESIGN.md) for the review workflow, table layout, matching signals, review rules, and test plan.
