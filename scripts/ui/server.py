"""Minimal web server for power toy UIs."""

import json
import os
import socket
import sys
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import db


def find_free_port(start: int = 8100, end: int = 8199) -> int:
    """Find a free port in the given range."""
    for port in range(start, end):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No free port found in range {start}-{end}")


def get_hostname() -> str:
    """Get the exe.dev hostname if available."""
    hostname = os.environ.get('EXE_HOSTNAME', '')
    if hostname:
        return hostname
    try:
        with open('/etc/hostname') as f:
            name = f.read().strip()
            if name:
                return f"{name}.exe.xyz"
    except:
        pass
    return 'localhost'


# HTML Templates as module-level constants
CONVERSATION_LIST_HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>Select Conversation - Power Toys</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: system-ui, -apple-system, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px;
            background: #1a1a2e;
            color: #eee;
        }
        h1 { color: #fff; border-bottom: 2px solid #4a4a6a; padding-bottom: 10px; }
        .conversation {
            background: #252540;
            border: 1px solid #3a3a5a;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            cursor: pointer;
            transition: all 0.2s;
        }
        .conversation:hover {
            background: #2a2a4a;
            border-color: #5a5a8a;
        }
        .conversation .slug { font-weight: bold; color: #8af; }
        .conversation .meta { color: #888; font-size: 0.85em; margin-top: 5px; }
        .conversation .id { font-family: monospace; color: #666; }
    </style>
</head>
<body>
    <h1>Select Conversation to Branch</h1>
    <div id="conversations">Loading...</div>
    <script>
        fetch('/api/conversations')
            .then(r => r.json())
            .then(conversations => {
                const container = document.getElementById('conversations');
                if (conversations.length === 0) {
                    container.innerHTML = '<p>No conversations found.</p>';
                    return;
                }
                container.innerHTML = conversations.map(c => 
                    '<div class="conversation" onclick="window.location=\\'/pick?conversation=' + c.conversation_id + '\\'">' +
                    '<div class="slug">' + (c.slug || '(untitled)') + '</div>' +
                    '<div class="meta"><span class="id">' + c.conversation_id + '</span> · Updated ' + new Date(c.updated_at).toLocaleString() + '</div>' +
                    '</div>'
                ).join('');
            })
            .catch(err => {
                document.getElementById('conversations').innerHTML = 
                    '<p style="color: #f88">Error loading conversations: ' + err + '</p>';
            });
    </script>
</body>
</html>'''


BRANCH_PICKER_HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>Branch: __SLUG__ - Power Toys</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: system-ui, -apple-system, sans-serif; 
            max-width: 900px; 
            margin: 0 auto; 
            padding: 20px;
            background: #1a1a2e;
            color: #eee;
        }
        h1 { color: #fff; margin-bottom: 5px; }
        .subtitle { color: #888; margin-bottom: 20px; }
        .back { color: #8af; text-decoration: none; }
        .back:hover { text-decoration: underline; }
        
        .timeline { 
            border-left: 3px solid #3a3a5a; 
            margin-left: 20px;
            padding-left: 20px;
        }
        .turn {
            position: relative;
            margin: 15px 0;
            padding: 12px 15px;
            background: #252540;
            border: 1px solid #3a3a5a;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .turn:hover {
            background: #2a2a4a;
            border-color: #5a5a8a;
        }
        .turn::before {
            content: '';
            position: absolute;
            left: -28px;
            top: 50%;
            transform: translateY(-50%);
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #3a3a5a;
            border: 2px solid #252540;
        }
        .turn:hover::before {
            background: #8af;
        }
        .turn.user { border-left: 3px solid #4a9; }
        .turn.agent { border-left: 3px solid #84f; }
        .turn.system { border-left: 3px solid #666; opacity: 0.7; }
        
        .turn .seq { 
            font-family: monospace; 
            color: #666; 
            font-size: 0.8em;
            float: right;
        }
        .turn .type { 
            font-weight: bold; 
            color: #aaa;
            text-transform: uppercase;
            font-size: 0.75em;
            letter-spacing: 0.5px;
        }
        .turn .summary { 
            margin-top: 5px;
            color: #ccc;
            font-size: 0.95em;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: #252540;
            border: 1px solid #4a4a6a;
            border-radius: 12px;
            padding: 25px;
            max-width: 500px;
            text-align: center;
        }
        .modal h2 { margin-top: 0; }
        .modal button {
            padding: 12px 24px;
            margin: 10px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
        }
        .modal .confirm {
            background: #4a9;
            color: white;
        }
        .modal .cancel {
            background: #444;
            color: #ccc;
        }
        .modal .confirm:hover { background: #5ba; }
        .modal .cancel:hover { background: #555; }
        
        .status {
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }
        .status.loading { background: #2a2a4a; }
        .status.success { background: #1a3a2a; color: #4c8; }
        .status.error { background: #3a1a1a; color: #c44; }
    </style>
</head>
<body>
    <p><a href="/" class="back">← Back to conversations</a></p>
    <h1>Branch: __SLUG__</h1>
    <p class="subtitle">Click on a turn to branch from that point. All messages up to and including that turn will be copied to a new conversation.</p>
    
    <div id="timeline" class="timeline">
        <div class="status loading">Loading conversation...</div>
    </div>
    
    <div id="modal" class="modal">
        <div class="modal-content">
            <h2>Create Branch?</h2>
            <p id="modal-text">Branch from turn #<span id="modal-seq"></span>?</p>
            <p id="modal-summary" style="color: #888; font-size: 0.9em;"></p>
            <button class="confirm" onclick="confirmBranch()">Create Branch</button>
            <button class="cancel" onclick="closeModal()">Cancel</button>
        </div>
    </div>
    
    <script>
        var conversationId = '__CONV_ID__';
        var selectedSequence = null;
        var selectedSummary = '';
        
        function escapeHtml(text) {
            return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }
        
        function showModal(seq, summary) {
            selectedSequence = seq;
            selectedSummary = summary;
            document.getElementById('modal-seq').textContent = seq;
            document.getElementById('modal-summary').textContent = summary;
            document.getElementById('modal').classList.add('active');
        }
        
        function closeModal() {
            document.getElementById('modal').classList.remove('active');
        }
        
        function confirmBranch() {
            document.querySelector('.modal-content').innerHTML = 
                '<div class="status loading">Creating branch...</div>';
            
            fetch('/api/branch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    conversation_id: conversationId,
                    sequence_id: selectedSequence
                })
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.success) {
                    document.querySelector('.modal-content').innerHTML = 
                        '<div class="status success">' +
                        '<h3>Branch Created!</h3>' +
                        '<p>New conversation: ' + data.new_conversation_id + '</p>' +
                        '<p><a href="' + data.redirect_url + '" style="color: #4c8;">Open new conversation →</a></p>' +
                        '</div>';
                } else {
                    throw new Error(data.error || 'Unknown error');
                }
            })
            .catch(function(err) {
                document.querySelector('.modal-content').innerHTML = 
                    '<div class="status error">' +
                    '<h3>Error</h3>' +
                    '<p>' + err + '</p>' +
                    '<button class="cancel" onclick="closeModal()">Close</button>' +
                    '</div>';
            });
        }
        
        // Load messages
        fetch('/api/messages?conversation=' + conversationId)
            .then(function(r) { return r.json(); })
            .then(function(messages) {
                var timeline = document.getElementById('timeline');
                
                if (messages.length === 0) {
                    timeline.innerHTML = '<p>No messages in this conversation.</p>';
                    return;
                }
                
                timeline.innerHTML = messages.map(function(m) {
                    var safeSummary = escapeHtml(m.summary).replace(/'/g, "\\'").replace(/\\n/g, ' ');
                    return '<div class="turn ' + m.type + '" onclick="showModal(' + m.sequence_id + ', \\'' + safeSummary + '\\')">' +
                        '<span class="seq">#' + m.sequence_id + '</span>' +
                        '<div class="type">' + m.type + '</div>' +
                        '<div class="summary">' + escapeHtml(m.summary) + '</div>' +
                        '</div>';
                }).join('');
            })
            .catch(function(err) {
                document.getElementById('timeline').innerHTML = 
                    '<div class="status error">Error loading messages: ' + err + '</div>';
            });
    </script>
</body>
</html>'''


class BranchPickerHandler(BaseHTTPRequestHandler):
    """HTTP handler for the branch picker UI."""
    
    conversation_id = None
    pick_conversation = False
    shelley_ui_base = 'https://localhost:9999'
    
    def log_message(self, format, *args):
        pass
    
    def send_html(self, html: str, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(html.encode()))
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data)
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body.encode()))
        self.end_headers()
        self.wfile.write(body.encode())
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        
        if path == '/':
            if self.pick_conversation or not self.conversation_id:
                self.send_html(CONVERSATION_LIST_HTML)
            else:
                self.show_branch_picker(self.conversation_id)
        
        elif path == '/pick':
            conv_id = query.get('conversation', [None])[0]
            if conv_id:
                self.show_branch_picker(conv_id)
            else:
                self.send_html('<h1>Error</h1><p>No conversation specified</p>', 400)
        
        elif path == '/api/conversations':
            conversations = db.list_conversations(50)
            self.send_json(conversations)
        
        elif path == '/api/messages':
            conv_id = query.get('conversation', [None])[0]
            if conv_id:
                messages = db.get_messages(conv_id)
                simplified = []
                for msg in messages:
                    simplified.append({
                        'sequence_id': msg['sequence_id'],
                        'type': msg['type'],
                        'summary': db.get_message_summary(msg),
                        'created_at': msg.get('created_at', '')
                    })
                self.send_json(simplified)
            else:
                self.send_json({'error': 'No conversation specified'}, 400)
        
        else:
            self.send_html('<h1>404 Not Found</h1>', 404)
    
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path == '/api/branch':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body) if body else {}
            
            conv_id = data.get('conversation_id')
            sequence_id = data.get('sequence_id')
            
            if not conv_id or sequence_id is None:
                self.send_json({'error': 'Missing conversation_id or sequence_id'}, 400)
                return
            
            try:
                new_id = db.branch_conversation(conv_id, sequence_id)
                new_url = f"{self.shelley_ui_base}/c/{new_id}"
                self.send_json({
                    'success': True,
                    'new_conversation_id': new_id,
                    'redirect_url': new_url
                })
            except Exception as e:
                self.send_json({'error': str(e)}, 500)
        
        else:
            self.send_json({'error': 'Not found'}, 404)
    
    def show_branch_picker(self, conversation_id: str):
        conv = db.get_conversation(conversation_id)
        if not conv:
            self.send_html(f'<h1>Error</h1><p>Conversation {conversation_id} not found</p>', 404)
            return
        
        slug = conv.get('slug') or conversation_id
        html = BRANCH_PICKER_HTML.replace('__SLUG__', slug).replace('__CONV_ID__', conversation_id)
        self.send_html(html)


def run_branch_picker(
    conversation_id: str = None,
    pick_conversation: bool = False,
    shelley_ui_base: str = None
) -> str:
    port = find_free_port()
    hostname = get_hostname()
    
    if not shelley_ui_base:
        if 'exe.xyz' in hostname:
            shelley_ui_base = f"https://{hostname}:9999"
        else:
            shelley_ui_base = "http://localhost:9999"
    
    BranchPickerHandler.conversation_id = conversation_id
    BranchPickerHandler.pick_conversation = pick_conversation
    BranchPickerHandler.shelley_ui_base = shelley_ui_base
    
    server = HTTPServer(('0.0.0.0', port), BranchPickerHandler)
    
    if 'exe.xyz' in hostname:
        url = f"https://{hostname}:{port}/"
    else:
        url = f"http://localhost:{port}/"
    
    print(f"Branch picker running at: {url}", file=sys.stderr)
    print(url)
    sys.stdout.flush()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
    
    return url


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Branch picker UI server')
    parser.add_argument('-c', '--conversation', help='Conversation ID to branch')
    parser.add_argument('--pick', action='store_true', help='Show conversation picker first')
    parser.add_argument('--shelley-ui', help='Shelley UI base URL')
    
    args = parser.parse_args()
    run_branch_picker(
        conversation_id=args.conversation,
        pick_conversation=args.pick,
        shelley_ui_base=args.shelley_ui
    )
