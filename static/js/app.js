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

// --- Modal dialog utility ---
var pendingImportMode = 'replace';

function showModal(title, body, buttons) {
    var overlay = document.getElementById('modal-overlay');
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').textContent = body;
    var actions = document.getElementById('modal-actions');
    actions.innerHTML = '';
    buttons.forEach(function (btn) {
        var el = document.createElement('button');
        el.className = 'modal-btn' + (btn.primary ? ' primary' : '');
        el.textContent = btn.label;
        el.addEventListener('click', function () {
            overlay.classList.add('hidden');
            if (btn.action) btn.action();
        });
        actions.appendChild(el);
    });
    overlay.classList.remove('hidden');
}

function exportCurrentView() {
    if (!cy) return;
    var elements = cy.json().elements;
    var data = { nodes: {}, edges: [] };
    // Convert Cytoscape elements to our graph format
    if (elements.nodes) {
        elements.nodes.forEach(function (n) {
            data.nodes[n.data.id] = n.data;
        });
    }
    if (elements.edges) {
        elements.edges.forEach(function (e) {
            data.edges.push({ source: e.data.source, target: e.data.target, type: e.data.type });
        });
    }
    var blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'rtk-graph-view.json';
    a.click();
    URL.revokeObjectURL(url);
}

// Graph search bar + Settings panel
function initGraphSearch() {
    var searchInput = document.getElementById('search-input');
    var searchBtn = document.getElementById('search-btn');
    var filterBar = document.getElementById('filter-bar');
    var filterToggleCheck = document.getElementById('filter-toggle-check');
    var filterRun = document.getElementById('filter-run');
    var clearBtn = document.getElementById('clear-btn');
    var newStudyBtn = document.getElementById('new-study-btn');
    var legend = document.getElementById('graph-legend');
    var viewToggle = document.getElementById('view-toggle');
    var graphContainer = document.getElementById('graph-container');
    var tableView = document.getElementById('table-view');
    var saveBtn = document.getElementById('save-btn');
    var loadBtn = document.getElementById('load-btn');
    var loadFileInput = document.getElementById('load-file-input');
    var settingsToggle = document.getElementById('settings-toggle');
    var settingsPanel = document.getElementById('settings-panel');

    // Settings panel toggle
    settingsToggle.addEventListener('click', function () {
        settingsPanel.classList.toggle('collapsed');
        settingsToggle.classList.toggle('active');
        // Let cytoscape resize after transition
        setTimeout(function () { if (cy) cy.resize(); }, 220);
    });

    // Filter bar toggle (header checkbox)
    filterToggleCheck.addEventListener('change', function () {
        filterBar.classList.toggle('hidden', !filterToggleCheck.checked);
        if (filterToggleCheck.checked) {
            document.getElementById('filter-query').focus();
        }
    });

    // Search on Enter or click
    searchBtn.addEventListener('click', function () {
        graphSearch(searchInput.value);
    });
    searchInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            graphSearch(searchInput.value);
        }
    });

    // --- Settings panel controls ---

    // Node sizing segmented control
    var segBtns = document.querySelectorAll('#size-segmented .sp-seg-btn');
    segBtns.forEach(function (btn) {
        btn.addEventListener('click', function () {
            var mode = btn.dataset.mode;
            // Set internal mode directly
            nodeSizeMode = mode;
            applyNodeSizing();
            // Update active state
            segBtns.forEach(function (b) { b.classList.remove('active'); });
            btn.classList.add('active');
        });
    });

    // Edge label toggle (checkbox)
    var edgeLabelCheck = document.getElementById('edge-label-check');
    edgeLabelCheck.addEventListener('change', function () {
        toggleEdgeLabels();
    });

    // Legend toggle (checkbox)
    var legendCheck = document.getElementById('legend-check');
    legendCheck.addEventListener('change', function () {
        legend.classList.toggle('hidden', !legendCheck.checked);
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

    // Run Filter
    filterRun.addEventListener('click', function () {
        runFilter();
    });
    document.getElementById('filter-query').addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            runFilter();
        }
    });

    // Clear view button (just removes from display)
    clearBtn.addEventListener('click', function () {
        cy.elements().remove();
        updateGraphInfo();
    });

    // New Study button — deletes all data from memory (like graph reset)
    newStudyBtn.addEventListener('click', function () {
        showModal(
            'New Study',
            'This will DELETE ALL data from your current study (all nodes and edges in memory). This cannot be undone. Are you sure?',
            [
                { label: 'Delete & Start Fresh', primary: false, action: function () {
                    fetch('/api/graph/reset', { method: 'POST' })
                        .then(function (res) { return res.json(); })
                        .then(function (data) {
                            cy.elements().remove();
                            updateGraphInfo();
                            if (term) {
                                term.write('\r\n\x1b[32m' + data.message + '\x1b[0m\r\n');
                                showPrompt();
                            }
                        });
                }},
                { label: 'Cancel', primary: true }
            ]
        );
    });

    // Save graph to JSON file — ask entire study or current view
    saveBtn.addEventListener('click', function () {
        showModal(
            'Export Study',
            'Would you like to export the entire study (all data in memory) or only the nodes and edges currently displayed in the graph?',
            [
                { label: 'Entire Study', primary: true, action: function () { window.location.href = '/api/graph/export'; } },
                { label: 'Current View', action: function () { exportCurrentView(); } },
                { label: 'Cancel' }
            ]
        );
    });

    // Load graph from JSON file — ask add or replace
    loadBtn.addEventListener('click', function () {
        showModal(
            'Import Study',
            'Would you like to merge the file into your current study (keeping existing data) or replace the entire study with the file contents?',
            [
                { label: 'Merge', primary: true, action: function () { pendingImportMode = 'merge'; loadFileInput.click(); } },
                { label: 'Replace', action: function () { pendingImportMode = 'replace'; loadFileInput.click(); } },
                { label: 'Cancel' }
            ]
        );
    });
    loadFileInput.addEventListener('change', function () {
        var file = loadFileInput.files[0];
        if (!file) return;
        var formData = new FormData();
        formData.append('file', file);
        formData.append('mode', pendingImportMode || 'replace');
        fetch('/api/graph/import', { method: 'POST', body: formData })
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.error) {
                    if (term) {
                        term.write('\r\n\x1b[31mImport error: ' + data.error + '\x1b[0m\r\n');
                        showPrompt();
                    }
                    return;
                }
                if (term) {
                    term.write('\r\n\x1b[32m' + data.message + '\x1b[0m\r\n');
                    showPrompt();
                }
                // Reload graph view
                loadGraph();
            })
            .catch(function (err) {
                if (term) {
                    term.write('\r\n\x1b[31mImport failed: ' + err + '\x1b[0m\r\n');
                    showPrompt();
                }
            })
            .finally(function () {
                loadFileInput.value = '';
            });
    });
}

function graphSearch(query) {
    query = query.trim();
    if (!query) {
        // Blank search = load all nodes from study
        loadGraph();
        return;
    }

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

function runFilter() {
    var filterType = document.getElementById('filter-type').value;
    var filterYearMin = document.getElementById('filter-year-min').value;
    var filterYearMax = document.getElementById('filter-year-max').value;
    var filterQuery = document.getElementById('filter-query').value.trim();

    if (!filterType && !filterYearMin && !filterYearMax && !filterQuery) return;

    var body = {};
    if (filterType) body.type = filterType;
    if (filterYearMin) body.yearMin = parseInt(filterYearMin);
    if (filterYearMax) body.yearMax = parseInt(filterYearMax);
    if (filterQuery) body.query = filterQuery;

    fetch('/api/graph/filter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    })
        .then(function (res) { return res.json(); })
        .then(function (data) {
            if (data.error) {
                if (term) {
                    term.write('\r\n\x1b[31mFilter error: ' + data.error + '\x1b[0m\r\n');
                    showPrompt();
                }
                return;
            }
            cy.elements().remove();
            hideGraphBanner();
            cy.add(data.nodes);
            if (data.edges) cy.add(data.edges);
            runLayout();
            updateGraphInfo();

            if (term) {
                term.write('\r\n\x1b[32mFilter returned ' + data.nodes.length + ' nodes\x1b[0m\r\n');
                showPrompt();
            }
        })
        .catch(function (err) {
            if (term) {
                term.write('\r\n\x1b[31mFilter error: ' + err + '\x1b[0m\r\n');
                showPrompt();
            }
        });
}

function updateGraphInfo() {
    var info = document.getElementById('graph-info');
    if (info && cy) {
        var displayed = cy.nodes().length;
        var displayedEdges = cy.edges().length;
        // Fetch total study size from server
        fetch('/api/graph/stats')
            .then(function (res) { return res.json(); })
            .then(function (stats) {
                info.innerHTML = '<span class="info-displayed">' + displayed + ' nodes, ' + displayedEdges + ' edges displayed</span>' +
                    ' <span class="info-sep">|</span> ' +
                    '<span class="info-total">' + stats.total_nodes + ' nodes, ' + stats.total_edges + ' edges in study</span>';
            })
            .catch(function () {
                info.textContent = displayed + ' nodes, ' + displayedEdges + ' edges displayed';
            });
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
    var exportPngBtn = document.getElementById('export-png-btn');

    layoutSelect.addEventListener('change', function () {
        runLayoutWithName(layoutSelect.value);
    });

    exportPngBtn.addEventListener('click', function () {
        exportGraph();
    });
}

function runLayoutWithName(name) {
    if (!cy || cy.nodes().length === 0) return;

    var opts = { name: name, animate: true, animationDuration: 500, padding: 40 };

    // Layout-specific options
    if (name === 'fcose') {
        opts.quality = 'default';
        opts.nodeSeparation = 120;
        opts.idealEdgeLength = 120;
        opts.nodeRepulsion = function () { return 45000; };
        opts.gravity = 0.1;
        opts.gravityRange = 1.5;
        opts.numIter = 2500;
        opts.animate = 'end';
    } else if (name === 'dagre') {
        opts.rankDir = 'TB';
        opts.nodeSep = 60;
        opts.rankSep = 100;
        opts.edgeSep = 30;
        opts.animate = true;
    } else if (name === 'cose') {
        opts.nodeRepulsion = function () { return 32000; };
        opts.idealEdgeLength = function () { return 100; };
        opts.gravity = 0.15;
        opts.numIter = 500;
        opts.nodeOverlap = 20;
    } else if (name === 'breadthfirst') {
        opts.directed = true;
        opts.spacingFactor = 1.2;
    } else if (name === 'concentric') {
        opts.concentric = function (node) {
            return node.degree();
        };
        opts.levelWidth = function () { return 2; };
        opts.minNodeSpacing = 50;
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
    // No-op: persistence is via export/import JSON
}

function loadPreview() {
    fetch('/api/graph?limit=10')
        .then(function (res) { return res.json(); })
        .then(function (data) {
            if (data.nodes.length > 0) {
                cy.add(data.nodes);
                cy.add(data.edges);
                runLayout();
                showGraphBanner();
            }
            updateGraphInfo();
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
