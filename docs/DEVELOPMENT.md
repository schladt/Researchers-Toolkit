# Developer Guide

This document describes how the Researchers-Toolkit application is structured, the technologies used, and how the pieces fit together.

## Architecture Overview

The app is a **single-page application** with a split-pane layout:

```
┌─────────────────────────────────────────────────────┐
│                    Browser (SPA)                     │
├──────────────────┬──┬───────────────────────────────┤
│  Console Panel   │  │        Graph Panel            │
│  (xterm.js)      │  │  (Cytoscape.js / Table View)  │
│                  │◄►│                               │
│  Socket.IO ↕     │  │  REST API ↕                   │
├──────────────────┴──┴───────────────────────────────┤
│              Flask + Flask-SocketIO                  │
│                  (app.py)                            │
├─────────────────────────────────────────────────────┤
│  RTKCore (rtk_core.py) + CommandHandler             │
├──────────────┬──────────────────────────────────────┤
│   Neo4j DB   │       Semantic Scholar API           │
└──────────────┴──────────────────────────────────────┘
```

**Data flow:**
1. Console commands travel over WebSocket (Socket.IO) → `CommandHandler` → `RTKCore` → Neo4j/S2 API
2. Graph/search interactions use REST endpoints → Neo4j queries → Cytoscape.js JSON

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend server | Flask 3.x + eventlet | HTTP + WebSocket server |
| Real-time I/O | Flask-SocketIO + Socket.IO 4.7 | Console command/response streaming |
| Graph database | Neo4j 5.x (bolt protocol) | Persistent knowledge graph storage |
| Data source | Semantic Scholar API | Paper discovery and metadata |
| Graph visualization | Cytoscape.js 3.28 (CDN) | Interactive node-edge rendering |
| Terminal emulator | xterm.js 5.5 (CDN) | Browser-based CLI |
| NLP | NLTK | Keyword extraction from abstracts |
| Rate limiting | ratelimit + backoff | S2 API throttling (1 req/sec) |

**No frontend build step** — vanilla JavaScript with CDN-loaded libraries. No npm, webpack, or bundler.

## Project Structure

```
Researchers-Toolkit/
├── app.py              # Flask entry point, REST API, Socket.IO handlers
├── rtk_core.py         # Business logic: Paper class, S2 API, Neo4j ops, NLP
├── command_handler.py  # Console command parser and dispatcher
├── rtk.py              # Original standalone CLI (still functional)
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (not committed)
├── templates/
│   └── index.html      # Single-page app HTML shell
├── static/
│   ├── css/
│   │   └── style.css   # All application styles (dark theme)
│   ├── js/
│   │   ├── app.js      # Main entry: init, search, layout, table view
│   │   ├── graph.js    # Cytoscape init, styling, context menu, tooltip
│   │   └── terminal.js # xterm.js init, Socket.IO I/O, command history
│   └── favicon.svg     # Network graph favicon
└── docs/
    └── DEVELOPMENT.md  # This file
```

## Backend Components

### `app.py` — Server & API

The Flask application provides:

**REST Endpoints:**
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Serves the SPA HTML |
| `/api/graph` | GET | All nodes/edges (supports `?limit=N`) |
| `/api/graph/neighbors/<id>` | GET | Neighbors of a specific node |
| `/api/graph/search` | GET | Case-insensitive node search (`?q=term`) |
| `/api/graph/cypher` | POST | Execute read-only Cypher queries |
| `/api/graph/stats` | GET | Node/edge counts by type |
| `/api/graph/reset` | POST | Delete all graph data |

**Socket.IO Events:**
| Event | Direction | Purpose |
|-------|-----------|---------|
| `connect` | server→client | Initializes CommandHandler, sends welcome |
| `command` | client→server | Receives CLI input from the console |
| `output` | server→client | Streams command output line-by-line |
| `done` | server→client | Signals command execution complete |

**Key design decisions:**
- `RTKCore` and `CommandHandler` are lazily initialized singletons
- Cypher endpoint only allows `MATCH`/`OPTIONAL` queries (read-only guard)
- Node IDs are derived from domain-specific properties (PaperId, AuthorId, etc.)

### `rtk_core.py` — Business Logic

Contains all research operations independent of the web layer:

- **`Paper` class** — Data model for academic papers with metadata fields
- **`RTKCore` class** — Orchestrates Neo4j connection, API calls, graph operations
- **`s2_api_get()`** — Rate-limited Semantic Scholar API wrapper (1 req/sec, exponential backoff)
- **Neo4j operations** — Paper/author/venue/keyword MERGE operations
- **NLP pipeline** — NLTK-based keyword extraction (tokenize → filter stopwords → lemmatize)

### `command_handler.py` — CLI Parser

Parses text commands and dispatches to `RTKCore`:

- Maintains search result state (`_last_results`, pagination)
- Commands: `search`, `author`, `paper`, `select`, `add`, `tags`, `graph`, `help`, `more`
- Emits formatted output via callback function (ANSI color codes for terminal rendering)

## Frontend Components

### `templates/index.html`

The HTML shell defines the layout:
- **container** → `console-panel` (left) + `divider` (resizable) + `graph-panel` (right)
- **graph-panel** → header (title, search, controls) → `cypher-bar` → `graph-container` / `table-view`
- CDN scripts loaded in `<head>`, app scripts at end of `<body>`

Script load order: `graph.js` → `terminal.js` → `app.js` (app.js orchestrates, runs after DOM ready)

### `static/js/graph.js`

Cytoscape.js initialization and interaction:

- **Node styles** — Color-coded by type (Paper=blue, Author=teal, Venue=purple, Keyword=green, Tag=orange)
- **Edge styles** — Colored by relationship type
- **Event handlers** — `dbltap` (expand), `cxttap` (context menu), `mouseover/out` (tooltip)
- **Context menu** — Type-specific actions (expand, details, open URL, remove, select neighbors)
- **`expandNeighbors()`** — Fetches and adds connected nodes via REST
- **`loadGraph()`** — Full graph load triggered by CLI `graph load`

### `static/js/terminal.js`

xterm.js terminal with:

- Socket.IO integration for command/response streaming
- Command history (up/down arrows)
- Local line editing (backspace, cursor movement)
- ASCII art banner on init
- Prompt rendering with `showPrompt()`

### `static/js/app.js`

Main orchestration and UI features:

- **`initDivider()`** — Draggable panel resize (20%-80% bounds)
- **`initGraphSearch()`** — Search bar, Cypher toggle, legend toggle, view toggle (graph/table)
- **`initGraphControls()`** — Layout selector, export button
- **`initToolbarTooltips()`** — Styled hover tooltips on toolbar buttons
- **`graphSearch()`** — REST search, replaces current graph view with results
- **`runCypher()`** — POST Cypher query, replaces graph view with results
- **`loadPreview()`** — Fetches 10 nodes on startup as an initial preview
- **`updateGraphInfo()`** — Updates node/edge counter, syncs table if visible
- **`populateTable()`** — Renders graph data as categorized HTML tables

### `static/css/style.css`

Single stylesheet with dark theme. Key sections:
- Layout and panel sizing (flexbox)
- Graph controls and toolbar button styling
- Cytoscape container and legend overlay
- Context menu and tooltip positioning
- Table view with type-colored headers
- Banner messages (preview indicator)

## Graph Schema

### Node Types
| Type | Key Properties | ID Field |
|------|---------------|----------|
| Paper | Title, Year, CitationCount, Abstract, URL, TLDR | PaperId |
| Author | Name, AuthorId | AuthorId |
| Venue | Name | venue:{Name} |
| Keyword | Value | kw:{Value} |
| Tag | Tag | tag:{Tag} |

### Relationship Types
| Relationship | From → To | Meaning |
|-------------|-----------|---------|
| REFERENCES | Paper → Paper | Citation link |
| AUTHORED_BY | Paper → Author | Authorship |
| PUBLISHED_IN | Paper → Venue | Publication venue |
| HAS_KEYWORD | Paper → Keyword | Extracted term |
| TAGGED | Any → Tag | User-defined grouping |

## Running for Development

```bash
source .venv/bin/activate
python app.py
```

The Flask server runs on `http://localhost:5000` with `debug=True` (auto-reloads on Python file changes). Frontend changes (JS/CSS/HTML) take effect on browser refresh.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NEO4J_URL` | Yes | Bolt connection URL (e.g. `bolt://localhost:7687`) |
| `NEO4J_USER` | Yes | Neo4j username |
| `NEO4J_PASSWORD` | Yes | Neo4j password |
| `S2_API_KEY` | No | Semantic Scholar API key (higher rate limits) |
