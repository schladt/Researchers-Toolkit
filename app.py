from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit

from rtk_core import RTKCore
from command_handler import CommandHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rtk-dev-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize core engine and command handler
core = None
handler = None


def get_core():
    """Lazy-init the RTKCore singleton."""
    global core
    if core is None:
        core = RTKCore()
    return core


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/graph')
def api_graph():
    """Return all nodes and edges in Cytoscape.js JSON format."""
    c = get_core()
    nodes = []
    edges = []

    limit = request.args.get('limit', 2000, type=int)

    # Fetch all nodes with labels
    records, _, _ = c.driver.execute_query(
        "MATCH (n) RETURN n, labels(n) AS labels LIMIT $limit",
        limit=limit
    )
    node_ids = set()
    for record in records:
        node = record["n"]
        labels = record["labels"]
        node_type = labels[0] if labels else "Unknown"
        node_data = dict(node)
        node_id = _get_node_id(node_data, node_type)
        node_ids.add(node_id)
        nodes.append({
            "data": {
                "id": node_id,
                "label": _get_node_label(node_data, node_type),
                "type": node_type,
                **node_data
            }
        })

    # Fetch all relationships
    records, _, _ = c.driver.execute_query(
        "MATCH (a)-[r]->(b) "
        "RETURN a, labels(a) AS a_labels, type(r) AS rel_type, b, labels(b) AS b_labels "
        "LIMIT 5000"
    )
    for record in records:
        a_data = dict(record["a"])
        b_data = dict(record["b"])
        a_type = record["a_labels"][0] if record["a_labels"] else "Unknown"
        b_type = record["b_labels"][0] if record["b_labels"] else "Unknown"
        source = _get_node_id(a_data, a_type)
        target = _get_node_id(b_data, b_type)
        # Only include edges where both endpoints are in the loaded node set
        if source in node_ids and target in node_ids:
            edges.append({
                "data": {
                    "source": source,
                    "target": target,
                    "type": record["rel_type"]
                }
            })

    return jsonify({"nodes": nodes, "edges": edges})


@app.route('/api/graph/neighbors/<node_id>')
def api_graph_neighbors(node_id):
    """Return neighbors of a given node."""
    c = get_core()
    nodes = []
    edges = []

    # Find the node and its neighbors
    records, _, _ = c.driver.execute_query(
        "MATCH (a)-[r]-(b) "
        "WHERE a.PaperId = $nid OR a.AuthorId = $nid OR a.Name = $nid OR a.Tag = $nid OR a.Value = $nid "
        "RETURN b, labels(b) AS labels, type(r) AS rel_type, "
        "       startNode(r) = a AS outgoing, a, labels(a) AS a_labels "
        "LIMIT 100",
        nid=node_id
    )
    for record in records:
        b_data = dict(record["b"])
        b_type = record["labels"][0] if record["labels"] else "Unknown"
        b_id = _get_node_id(b_data, b_type)
        nodes.append({
            "data": {
                "id": b_id,
                "label": _get_node_label(b_data, b_type),
                "type": b_type,
                **b_data
            }
        })

        a_data = dict(record["a"])
        a_type = record["a_labels"][0] if record["a_labels"] else "Unknown"
        a_id = _get_node_id(a_data, a_type)

        if record["outgoing"]:
            edges.append({"data": {"source": a_id, "target": b_id, "type": record["rel_type"]}})
        else:
            edges.append({"data": {"source": b_id, "target": a_id, "type": record["rel_type"]}})

    return jsonify({"nodes": nodes, "edges": edges})


@app.route('/api/graph/stats')
def api_graph_stats():
    """Return node/edge counts by type."""
    c = get_core()

    # Count nodes by label
    records, _, _ = c.driver.execute_query(
        "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt"
    )
    node_counts = {record["label"]: record["cnt"] for record in records}

    # Count relationships by type
    records, _, _ = c.driver.execute_query(
        "MATCH ()-[r]->() RETURN type(r) AS rel_type, count(r) AS cnt"
    )
    edge_counts = {record["rel_type"]: record["cnt"] for record in records}

    total_nodes = sum(node_counts.values())
    total_edges = sum(edge_counts.values())

    return jsonify({
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "node_counts": node_counts,
        "edge_counts": edge_counts
    })


@app.route('/api/graph/search')
def api_graph_search():
    """Search Neo4j for nodes matching a query. Returns matched nodes + their direct edges."""
    c = get_core()
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({"nodes": [], "edges": []})

    # Search across node types using case-insensitive CONTAINS
    records, _, _ = c.driver.execute_query(
        "MATCH (n) "
        "WHERE n.Title CONTAINS $q OR n.Name CONTAINS $q OR n.Tag CONTAINS $q "
        "   OR n.Value CONTAINS $q OR toLower(n.Title) CONTAINS toLower($q) "
        "   OR toLower(n.Name) CONTAINS toLower($q) "
        "RETURN DISTINCT n, labels(n) AS labels "
        "LIMIT 50",
        q=q
    )

    nodes = []
    node_ids = set()
    for record in records:
        node_data = dict(record["n"])
        node_type = record["labels"][0] if record["labels"] else "Unknown"
        node_id = _get_node_id(node_data, node_type)
        if node_id not in node_ids:
            node_ids.add(node_id)
            nodes.append({
                "data": {
                    "id": node_id,
                    "label": _get_node_label(node_data, node_type),
                    "type": node_type,
                    **node_data
                }
            })

    # Fetch edges between matched nodes
    edges = []
    if node_ids:
        records, _, _ = c.driver.execute_query(
            "MATCH (a)-[r]->(b) "
            "WHERE (a.PaperId IN $ids OR a.AuthorId IN $ids OR a.Name IN $ids OR a.Tag IN $ids OR a.Value IN $ids) "
            "  AND (b.PaperId IN $ids OR b.AuthorId IN $ids OR b.Name IN $ids OR b.Tag IN $ids OR b.Value IN $ids) "
            "RETURN a, labels(a) AS a_labels, type(r) AS rel_type, b, labels(b) AS b_labels",
            ids=list(node_ids)
        )
        for record in records:
            a_data = dict(record["a"])
            b_data = dict(record["b"])
            a_type = record["a_labels"][0] if record["a_labels"] else "Unknown"
            b_type = record["b_labels"][0] if record["b_labels"] else "Unknown"
            source = _get_node_id(a_data, a_type)
            target = _get_node_id(b_data, b_type)
            if source in node_ids and target in node_ids:
                edges.append({"data": {"source": source, "target": target, "type": record["rel_type"]}})

    return jsonify({"nodes": nodes, "edges": edges})


@app.route('/api/graph/cypher', methods=['POST'])
def api_graph_cypher():
    """Execute a read-only Cypher query and return nodes/edges."""
    c = get_core()
    query = request.json.get('query', '').strip()
    if not query:
        return jsonify({"error": "No query provided"}), 400

    # Safety: only allow read operations
    query_upper = query.upper().strip()
    if not query_upper.startswith("MATCH") and not query_upper.startswith("OPTIONAL"):
        return jsonify({"error": "Only MATCH queries are allowed"}), 403

    try:
        records, _, _ = c.driver.execute_query(query)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    nodes = []
    edges = []
    node_ids = set()

    for record in records:
        for value in record.values():
            # Handle Node objects
            if hasattr(value, 'labels'):
                node_data = dict(value)
                node_type = list(value.labels)[0] if value.labels else "Unknown"
                node_id = _get_node_id(node_data, node_type)
                if node_id not in node_ids:
                    node_ids.add(node_id)
                    nodes.append({
                        "data": {
                            "id": node_id,
                            "label": _get_node_label(node_data, node_type),
                            "type": node_type,
                            **node_data
                        }
                    })

    return jsonify({"nodes": nodes, "edges": edges})


@app.route('/api/graph/reset', methods=['POST'])
def api_graph_reset():
    """Delete all nodes and relationships from Neo4j."""
    c = get_core()
    c.driver.execute_query("MATCH (n) DETACH DELETE n")
    return jsonify({"status": "ok", "message": "All nodes and relationships deleted."})


def _get_node_id(data, node_type):
    """Extract a unique ID from node properties based on type."""
    if node_type == "Paper":
        return data.get("PaperId", "")
    elif node_type == "Author":
        return data.get("AuthorId", "")
    elif node_type == "Venue":
        return "venue:" + data.get("Name", "")
    elif node_type == "Keyword":
        return "kw:" + data.get("Value", "")
    elif node_type == "Tag":
        return "tag:" + data.get("Tag", "")
    return str(hash(frozenset(data.items())))


def _get_node_label(data, node_type):
    """Get a display label for a node."""
    if node_type == "Paper":
        title = data.get("Title", "Untitled")
        return title[:40] + "..." if len(title) > 40 else title
    elif node_type == "Author":
        return data.get("Name", "Unknown")
    elif node_type == "Venue":
        return data.get("Name", "Unknown")
    elif node_type == "Keyword":
        return data.get("Value", "")
    elif node_type == "Tag":
        return data.get("Tag", "")
    return "?"


@socketio.on('connect')
def on_connect():
    global handler
    try:
        c = get_core()
        handler = CommandHandler(c)
        emit('output', {'data': '\x1b[32mConnected to backend.\x1b[0m'})
        emit('output', {'data': 'Type \x1b[33mhelp\x1b[0m for available commands.'})
        emit('done')
    except Exception as e:
        emit('output', {'data': f'\x1b[31mBackend error: {e}\x1b[0m'})
        emit('done')


@socketio.on('command')
def on_command(data):
    global handler
    command = data.get('command', '').strip()
    if not command:
        return

    def send_output(text):
        emit('output', {'data': text})
        socketio.sleep(0)  # Yield to event loop so message flushes immediately

    try:
        handler.handle(command, send_output)
    except Exception as e:
        emit('output', {'data': f'\x1b[31mError: {e}\x1b[0m'})
    finally:
        emit('done')


if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
