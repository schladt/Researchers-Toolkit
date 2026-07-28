// graph.js — Cytoscape.js initialization and graph rendering

let cy = null;

function initGraph() {
    cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            // Default node style (MUST come first — Cytoscape ignores specificity, last matching selector wins)
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'color': '#d4d4d4',
                    'font-size': '8px',
                    'text-valign': 'bottom',
                    'text-margin-y': 5,
                    'text-outline-width': 2,
                    'text-outline-color': '#1a1a1a',
                    'background-color': '#666',
                    'width': 18,
                    'height': 18,
                    'overlay-opacity': 0
                }
            },
            // Paper nodes - blue
            {
                selector: 'node[type="Paper"]',
                style: {
                    'label': 'data(label)',
                    'color': '#e0e6ed',
                    'font-size': '8px',
                    'text-valign': 'bottom',
                    'text-margin-y': 5,
                    'text-wrap': 'ellipsis',
                    'text-max-width': '90px',
                    'text-outline-width': 2,
                    'text-outline-color': '#1a1a1a',
                    'background-color': '#5b9bd5',
                    'border-width': 2,
                    'border-color': '#7bb3e0',
                    'shape': 'ellipse',
                    'width': 28,
                    'height': 28,
                    'overlay-opacity': 0
                }
            },
            // Author nodes - teal
            {
                selector: 'node[type="Author"]',
                style: {
                    'label': 'data(label)',
                    'color': '#e0e6ed',
                    'font-size': '8px',
                    'text-valign': 'bottom',
                    'text-margin-y': 5,
                    'text-outline-width': 2,
                    'text-outline-color': '#1a1a1a',
                    'background-color': '#4db6ac',
                    'border-width': 2,
                    'border-color': '#6ec8be',
                    'shape': 'diamond',
                    'width': 22,
                    'height': 22,
                    'overlay-opacity': 0
                }
            },
            // Venue nodes - gold
            {
                selector: 'node[type="Venue"]',
                style: {
                    'label': 'data(label)',
                    'color': '#e0e6ed',
                    'font-size': '7px',
                    'text-valign': 'bottom',
                    'text-margin-y': 5,
                    'text-wrap': 'ellipsis',
                    'text-max-width': '80px',
                    'text-outline-width': 2,
                    'text-outline-color': '#1a1a1a',
                    'background-color': '#e8a838',
                    'border-width': 2,
                    'border-color': '#f0c060',
                    'shape': 'round-rectangle',
                    'width': 20,
                    'height': 20,
                    'overlay-opacity': 0
                }
            },
            // Keyword nodes - slate (no label)
            {
                selector: 'node[type="Keyword"]',
                style: {
                    'label': '',
                    'background-color': '#607d8b',
                    'border-width': 1,
                    'border-color': '#78909c',
                    'shape': 'ellipse',
                    'width': 8,
                    'height': 8,
                    'overlay-opacity': 0
                }
            },
            // Tag nodes - purple
            {
                selector: 'node[type="Tag"]',
                style: {
                    'label': 'data(label)',
                    'color': '#e0e6ed',
                    'font-size': '8px',
                    'text-valign': 'bottom',
                    'text-margin-y': 5,
                    'text-outline-width': 2,
                    'text-outline-color': '#1a1a1a',
                    'background-color': '#9575cd',
                    'border-width': 2,
                    'border-color': '#b39ddb',
                    'shape': 'hexagon',
                    'width': 24,
                    'height': 24,
                    'overlay-opacity': 0
                }
            },
            // Selected node - bright white ring
            {
                selector: 'node:selected',
                style: {
                    'border-width': 3,
                    'border-color': '#ffffff',
                    'overlay-opacity': 0.08,
                    'overlay-color': '#ffffff'
                }
            },
            // Prevent edge click/active from showing labels
            {
                selector: 'edge:active',
                style: {
                    'font-size': '0px'
                }
            },
            {
                selector: 'edge:selected',
                style: {
                    'font-size': '0px'
                }
            },
            // Faded state for non-neighbors on select
            {
                selector: 'node.faded',
                style: {
                    'opacity': 0.15
                }
            },
            {
                selector: 'edge.faded',
                style: {
                    'opacity': 0.08
                }
            },
            // Highlighted neighbors
            {
                selector: 'node.highlighted',
                style: {
                    'opacity': 1,
                    'border-width': 2.5,
                    'border-color': '#ffffff'
                }
            },
            // Default edge style (MUST come before typed edges — last matching selector wins)
            {
                selector: 'edge',
                style: {
                    'width': 1,
                    'line-color': '#4a4a4a',
                    'target-arrow-color': '#4a4a4a',
                    'target-arrow-shape': 'none',
                    'curve-style': 'bezier',
                    'opacity': 0.5,
                    'label': 'data(type)',
                    'font-size': '0px',
                    'text-rotation': 'autorotate',
                    'color': '#888',
                    'text-opacity': 0.7,
                    'text-margin-y': -8
                }
            },
            // REFERENCES edges - directed arrows, blue-gray
            {
                selector: 'edge[type="REFERENCES"]',
                style: {
                    'width': 1.5,
                    'line-color': '#5580a8',
                    'target-arrow-color': '#5580a8',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'arrow-scale': 0.8,
                    'opacity': 0.7,
                    'label': 'data(type)',
                    'font-size': '0px',
                    'text-rotation': 'autorotate',
                    'color': '#5580a8',
                    'text-opacity': 0.8,
                    'text-margin-y': -8
                }
            },
            // AUTHORED_BY edges - teal dashed
            {
                selector: 'edge[type="AUTHORED_BY"]',
                style: {
                    'width': 1,
                    'line-color': '#4db6ac',
                    'line-style': 'dashed',
                    'target-arrow-shape': 'none',
                    'curve-style': 'bezier',
                    'opacity': 0.5,
                    'label': 'data(type)',
                    'font-size': '0px',
                    'text-rotation': 'autorotate',
                    'color': '#4db6ac',
                    'text-opacity': 0.7,
                    'text-margin-y': -8
                }
            },
            // PUBLISHED_IN edges - amber dotted
            {
                selector: 'edge[type="PUBLISHED_IN"]',
                style: {
                    'width': 1,
                    'line-color': '#e8a838',
                    'line-style': 'dotted',
                    'target-arrow-shape': 'none',
                    'curve-style': 'bezier',
                    'opacity': 0.5,
                    'label': 'data(type)',
                    'font-size': '0px',
                    'text-rotation': 'autorotate',
                    'color': '#e8a838',
                    'text-opacity': 0.7,
                    'text-margin-y': -8
                }
            }
        ],
        layout: { name: 'preset' },
        elements: [],
        minZoom: 0.1,
        maxZoom: 5
    });

    // Click node to show details in console + highlight neighborhood
    cy.on('tap', 'node', function (evt) {
        var node = evt.target;
        var data = node.data();
        showNodeDetails(data);

        // Fade all, highlight neighborhood
        var neighborhood = node.closedNeighborhood();
        cy.elements().addClass('faded');
        neighborhood.removeClass('faded');
        neighborhood.nodes().addClass('highlighted');
    });

    // Double-click to expand neighbors
    cy.on('dbltap', 'node', function (evt) {
        var node = evt.target;
        expandNeighbors(node.data().id);
    });

    // Right-click context menu
    cy.on('cxttap', 'node', function (evt) {
        evt.originalEvent.preventDefault();
        showContextMenu(evt.originalEvent, evt.target);
    });

    // Hide context menu on tap elsewhere + clear fading
    cy.on('tap', function (evt) {
        if (evt.target === cy) {
            hideContextMenu();
            cy.elements().removeClass('faded');
            cy.nodes().removeClass('highlighted');
        }
    });

    // Tooltip on hover
    cy.on('mouseover', 'node', function (evt) {
        showTooltip(evt);
    });
    cy.on('mouseout', 'node', function () {
        hideTooltip();
    });
    cy.on('drag', 'node', function () {
        hideTooltip();
    });
}

function loadGraph() {
    // Show stats first, warn if large
    fetch('/api/graph/stats')
        .then(function (res) { return res.json(); })
        .then(function (stats) {
            if (stats.total_nodes > 200) {
                term.write('\r\n\x1b[33mWarning: Database has ' + stats.total_nodes + ' nodes. Use the search bar to load specific nodes instead.\x1b[0m\r\n');
                term.write('Loading first 200 nodes...\r\n');
            } else {
                term.write('\r\n\x1b[36mDatabase: ' + stats.total_nodes + ' nodes, ' + stats.total_edges + ' edges\x1b[0m\r\n');
                term.write('Loading graph...\r\n');
            }
            return fetch('/api/graph');
        })
        .then(function (res) { return res.json(); })
        .then(function (data) {
            cy.elements().remove();
            cy.add(data.nodes);
            cy.add(data.edges);
            // Apply current edge label visibility
            if (edgeLabelsVisible) {
                cy.edges().style('font-size', '8px');
            }
            runLayout();
            updateGraphInfo();
            term.write('\x1b[32mRendered: ' + data.nodes.length + ' nodes, ' + data.edges.length + ' edges.\x1b[0m\r\n');
            showPrompt();
        })
        .catch(function (err) {
            term.write('\r\n\x1b[31mFailed to load graph: ' + err + '\x1b[0m\r\n');
            showPrompt();
        });
}

function clearGraph() {
    cy.elements().remove();
    updateGraphInfo();
    if (term) {
        term.write('\r\n\x1b[32mGraph cleared.\x1b[0m\r\n');
        showPrompt();
    }
}

function expandNeighbors(nodeId) {
    fetch('/api/graph/neighbors/' + encodeURIComponent(nodeId))
        .then(function (res) { return res.json(); })
        .then(function (data) {
            // Add only new nodes
            var existingIds = new Set(cy.nodes().map(function (n) { return n.id(); }));
            var newNodes = data.nodes.filter(function (n) { return !existingIds.has(n.data.id); });
            hideGraphBanner();
            cy.add(newNodes);

            // Add only new edges (dedup by source+target+type)
            var existingEdges = new Set();
            cy.edges().forEach(function (e) {
                existingEdges.add(e.data('source') + '|' + e.data('target') + '|' + e.data('type'));
            });
            var newEdges = data.edges.filter(function (e) {
                var key = e.data.source + '|' + e.data.target + '|' + e.data.type;
                if (existingEdges.has(key)) return false;
                // Only add edges where both endpoints exist
                return cy.getElementById(e.data.source).length > 0 &&
                       cy.getElementById(e.data.target).length > 0;
            });
            cy.add(newEdges);
            // Apply current edge label visibility to new edges
            if (edgeLabelsVisible) {
                cy.edges().style('font-size', '8px');
            }
            runLayout();
            updateGraphInfo();
        });
}

function runLayout() {
    var name = document.getElementById('layout-select').value || 'fcose';
    runLayoutWithName(name);
}

function showNodeDetails(data) {
    if (!term) return;

    var type = data.type || 'Unknown';
    term.write('\r\n');

    if (type === 'Paper') {
        term.write('\x1b[1;36m' + (data.Title || data.label) + '\x1b[0m\r\n');
        if (data.PrimaryAuthor) term.write('  Author: ' + data.PrimaryAuthor + '\r\n');
        if (data.Year) term.write('  Year: ' + data.Year + '\r\n');
        if (data.Venue) term.write('  Venue: ' + data.Venue + '\r\n');
        if (data.CitationCount !== undefined) term.write('  Citations: ' + data.CitationCount + '\r\n');
        if (data.TLDR) term.write('  TLDR: ' + data.TLDR + '\r\n');
        if (data.URL) term.write('  URL: ' + data.URL + '\r\n');
        term.write('  ID: ' + data.id + '\r\n');
    } else if (type === 'Author') {
        term.write('\x1b[1;32m' + (data.Name || data.label) + '\x1b[0m\r\n');
        term.write('  ID: ' + data.id + '\r\n');
    } else if (type === 'Venue') {
        term.write('\x1b[1;33m' + (data.Name || data.label) + '\x1b[0m\r\n');
    } else if (type === 'Tag') {
        term.write('\x1b[1;35m' + (data.Tag || data.label) + '\x1b[0m\r\n');
    } else {
        term.write('\x1b[36m' + data.label + '\x1b[0m (' + type + ')\r\n');
    }

    showPrompt();
}

function showGraphStats() {
    fetch('/api/graph/stats')
        .then(function (res) { return res.json(); })
        .then(function (data) {
            term.write('\r\n\x1b[1;36mDatabase Statistics\x1b[0m\r\n');
            term.write('  Total nodes: ' + data.total_nodes + '\r\n');
            term.write('  Total edges: ' + data.total_edges + '\r\n');
            term.write('\r\n  Nodes by type:\r\n');
            Object.entries(data.node_counts).forEach(function (entry) {
                term.write('    ' + entry[0] + ': ' + entry[1] + '\r\n');
            });
            term.write('\r\n  Edges by type:\r\n');
            Object.entries(data.edge_counts).forEach(function (entry) {
                term.write('    ' + entry[0] + ': ' + entry[1] + '\r\n');
            });
            term.write('\r\n');
            showPrompt();
        })
        .catch(function (err) {
            term.write('\r\n\x1b[31mFailed to get stats: ' + err + '\x1b[0m\r\n');
            showPrompt();
        });
}

function resetGraph() {
    if (!confirm('Are you sure you want to DELETE ALL data from the database? This cannot be undone.')) {
        term.write('\r\nCancelled.\r\n');
        showPrompt();
        return;
    }

    fetch('/api/graph/reset', { method: 'POST' })
        .then(function (res) { return res.json(); })
        .then(function (data) {
            cy.elements().remove();
            term.write('\r\n\x1b[32m' + data.message + '\x1b[0m\r\n');
            showPrompt();
        })
        .catch(function (err) {
            term.write('\r\n\x1b[31mFailed to reset: ' + err + '\x1b[0m\r\n');
            showPrompt();
        });
}

// --- Context Menu ---

function showContextMenu(event, node) {
    hideContextMenu();
    var data = node.data();
    var type = data.type || 'Unknown';

    var menu = document.createElement('div');
    menu.id = 'context-menu';
    menu.className = 'context-menu';

    var items = [];

    // Type-specific items
    if (type === 'Paper') {
        items.push({ label: 'Expand neighbors', action: function () { expandNeighbors(data.id); } });
        items.push({ label: 'Show details', action: function () { showNodeDetails(data); } });
        if (data.URL) {
            items.push({ label: 'Open in browser', action: function () { window.open(data.URL, '_blank'); } });
        }
    } else if (type === 'Author') {
        items.push({ label: 'Expand papers', action: function () { expandNeighbors(data.id); } });
        items.push({ label: 'Show details', action: function () { showNodeDetails(data); } });
    } else {
        items.push({ label: 'Expand neighbors', action: function () { expandNeighbors(data.id); } });
    }

    // Common items
    items.push({ label: 'Select neighbors', action: function () {
        node.neighborhood().nodes().select();
    }});
    items.push({ label: 'Remove from view', action: function () {
        node.remove();
        updateGraphInfo();
    }});
    items.push({ label: 'Remove all others', action: function () {
        cy.nodes().filter(function (n) { return n.id() !== data.id; }).remove();
        updateGraphInfo();
    }});
    items.push({ label: 'Remove disconnected', action: function () {
        cy.nodes().filter(function (n) { return n.degree() === 0 && n.id() !== data.id; }).remove();
        updateGraphInfo();
    }});

    items.forEach(function (item) {
        var el = document.createElement('div');
        el.className = 'context-menu-item';
        el.textContent = item.label;
        el.addEventListener('click', function () {
            hideContextMenu();
            item.action();
        });
        menu.appendChild(el);
    });

    // Position menu at cursor
    menu.style.left = event.clientX + 'px';
    menu.style.top = event.clientY + 'px';
    document.body.appendChild(menu);

    // Close on click outside
    setTimeout(function () {
        document.addEventListener('click', hideContextMenuOnClick);
    }, 0);
}

function hideContextMenu() {
    var menu = document.getElementById('context-menu');
    if (menu) menu.remove();
    document.removeEventListener('click', hideContextMenuOnClick);
}

function hideContextMenuOnClick(e) {
    if (!e.target.closest('.context-menu')) {
        hideContextMenu();
    }
}

// --- Tooltip ---

function showTooltip(evt) {
    hideTooltip();
    var node = evt.target;
    var data = node.data();
    var type = data.type || 'Unknown';

    var tip = document.createElement('div');
    tip.id = 'graph-tooltip';
    tip.className = 'graph-tooltip';

    var lines = [];
    if (type === 'Paper') {
        lines.push('<strong>' + escapeHtml(data.Title || data.label) + '</strong>');
        if (data.PrimaryAuthor) lines.push('<span class="tip-dim">by</span> ' + escapeHtml(data.PrimaryAuthor));
        if (data.Year) lines.push('<span class="tip-dim">Year:</span> ' + data.Year);
        if (data.CitationCount !== undefined) lines.push('<span class="tip-dim">Citations:</span> ' + data.CitationCount);
        if (data.ReferenceCount !== undefined) lines.push('<span class="tip-dim">References:</span> ' + data.ReferenceCount);
        lines.push('<span class="tip-dim">Connections:</span> ' + node.degree());
    } else if (type === 'Author') {
        lines.push('<strong>' + escapeHtml(data.Name || data.label) + '</strong>');
        lines.push('<span class="tip-dim">Papers in graph:</span> ' + node.degree());
    } else if (type === 'Venue') {
        lines.push('<strong>' + escapeHtml(data.Name || data.label) + '</strong>');
        lines.push('<span class="tip-dim">Papers in graph:</span> ' + node.degree());
    } else if (type === 'Keyword') {
        lines.push(escapeHtml(data.Value || data.label || data.id));
        lines.push('<span class="tip-dim">Keyword</span>');
    } else if (type === 'Tag') {
        lines.push('<strong>' + escapeHtml(data.Tag || data.label) + '</strong>');
        lines.push('<span class="tip-dim">Tag • ' + node.degree() + ' items</span>');
    } else {
        lines.push(escapeHtml(data.label || data.id));
    }

    tip.innerHTML = lines.join('<br>');

    // Position near the node
    var renderedPos = node.renderedPosition();
    var cyContainer = document.getElementById('cy');
    var rect = cyContainer.getBoundingClientRect();
    tip.style.left = (rect.left + renderedPos.x + 15) + 'px';
    tip.style.top = (rect.top + renderedPos.y - 10) + 'px';

    document.body.appendChild(tip);
}

function hideTooltip() {
    var tip = document.getElementById('graph-tooltip');
    if (tip) tip.remove();
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// --- Edge label toggle ---

var edgeLabelsVisible = false;

function toggleEdgeLabels() {
    edgeLabelsVisible = !edgeLabelsVisible;
    if (!cy) return;
    cy.edges().style('font-size', edgeLabelsVisible ? '8px' : '0px');
}

// --- Node sizing toggle ---
// Modes: 'fixed' (default), 'citations', 'connections'
var nodeSizeMode = 'fixed';

function cycleNodeSizeMode() {
    if (nodeSizeMode === 'fixed') {
        nodeSizeMode = 'citations';
    } else if (nodeSizeMode === 'citations') {
        nodeSizeMode = 'connections';
    } else {
        nodeSizeMode = 'fixed';
    }
    applyNodeSizing();
    return nodeSizeMode;
}

function applyNodeSizing() {
    if (!cy) return;

    cy.nodes().forEach(function (node) {
        var type = node.data('type');
        var size;

        if (nodeSizeMode === 'fixed') {
            // Reset to defaults
            if (type === 'Paper') size = 28;
            else if (type === 'Author') size = 22;
            else if (type === 'Venue') size = 20;
            else if (type === 'Keyword') size = 8;
            else if (type === 'Tag') size = 24;
            else size = 18;
        } else if (nodeSizeMode === 'citations') {
            var citations = node.data('CitationCount') || 0;
            if (type === 'Paper') {
                // Map citations: 0 -> 16, 500+ -> 60
                size = Math.min(60, Math.max(16, 16 + Math.sqrt(citations) * 2));
            } else {
                // Non-papers: size by degree
                size = Math.min(40, Math.max(12, 12 + node.degree() * 2));
            }
        } else if (nodeSizeMode === 'connections') {
            var deg = node.degree();
            size = Math.min(55, Math.max(12, 12 + deg * 3.5));
        }

        node.style({ 'width': size, 'height': size });
    });
}

// --- Fade on select (highlight neighborhood) ---
// Integrated into initGraph tap handlers above.
