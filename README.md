# Researchers-Toolkit

A browser-based tool for exploring academic research through connected knowledge graphs. Built with Python, Flask, and the Semantic Scholar API, this toolkit lets you discover papers, build citation networks, and interactively visualize relationships between papers, authors, venues, and concepts — all from a single-page app with a split-pane layout: interactive graph visualization on the right, command console on the left.

## Features

### Graph Visualization

- Interactive graph with multiple layout algorithms (fcose, dagre, cose, tree, concentric, circle, grid)
- Collapsible settings panel with layout selection, node sizing, display toggles, and file actions
- Dynamic node sizing by citation count or connection degree
- Color-coded nodes by type: Papers, Authors, Venues, Keywords, Tags
- Edge labels for relationship types (References, Authored by, Published in)
- Right-click context menus (expand neighbors, remove nodes, open URLs)
- Hover tooltips with node details (citations, degree, references)
- Double-click to expand node neighbors
- Click-to-highlight neighborhood (dims unconnected nodes)
- Switchable graph/table view
- Filter bar for narrowing by type, year range, and text
- Legend overlay
- Export graph as PNG
- Graph info showing displayed vs total study counts

### Research Discovery

- **Keyword Search**: Find papers by research topics
- **Author Search**: Discover papers by specific researchers
- **Paper ID Lookup**: Direct access via Semantic Scholar IDs
- **Field-of-Study Filter**: Narrow searches to specific academic fields

### Knowledge Graph Construction

- In-memory graph store with JSON export/import for persistence
- Automatic graph building: papers, authors, venues, keywords, tags
- Citation network mapping (REFERENCES relationships)
- Author collaboration tracking (AUTHORED_BY relationships)
- Venue organization (PUBLISHED_IN relationships)
- Keyword extraction from abstracts (NLTK)
- Custom project tagging
- Study management: save/load entire study or current view, merge or replace on import

### Console Commands

- `search <query>` — Search Semantic Scholar for papers
- `author <name>` — Search for authors
- `paper <id>` — Get paper details by ID
- `select <n>` — Select a result from the last search
- `add` / `add refs` / `add cites` / `add keywords` — Add papers to graph
- `refs [n]` / `cites [n]` — Show references or citations of selected paper
- `tags <tag1, tag2>` — Set project tags
- `field <name|clear>` — Set or clear field-of-study filter
- `graph load|clear|stats|reset` — Graph management
- `help` — Show all available commands

## Installation

### Prerequisites

1. **Python 3.8+**
2. **Semantic Scholar API Key** (optional, recommended for higher rate limits)

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
# Optional: Semantic Scholar API Key (for higher rate limits)
S2_API_KEY=your_semantic_scholar_api_key_here
```

#### Getting a Semantic Scholar API Key (Optional)

1. Visit [Semantic Scholar API](https://www.semanticscholar.org/product/api)
2. Sign up for a free account
3. Generate an API key

The tool works without an API key but with lower rate limits (1 req/sec).

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
