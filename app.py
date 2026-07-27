import io
import json

from flask import Flask, render_template, jsonify, request, send_file
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
    limit = request.args.get('limit', 2000, type=int)
    nodes, edges = c.graph.get_all(limit=limit)
    return jsonify({"nodes": nodes, "edges": edges})


@app.route('/api/graph/neighbors/<path:node_id>')
def api_graph_neighbors(node_id):
    """Return neighbors of a given node."""
    c = get_core()
    nodes, edges = c.graph.get_neighbors(node_id, limit=100)
    return jsonify({"nodes": nodes, "edges": edges})


@app.route('/api/graph/stats')
def api_graph_stats():
    """Return node/edge counts by type."""
    c = get_core()
    return jsonify(c.graph.stats())


@app.route('/api/graph/search')
def api_graph_search():
    """Search nodes matching a query. Returns matched nodes + their direct edges."""
    c = get_core()
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({"nodes": [], "edges": []})
    nodes, edges = c.graph.search(q, limit=50)
    return jsonify({"nodes": nodes, "edges": edges})


@app.route('/api/graph/filter', methods=['POST'])
def api_graph_filter():
    """Filter graph nodes by type, year range, and text query."""
    c = get_core()
    filters = request.json or {}
    node_type = filters.get("type", "").strip()
    query = filters.get("query", "").strip().lower()
    year_min = filters.get("yearMin")
    year_max = filters.get("yearMax")

    matched_ids = set()
    nodes = []

    for node_id, props in c.graph.nodes.items():
        # Type filter
        if node_type and props.get("type") != node_type:
            continue
        # Year filter (only applies to Papers)
        if year_min is not None and props.get("type") == "Paper":
            if (props.get("Year") or 0) < year_min:
                continue
        if year_max is not None and props.get("type") == "Paper":
            if (props.get("Year") or 9999) > year_max:
                continue
        # Text query filter
        if query:
            searchable = " ".join(str(v) for v in props.values() if isinstance(v, str)).lower()
            if query not in searchable:
                continue

        matched_ids.add(node_id)
        nodes.append({
            "data": {
                "id": node_id,
                "label": c.graph._get_label(node_id, props),
                **props
            }
        })
        if len(nodes) >= 200:
            break

    # Edges between matched nodes
    edges = []
    for edge in c.graph.edges:
        if edge["source"] in matched_ids and edge["target"] in matched_ids:
            edges.append({"data": edge})

    return jsonify({"nodes": nodes, "edges": edges})


@app.route('/api/graph/reset', methods=['POST'])
def api_graph_reset():
    """Delete all nodes and relationships."""
    c = get_core()
    c.graph.clear()
    return jsonify({"status": "ok", "message": "All nodes and relationships deleted."})


@app.route('/api/graph/export')
def api_graph_export():
    """Export the graph as a downloadable JSON file."""
    c = get_core()
    data = json.dumps(c.graph.to_json(), indent=2)
    buf = io.BytesIO(data.encode('utf-8'))
    buf.seek(0)
    return send_file(buf, mimetype='application/json', as_attachment=True, download_name='rtk-graph.json')


@app.route('/api/graph/import', methods=['POST'])
def api_graph_import():
    """Import a graph from an uploaded JSON file."""
    c = get_core()
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    try:
        data = json.load(file)
        c.graph.from_json(data)
        stats = c.graph.stats()
        return jsonify({
            "status": "ok",
            "message": f"Imported {stats['total_nodes']} nodes and {stats['total_edges']} edges."
        })
    except (json.JSONDecodeError, KeyError) as e:
        return jsonify({"error": f"Invalid file format: {e}"}), 400


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
