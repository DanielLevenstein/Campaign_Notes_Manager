# Persistence Layer Spec

Application needs to be updated so all IO operations go through a single persistence layer.

## Current Behavior
- User documents are stored in the `world_building/lore` directory
- `world_building/backup` Contains a backup of all UI edits made through UI.
- `world_building/lore` Contains the users `character_sheets`, `places` and `session_notes`
- `meta_data/character_graph` contains a backup of imported session notes. 

## Updated Behavior
- All UI operations should go through a single persistence module.
- Graphing metadata should be stored in `world_building/meta_data` and should use the same directory structure as the source data.
- And an update to a md file should trigger an update to the corresponding graph data file.
- All interactions with the graph database should go through the new persistence layer.
- Synthetic edges should not be stored to the persisted graph structure. 