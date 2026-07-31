# Knowledge Graph Creation
Build a role-playing character sheet tracker which will pull in information from multiple data sources and display semantic connections between characters. 

## Features

- **Use local language model to clean up character summaries and backstories**
- **Import session notes from external data sources extracting heading and date information**
- **Generate knowledge graph from multiple data import sources and display information to users in clean readable format**

## Dependencies

- [Python 3.11](https://www.python.org/downloads/): Streamlit App
- [llama.cpp](https://github.com/ggml-org/llama.cpp): For Backstory Rewrites

## Knowledge Graph Views

Main Tab [Characters, Places, Session Notes]

- Characters: [Single Character, Party View]
- Places: [Location View, Heading View]
- Session Notes: [Location View, Directory File View]

## Tech Stack
- Streamlit, LangChain, Llama Cli, Graphviz