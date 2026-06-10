# Researchers-Toolkit

A browser-based tool for exploring academic research through connected knowledge graphs. Built with Python, Flask, Neo4j, and the Semantic Scholar API, this toolkit lets you discover papers, build citation networks, and interactively visualize relationships between papers, authors, venues, and concepts — all from a single-page app with a split-pane layout: interactive graph visualization on the right, command console on the left.

## Features

### Graph Visualization

- Interactive force-directed graph (Cytoscape.js)
- Multiple layout algorithms (Force, Tree, Concentric, Circle, Grid)
- Search bar for finding nodes by name
- Cypher mode for raw Neo4j queries
- Right-click context menus (expand neighbors, remove nodes, open URLs)
- Hover tooltips with node details
- Double-click to expand node neighbors
- Switchable graph/table view
- Export graph as PNG

### Research Discovery

- **Keyword Search**: Find papers by research topics
- **Author Search**: Discover papers by specific researchers
- **Paper ID Lookup**: Direct access via Semantic Scholar IDs

### Knowledge Graph Construction

- Automatic graph building: papers, authors, venues, keywords, tags
- Citation network mapping (REFERENCES relationships)
- Author collaboration tracking (AUTHORED_BY relationships)
- Venue organization (PUBLISHED_IN relationships)
- Keyword extraction from abstracts (NLTK)
- Custom project tagging

### Console Commands

- `search <query>` — Search Semantic Scholar for papers
- `author <name>` — Search for authors
- `paper <id>` — Get paper details by ID
- `select <n>` — Select a result from the last search
- `add` / `add refs` / `add keywords` — Add papers to graph
- `tags <tag1, tag2>` — Set project tags
- `graph load|clear|stats|reset` — Graph management
- `help` — Show all available commands

## Installation

### Prerequisites

1. **Python 3.8+**
2. **Neo4j Database** (Community or Enterprise)
3. **Semantic Scholar API Key** (optional, recommended for higher rate limits)

### Setup

```bash
# Clone the repository
git clone https://github.com/schladt/Researchers-Toolkit.git
cd Researchers-Toolkit

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file in the project root:

```bash
# Required: Neo4j Database Connection
NEO4J_URL=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j

# Optional: Semantic Scholar API Key (for higher rate limits)
S2_API_KEY=your_semantic_scholar_api_key_here
```

#### Getting a Semantic Scholar API Key (Optional)

1. Visit [Semantic Scholar API](https://www.semanticscholar.org/product/api)
2. Sign up for a free account
3. Generate an API key

The tool works without an API key but with lower rate limits (1 req/sec).

### Neo4j Setup

Install Neo4j via any method:

- [Neo4j Desktop](https://neo4j.com/download/) (recommended for beginners)
- `brew install neo4j` (macOS)
- Docker: `docker run -p 7474:7474 -p 7687:7687 --env NEO4J_AUTH=neo4j/neo4j neo4j:latest`

## Usage

### Starting the App

```bash
source .venv/bin/activate
python app.py
```

Open `http://localhost:5000` in your browser.

### Quick Start

1. Type `search machine learning transformers` in the console
2. Select a result with `select 1`
3. Add it to the graph with `add` (or `add refs` for citations too)
4. Search for more papers in the graph search bar
5. Double-click nodes to expand their neighbors
6. Right-click nodes for more options
7. Switch layouts with the dropdown (Force, Tree, Concentric, etc.)

### CLI Mode

The original CLI is still available:

```bash
python rtk.py
```

## Contributing

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for architecture details, project structure, and developer reference.

## License

MIT License — see [LICENSE](LICENSE) for details.

**Author**: Mike Schladt (2026)
**Repository**: [github.com/schladt/Researchers-Toolkit](https://github.com/schladt/Researchers-Toolkit)
