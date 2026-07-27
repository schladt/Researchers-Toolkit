"""
graph_store.py — In-memory graph database with adjacency index.
Replaces Neo4j with Python dicts for zero-dependency local persistence.
Export/import via JSON files.
"""

import json


class GraphStore:
    """In-memory labeled property graph with adjacency index."""

    def __init__(self):
        self.nodes = {}        # {node_id: {type, ...properties}}
        self.edges = []        # [{source, target, type}]
        self._edge_set = set() # {(source, target, type)} for O(1) dedup
        self.adjacency = {}    # {node_id: [(neighbor_id, rel_type, direction)]}

    def merge_node(self, node_id, node_type, properties=None):
        """Insert or update a node. Returns True if newly created."""
        if properties is None:
            properties = {}
        created = node_id not in self.nodes
        if created:
            self.nodes[node_id] = {"type": node_type, **properties}
            self.adjacency.setdefault(node_id, [])
        else:
            # Update properties (preserve type)
            self.nodes[node_id].update(properties)
            self.nodes[node_id]["type"] = node_type
        return created

    def merge_edge(self, source_id, target_id, rel_type):
        """Insert an edge if it doesn't exist. Returns True if newly created."""
        edge_key = (source_id, target_id, rel_type)
        if edge_key in self._edge_set:
            return False

        self._edge_set.add(edge_key)
        self.edges.append({"source": source_id, "target": target_id, "type": rel_type})

        self.adjacency.setdefault(source_id, []).append((target_id, rel_type, "out"))
        self.adjacency.setdefault(target_id, []).append((source_id, rel_type, "in"))
        return True

    def get_node(self, node_id):
        """Get a node by ID. Returns dict or None."""
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id, limit=100):
        """Get neighbors of a node. Returns (nodes_list, edges_list) in Cytoscape format."""
        neighbors = self.adjacency.get(node_id, [])
        result_nodes = []
        result_edges = []

        for neighbor_id, rel_type, direction in neighbors[:limit]:
            neighbor = self.nodes.get(neighbor_id)
            if neighbor is None:
                continue

            result_nodes.append({
                "data": {
                    "id": neighbor_id,
                    "label": self._get_label(neighbor_id, neighbor),
                    **neighbor
                }
            })

            if direction == "out":
                result_edges.append({"data": {"source": node_id, "target": neighbor_id, "type": rel_type}})
            else:
                result_edges.append({"data": {"source": neighbor_id, "target": node_id, "type": rel_type}})

        return result_nodes, result_edges

    def get_all(self, limit=2000):
        """Get all nodes and edges in Cytoscape JSON format."""
        nodes = []
        for node_id, props in list(self.nodes.items())[:limit]:
            nodes.append({
                "data": {
                    "id": node_id,
                    "label": self._get_label(node_id, props),
                    **props
                }
            })

        node_ids = {n["data"]["id"] for n in nodes}
        edges = []
        for edge in self.edges:
            if edge["source"] in node_ids and edge["target"] in node_ids:
                edges.append({"data": edge})

        return nodes, edges

    def search(self, query, limit=50):
        """Search nodes by substring match on key properties. Returns (nodes, edges)."""
        query_lower = query.lower()
        matched_ids = set()
        nodes = []

        for node_id, props in self.nodes.items():
            if len(matched_ids) >= limit:
                break

            searchable = ""
            node_type = props.get("type", "")
            if node_type == "Paper":
                searchable = (props.get("Title", "") + " " + props.get("PrimaryAuthor", "")).lower()
            elif node_type == "Author":
                searchable = props.get("Name", "").lower()
            elif node_type == "Venue":
                searchable = props.get("Name", "").lower()
            elif node_type == "Keyword":
                searchable = props.get("Value", "").lower()
            elif node_type == "Tag":
                searchable = props.get("Tag", "").lower()

            if query_lower in searchable:
                matched_ids.add(node_id)
                nodes.append({
                    "data": {
                        "id": node_id,
                        "label": self._get_label(node_id, props),
                        **props
                    }
                })

        # Edges between matched nodes
        edges = []
        for edge in self.edges:
            if edge["source"] in matched_ids and edge["target"] in matched_ids:
                edges.append({"data": edge})

        return nodes, edges

    def stats(self):
        """Return node/edge counts by type."""
        node_counts = {}
        for props in self.nodes.values():
            t = props.get("type", "Unknown")
            node_counts[t] = node_counts.get(t, 0) + 1

        edge_counts = {}
        for edge in self.edges:
            t = edge["type"]
            edge_counts[t] = edge_counts.get(t, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_counts": node_counts,
            "edge_counts": edge_counts,
        }

    def clear(self):
        """Delete all data."""
        self.nodes.clear()
        self.edges.clear()
        self._edge_set.clear()
        self.adjacency.clear()

    def to_json(self):
        """Serialize graph to JSON-compatible dict."""
        return {
            "nodes": self.nodes,
            "edges": self.edges,
        }

    def from_json(self, data):
        """Load graph from JSON dict. Rebuilds adjacency index."""
        self.clear()
        self.nodes = data.get("nodes", {})
        self.edges = data.get("edges", [])
        self._rebuild_index()

    def export_file(self, filepath):
        """Export graph to a JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.to_json(), f, indent=2)

    def import_file(self, filepath):
        """Import graph from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        self.from_json(data)

    def _rebuild_index(self):
        """Rebuild adjacency index and edge set from edges list."""
        self._edge_set = set()
        self.adjacency = {}
        for node_id in self.nodes:
            self.adjacency.setdefault(node_id, [])
        for edge in self.edges:
            key = (edge["source"], edge["target"], edge["type"])
            self._edge_set.add(key)
            self.adjacency.setdefault(edge["source"], []).append(
                (edge["target"], edge["type"], "out")
            )
            self.adjacency.setdefault(edge["target"], []).append(
                (edge["source"], edge["type"], "in")
            )

    def _get_label(self, node_id, props):
        """Get display label for a node."""
        node_type = props.get("type", "")
        if node_type == "Paper":
            title = props.get("Title", "Untitled")
            return title[:40] + "..." if len(title) > 40 else title
        elif node_type == "Author":
            return props.get("Name", "Unknown")
        elif node_type == "Venue":
            return props.get("Name", "Unknown")
        elif node_type == "Keyword":
            return props.get("Value", "")
        elif node_type == "Tag":
            return props.get("Tag", "")
        return "?"
