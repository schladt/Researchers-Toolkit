// terminal.js — xterm.js initialization with Socket.IO I/O

let term = null;
let fitAddon = null;
let socket = null;
let currentLine = '';
let commandHistory = [];
let historyIndex = -1;

function initTerminal() {
    term = new window.Terminal({
        theme: {
            background: '#1a1a1a',
            foreground: '#d4d4d4',
            cursor: '#4a9eff',
            cursorAccent: '#1a1a1a',
            selectionBackground: '#3e3e3e'
        },
        fontFamily: 'Menlo, Monaco, "Courier New", monospace',
        fontSize: 13,
        cursorBlink: true
    });

    fitAddon = new window.FitAddon.FitAddon();
    term.loadAddon(fitAddon);

    term.open(document.getElementById('terminal'));
    fitAddon.fit();

    // ASCII art banner
    term.writeln('');
    term.writeln('\x1b[1;36m  ╦═╗ ╔═╗ ╔═╗ ╔═╗ ╔═╗ ╦═╗ ╔═╗ ╦ ╦ ╔═╗ ╦═╗ ╔═╗\x1b[0m');
    term.writeln('\x1b[1;36m  ╠╦╝ ║╣  ╚═╗ ║╣  ╠═╣ ╠╦╝ ║   ╠═╣ ║╣  ╠╦╝ ╚═╗\x1b[0m');
    term.writeln('\x1b[1;36m  ╩╚═ ╚═╝ ╚═╝ ╚═╝ ╩ ╩ ╩╚═ ╚═╝ ╩ ╩ ╚═╝ ╩╚═ ╚═╝\x1b[0m');
    term.writeln('\x1b[1;34m  ╔╦╗ ╔═╗ ╔═╗ ╦   ╦╔═ ╦ ╔╦╗\x1b[0m');
    term.writeln('\x1b[1;34m   ║  ║ ║ ║ ║ ║   ╠╩╗ ║  ║ \x1b[0m');
    term.writeln('\x1b[1;34m   ╩  ╚═╝ ╚═╝ ╩═╝ ╩ ╩ ╩  ╩ \x1b[0m');
    term.writeln('');
    term.writeln('\x1b[90m  📚  Explore academic research through connected knowledge graphs 🔬\x1b[0m');
    term.writeln('\x1b[90m  🔍  Search papers, build citation networks, and visualize connections 🕸️\x1b[0m');
    term.writeln('');
    term.writeln('\x1b[33m  Type \x1b[1mhelp\x1b[0m\x1b[33m to get started.\x1b[0m');
    term.writeln('');

    // Connect Socket.IO
    socket = io();

    socket.on('connect', function () {
        // Server will send welcome message
    });

    socket.on('output', function (data) {
        // Handle special graph commands from backend
        if (data.data === '__GRAPH_LOAD__') {
            loadGraph();
            return;
        }
        if (data.data === '__GRAPH_CLEAR__') {
            clearGraph();
            return;
        }
        if (data.data === '__GRAPH_STATS__') {
            showGraphStats();
            return;
        }
        if (data.data === '__GRAPH_RESET__') {
            resetGraph();
            return;
        }
        term.write(data.data + '\r\n');
    });

    socket.on('done', function () {
        showPrompt();
    });

    socket.on('disconnect', function () {
        term.writeln('\r\n\x1b[31mDisconnected from backend.\x1b[0m');
    });

    // Handle keyboard input
    term.onData(function (data) {
        handleInput(data);
    });

    showPrompt();
}

function showPrompt() {
    term.write('\r\n\x1b[36mrtk>\x1b[0m ');
    currentLine = '';
}

function handleInput(data) {
    // Handle special characters
    if (data === '\r') {
        // Enter key
        term.write('\r\n');
        if (currentLine.trim()) {
            commandHistory.push(currentLine);
            historyIndex = commandHistory.length;
            socket.emit('command', { command: currentLine });
            currentLine = '';
        } else {
            showPrompt();
        }
    } else if (data === '\x7f') {
        // Backspace
        if (currentLine.length > 0) {
            currentLine = currentLine.slice(0, -1);
            term.write('\b \b');
        }
    } else if (data === '\x1b[A') {
        // Up arrow - history
        if (historyIndex > 0) {
            historyIndex--;
            clearLine();
            currentLine = commandHistory[historyIndex];
            term.write(currentLine);
        }
    } else if (data === '\x1b[B') {
        // Down arrow - history
        if (historyIndex < commandHistory.length - 1) {
            historyIndex++;
            clearLine();
            currentLine = commandHistory[historyIndex];
            term.write(currentLine);
        } else {
            historyIndex = commandHistory.length;
            clearLine();
            currentLine = '';
        }
    } else if (data === '\x03') {
        // Ctrl+C
        term.write('^C');
        showPrompt();
    } else if (data >= ' ') {
        // Printable characters
        currentLine += data;
        term.write(data);
    }
}

function clearLine() {
    // Clear current input on the line
    for (let i = 0; i < currentLine.length; i++) {
        term.write('\b \b');
    }
}

// Refit terminal on window resize
function fitTerminal() {
    if (fitAddon) {
        fitAddon.fit();
    }
}
