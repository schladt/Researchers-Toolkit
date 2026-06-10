// app.js — Main entry point, wires everything together

document.addEventListener('DOMContentLoaded', function () {
    // Initialize panels
    initGraph();
    initTerminal();

    // Resizable divider
    initDivider();

    // Graph search bar
    initGraphSearch();

    // Layout switcher + export
    initGraphControls();

    // Always start with 10-node preview
    localStorage.removeItem('rtk-graph');
    loadPreview();

    // Styled tooltips for toolbar buttons
    initToolbarTooltips();

    // Handle window resize
    window.addEventListener('resize', function () {
        fitTerminal();
        if (cy) cy.resize();
    });
});

// Styled tooltips for toolbar buttons (uses title attr)
function initToolbarTooltips() {
    var tip = null;
    var buttons = document.querySelectorAll('.toolbar-btn[title]');
    buttons.forEach(function (btn) {
        var text = btn.getAttribute('title');
        btn.removeAttribute('title');
        btn.dataset.tip = text;
        btn.addEventListener('mouseenter', function (e) {
            if (tip) tip.remove();
            tip = document.createElement('div');
            tip.className = 'graph-tooltip';
            tip.textContent = text;
            document.body.appendChild(tip);
            var rect = btn.getBoundingClientRect();
            tip.style.left = rect.left + 'px';
            tip.style.top = (rect.bottom + 6) + 'px';
        });
        btn.addEventListener('mouseleave', function () {
            if (tip) { tip.remove(); tip = null; }
        });
    });
}

// Draggable divider for resizing panels
function initDivider() {
    const divider = document.getElementById('divider');
    const container = document.getElementById('container');
    const graphPanel = document.getElementById('graph-panel');
    const consolePanel = document.getElementById('console-panel');

    let isDragging = false;

    divider.addEventListener('mousedown', function (e) {
        isDragging = true;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
    });

    document.addEventListener('mousemove', function (e) {
        if (!isDragging) return;

        const containerRect = container.getBoundingClientRect();
        const offsetX = e.clientX - containerRect.left;
        const totalWidth = containerRect.width;

        // Clamp between 20% and 80%
        const ratio = Math.max(0.2, Math.min(0.8, offsetX / totalWidth));

        consolePanel.style.flex = 'none';
        consolePanel.style.width = (ratio * 100) + '%';
        graphPanel.style.flex = 'none';
        graphPanel.style.width = ((1 - ratio) * 100 - 0.5) + '%';

        fitTerminal();
        if (cy) cy.resize();
    });

    document.addEventListener('mouseup', function () {
        if (isDragging) {
            isDragging = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });
}

// Graph search bar + Cypher mode
function initGraphSearch() {
    var searchInput = document.getElementById('search-input');
    var searchBtn = document.getElementById('search-btn');
    var cypherToggle = document.getElementById('cypher-toggle');
    var cypherBar = document.getElementById('cypher-bar');
    var cypherInput = document.getElementById('cypher-input');
    var cypherRun = document.getElementById('cypher-run');
    var clearBtn = document.getElementById('clear-btn');
    var legendToggle = document.getElementById('legend-toggle');
    var legend = document.getElementById('graph-legend');
    var viewToggle = document.getElementById('view-toggle');
    var graphContainer = document.getElementById('graph-container');
    var tableView = document.getElementById('table-view');

    // Search on Enter or click
    searchBtn.addEventListener('click', function () {
        graphSearch(searchInput.value);
    });
    searchInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            graphSearch(searchInput.value);
        }
    });

    // Toggle Cypher bar
    cypherToggle.addEventListener('click', function () {
        cypherBar.classList.toggle('hidden');
        cypherToggle.classList.toggle('active');
        if (!cypherBar.classList.contains('hidden')) {
            cypherInput.focus();
        }
    });

    // Toggle legend
    legendToggle.addEventListener('click', function () {
        legend.classList.toggle('hidden');
        legendToggle.classList.toggle('active');
    });

    // Toggle graph/table view
    viewToggle.addEventListener('click', function () {
        tableView.classList.toggle('hidden');
        graphContainer.classList.toggle('hidden');
        viewToggle.classList.toggle('active');
        if (!graphContainer.classList.contains('hidden') && cy) {
            cy.resize();
        }
        if (!tableView.classList.contains('hidden')) {
            populateTable();
        }
    });

    // Run Cypher
    cypherRun.addEventListener('click', function () {
        runCypher(cypherInput.value);
    });
    cypherInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            runCypher(cypherInput.value);
        }
    });

    // Clear button
    clearBtn.addEventListener('click', function () {
        cy.elements().remove();
        localStorage.removeItem('rtk-graph');
        updateGraphInfo();
    });
}

function graphSearch(query) {
    query = query.trim();
    if (!query) return;

    fetch('/api/graph/search?q=' + encodeURIComponent(query))
        .then(function (res) { return res.json(); })
        .then(function (data) {
            if (data.nodes.length === 0) {
                if (term) {
                    term.write('\r\n\x1b[33mNo nodes found for "' + query + '"\x1b[0m\r\n');
                    showPrompt();
                }
                return;
            }
            // Replace current view with search results
            cy.elements().remove();
            hideGraphBanner();
            cy.add(data.nodes);
            cy.add(data.edges);
            runLayout();
            updateGraphInfo();

            if (term) {
                term.write('\r\n\x1b[32mFound ' + data.nodes.length + ' nodes for "' + query + '"\x1b[0m\r\n');
                showPrompt();
            }
        })
        .catch(function (err) {
            if (term) {
                term.write('\r\n\x1b[31mSearch error: ' + err + '\x1b[0m\r\n');
                showPrompt();
            }
        });
}

function runCypher(query) {
    query = query.trim();
    if (!query) return;

    fetch('/api/graph/cypher', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })
    })
        .then(function (res) { return res.json(); })
        .then(function (data) {
            if (data.error) {
                if (term) {
                    term.write('\r\n\x1b[31mCypher error: ' + data.error + '\x1b[0m\r\n');
                    showPrompt();
                }
                return;
            }
            // Replace current view with cypher results
            cy.elements().remove();
            hideGraphBanner();
            cy.add(data.nodes);
            if (data.edges) cy.add(data.edges);
            runLayout();
            updateGraphInfo();

            if (term) {
                term.write('\r\n\x1b[32mCypher returned ' + data.nodes.length + ' nodes\x1b[0m\r\n');
                showPrompt();
            }
        })
        .catch(function (err) {
            if (term) {
                term.write('\r\n\x1b[31mCypher error: ' + err + '\x1b[0m\r\n');
                showPrompt();
            }
        });
}

function updateGraphInfo() {
    var info = document.getElementById('graph-info');
    if (info && cy) {
        var nodes = cy.nodes().length;
        var edges = cy.edges().length;
        info.textContent = nodes + ' nodes, ' + edges + ' edges';
    }
    // Keep table in sync if it's currently visible
    var tableView = document.getElementById('table-view');
    if (tableView && !tableView.classList.contains('hidden')) {
        populateTable();
    }
}

// --- Layout Switcher + Export ---

function initGraphControls() {
    var layoutSelect = document.getElementById('layout-select');
    var exportBtn = document.getElementById('export-btn');

    layoutSelect.addEventListener('change', function () {
        runLayoutWithName(layoutSelect.value);
    });

    exportBtn.addEventListener('click', function () {
        exportGraph();
    });
}

function runLayoutWithName(name) {
    if (!cy || cy.nodes().length === 0) return;

    var opts = { name: name, animate: true, animationDuration: 500, padding: 30 };

    // Layout-specific options
    if (name === 'cose') {
        opts.nodeRepulsion = function () { return 8000; };
        opts.idealEdgeLength = function () { return 80; };
        opts.gravity = 0.3;
        opts.numIter = 300;
    } else if (name === 'breadthfirst') {
        opts.directed = true;
        opts.spacingFactor = 1.2;
    } else if (name === 'concentric') {
        opts.concentric = function (node) {
            return node.degree();
        };
        opts.levelWidth = function () { return 2; };
    }

    cy.layout(opts).run();
}

function exportGraph() {
    if (!cy || cy.nodes().length === 0) return;

    var png = cy.png({ full: true, scale: 2, bg: '#1a1a1a' });
    var link = document.createElement('a');
    link.href = png;
    link.download = 'graph-export.png';
    link.click();
}

// --- LocalStorage Persistence ---

function saveGraph() {
    // No-op: we always start fresh with preview
}

function loadPreview() {
    fetch('/api/graph?limit=10')
        .then(function (res) { return res.json(); })
        .then(function (data) {
            if (data.nodes.length > 0) {
                cy.add(data.nodes);
                cy.add(data.edges);
                runLayout();
                updateGraphInfo();
                showGraphBanner();
            }
        });
}

function showGraphBanner() {
    var existing = document.getElementById('graph-banner');
    if (existing) return;
    var banner = document.createElement('div');
    banner.id = 'graph-banner';
    banner.innerHTML = 'Showing a preview (10 nodes). <strong>Search</strong> or <strong>double-click</strong> nodes to expand.';
    banner.addEventListener('click', function () { banner.remove(); });
    document.getElementById('graph-container').appendChild(banner);
}

function hideGraphBanner() {
    var banner = document.getElementById('graph-banner');
    if (banner) banner.remove();
}

// --- Table View ---

function populateTable() {
    var container = document.getElementById('table-container');
    var placeholder = document.getElementById('table-placeholder');

    if (!cy || cy.nodes().length === 0) {
        placeholder.style.display = '';
        container.innerHTML = '';
        return;
    }
    placeholder.style.display = 'none';

    // Check if this is preview state (banner still showing)
    var isPreview = !!document.getElementById('graph-banner');

    // Group nodes by type
    var groups = {};
    cy.nodes().forEach(function (node) {
        var data = node.data();
        var type = data.type || 'Other';
        if (!groups[type]) groups[type] = [];
        groups[type].push(data);
    });

    var html = '';
    if (isPreview) {
        html += '<div class="table-banner">Showing a preview (10 nodes). Search or double-click nodes in the graph to load more.</div>';
    }
    var typeOrder = ['Paper', 'Author', 'Venue', 'Keyword', 'Tag'];
    typeOrder.forEach(function (type) {
        if (!groups[type] || groups[type].length === 0) return;
        html += renderTypeTable(type, groups[type]);
    });
    // Render any remaining types
    Object.keys(groups).forEach(function (type) {
        if (typeOrder.indexOf(type) === -1) {
            html += renderTypeTable(type, groups[type]);
        }
    });

    container.innerHTML = html;
}

function renderTypeTable(type, nodes) {
    var html = '<div class="table-section">';
    html += '<h3 class="table-type-header table-type-' + type.toLowerCase() + '">' + type + 's (' + nodes.length + ')</h3>';
    html += '<table class="node-table"><thead><tr>';

    if (type === 'Paper') {
        html += '<th>Title</th><th>Author</th><th>Year</th><th>Venue</th><th>Citations</th><th>TLDR</th><th>URL</th>';
        html += '</tr></thead><tbody>';
        nodes.sort(function (a, b) { return (b.Year || 0) - (a.Year || 0); });
        nodes.forEach(function (d) {
            html += '<tr>';
            html += '<td class="td-title">' + escapeHtml(d.Title || d.label || '') + '</td>';
            html += '<td>' + escapeHtml(d.PrimaryAuthor || '') + '</td>';
            html += '<td>' + (d.Year || '') + '</td>';
            html += '<td>' + escapeHtml(d.Venue || '') + '</td>';
            html += '<td>' + (d.CitationCount !== undefined ? d.CitationCount : '') + '</td>';
            html += '<td class="td-tldr">' + escapeHtml(d.TLDR || '') + '</td>';
            html += '<td>' + (d.URL ? '<a href="' + escapeHtml(d.URL) + '" target="_blank" rel="noopener">link</a>' : '') + '</td>';
            html += '</tr>';
        });
    } else if (type === 'Author') {
        html += '<th>Name</th><th>ID</th>';
        html += '</tr></thead><tbody>';
        nodes.sort(function (a, b) { return (a.Name || a.label || '').localeCompare(b.Name || b.label || ''); });
        nodes.forEach(function (d) {
            html += '<tr>';
            html += '<td>' + escapeHtml(d.Name || d.label || '') + '</td>';
            html += '<td class="td-id">' + escapeHtml(d.id || '') + '</td>';
            html += '</tr>';
        });
    } else if (type === 'Venue') {
        html += '<th>Name</th>';
        html += '</tr></thead><tbody>';
        nodes.sort(function (a, b) { return (a.Name || a.label || '').localeCompare(b.Name || b.label || ''); });
        nodes.forEach(function (d) {
            html += '<tr>';
            html += '<td>' + escapeHtml(d.Name || d.label || '') + '</td>';
            html += '</tr>';
        });
    } else if (type === 'Keyword') {
        html += '<th>Keyword</th>';
        html += '</tr></thead><tbody>';
        nodes.sort(function (a, b) { return (a.Name || a.label || a.id || '').localeCompare(b.Name || b.label || b.id || ''); });
        nodes.forEach(function (d) {
            html += '<tr>';
            html += '<td>' + escapeHtml(d.Name || d.label || d.id || '') + '</td>';
            html += '</tr>';
        });
    } else if (type === 'Tag') {
        html += '<th>Tag</th>';
        html += '</tr></thead><tbody>';
        nodes.forEach(function (d) {
            html += '<tr>';
            html += '<td>' + escapeHtml(d.Tag || d.label || '') + '</td>';
            html += '</tr>';
        });
    } else {
        html += '<th>Label</th><th>ID</th>';
        html += '</tr></thead><tbody>';
        nodes.forEach(function (d) {
            html += '<tr>';
            html += '<td>' + escapeHtml(d.label || '') + '</td>';
            html += '<td class="td-id">' + escapeHtml(d.id || '') + '</td>';
            html += '</tr>';
        });
    }

    html += '</tbody></table></div>';
    return html;
}
