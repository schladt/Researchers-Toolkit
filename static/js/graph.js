// graph.js — Cytoscape.js initialization and graph rendering

let cy = null;

function initGraph() {
    cy = cytoscape({
        container: document.getElementById('cy'),
        style: [
            // Paper nodes - soft blue
            {
                selector: 'node[type="Paper"]',
                style: {
                    'label': 'data(label)',
                    'color': '#c8d0dc',
                    'font-size': '10px',
                    'text-valign': 'bottom',
                    'text-margin-y': 5,
                    'text-wrap': 'ellipsis',
                    'text-max-width': '80px',
                    'background-color': '#5b9bd5',
                    'border-width': 1.5,
                    'border-color': '#7bb8e8',
                    'shape': 'ellipse',
                    'width': 28,
                    'height': 28
                }
            },
            // Author nodes - teal
            {
                selector: 'node[type="Author"]',
                style: {
                    'label': 'data(label)',
                    'color': '#c8d0dc',
                    'font-size': '10px',
                    'text-valign': 'bottom',
                    'text-margin-y': 5,
                    'background-color': '#4db6ac',
                    'border-width': 1.5,
                    'border-color': '#80cbc4',
                    'shape': 'diamond',
                    'width': 24,
                    'height': 24
                }
            },
            // Venue nodes - warm amber
            {
                selector: 'node[type="Venue"]',
                style: {
                    'label': 'data(label)',
                    'color': '#c8d0dc',
                    'font-size': '9px',
                    'text-valign': 'bottom',
                    'text-margin-y': 5,
                    'text-wrap': 'ellipsis',
                    'text-max-width': '70px',
                    'background-color': '#e8a838',
                    'border-width': 1.5,
                    'border-color': '#f0c060',
                    'shape': 'round-rectangle',
                    'width': 22,
                    'height': 22
                }
            },
            // Keyword nodes - muted slate
            {
                selector: 'node[type="Keyword"]',
                style: {
                    'label': '',
                    'background-color': '#607d8b',
                    'border-width': 1,
                    'border-color': '#78909c',
                    'shape': 'ellipse',
                    'width': 10,
                    'height': 10
                }
            },
            // Tag nodes - soft purple
            {
                selector: 'node[type="Tag"]',
                style: {
                    'label': 'data(label)',
                    'color': '#c8d0dc',
                    'font-size': '10px',
                    'text-valign': 'bottom',
                    'text-margin-y': 5,
                    'background-color': '#9575cd',
                    'border-width': 1.5,
                    'border-color': '#b39ddb',
                    'shape': 'hexagon',
                    'width': 26,
                    'height': 26
                }
            },
            // Default node style
            {
                selector: 'node',
                style: {
                    'label': 'data(label)',
                    'color': '#d4d4d4',
                    'font-size': '10px',
                    'text-valign': 'bottom',
                    'text-margin-y': 5,
                    'background-color': '#666',
                    'width': 20,
                    'height': 20
                }
            },
            // Selected node
            {
                selector: 'node:selected',
                style: {
                    'border-width': 3,
                    'border-color': '#ffffff'
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
                    'opacity': 0.7
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
                    'opacity': 0.5
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
                    'opacity': 0.5
                }
            },
            // Default edge style
            {
                selector: 'edge',
                style: {
                    'width': 1,
                    'line-color': '#4a4a4a',
                    'target-arrow-color': '#4a4a4a',
                    'target-arrow-shape': 'none',
                    'curve-style': 'bezier',
                    'opacity': 0.5
                }
            }
        ],
        layout: { name: 'preset' },
        elements: [],
        minZoom: 0.1,
        maxZoom: 5
    });

    // Click node to show details in console
    cy.on('tap', 'node', function (evt) {
        var node = evt.target;
        var data = node.data();
        showNodeDetails(data);
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

    // Hide context menu on tap elsewhere
    cy.on('tap', function (evt) {
        if (evt.target === cy) {
            hideContextMenu();
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
    localStorage.removeItem('rtk-graph');
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
            // Add only new elements
            var existingIds = new Set(cy.nodes().map(function (n) { return n.id(); }));
            var newNodes = data.nodes.filter(function (n) { return !existingIds.has(n.data.id); });
            hideGraphBanner();
            cy.add(newNodes);
            cy.add(data.edges.filter(function (e) {
                // Only add edges where both endpoints exist
                return cy.getElementById(e.data.source).length > 0 &&
                       cy.getElementById(e.data.target).length > 0;
            }));
            runLayout();
            updateGraphInfo();
        });
}

function runLayout() {
    var name = document.getElementById('layout-select').value || 'cose';
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
        if (data.PrimaryAuthor) lines.push(escapeHtml(data.PrimaryAuthor));
        if (data.Year) lines.push('Year: ' + data.Year);
        if (data.CitationCount !== undefined) lines.push('Citations: ' + data.CitationCount);
    } else if (type === 'Author') {
        lines.push('<strong>' + escapeHtml(data.Name || data.label) + '</strong>');
        lines.push('Author');
    } else if (type === 'Venue') {
        lines.push('<strong>' + escapeHtml(data.Name || data.label) + '</strong>');
        lines.push('Venue');
    } else if (type === 'Keyword') {
        lines.push(escapeHtml(data.Name || data.label || data.id));
        lines.push('Keyword');
    } else if (type === 'Tag') {
        lines.push('<strong>' + escapeHtml(data.Tag || data.label) + '</strong>');
        lines.push('Tag');
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
