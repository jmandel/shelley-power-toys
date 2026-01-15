"""Minimal web server for power toy UIs."""

import json
import os
import socket
import sys
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Add parent to path for imports
SCRIPT_DIR = Path(__file__).parent.parent
UI_DIR = SCRIPT_DIR.parent / 'ui' / 'branch-picker'
sys.path.insert(0, str(SCRIPT_DIR))

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


class BranchPickerHandler(BaseHTTPRequestHandler):
    """HTTP handler for the branch picker UI."""
    
    conversation_id = None
    pick_conversation = False
    shelley_ui_base = 'https://localhost:9999'
    
    def log_message(self, format, *args):
        pass
    
    def send_file(self, filepath: Path, content_type: str):
        try:
            content = filepath.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', len(content))
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)
    
    def send_html(self, html: str, status: int = 200):
        content = html.encode()
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(content))
        self.end_headers()
        self.wfile.write(content)
    
    def send_json(self, data, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        
        # Static files
        if path == '/' or path == '/index.html':
            # Inject conversation ID if specified
            html = (UI_DIR / 'index.html').read_text()
            if self.conversation_id and not self.pick_conversation:
                # Auto-redirect to conversation view
                html = html.replace(
                    '<script src="app.js"></script>',
                    '<script>history.replaceState({}, "", "?c=' + self.conversation_id + '");</script>\n<script src="app.js"></script>'
                )
            self.send_html(html)
        elif path == '/style.css':
            self.send_file(UI_DIR / 'style.css', 'text/css')
        elif path == '/app.js':
            self.send_file(UI_DIR / 'app.js', 'application/javascript')
        
        # API endpoints
        elif path == '/api/conversations':
            conversations = db.list_conversations(100)
            self.send_json(conversations)
        
        elif path == '/api/messages':
            conv_id = query.get('conversation', [None])[0]
            if conv_id:
                messages = db.get_messages(conv_id)
                simplified = [{
                    'sequence_id': msg['sequence_id'],
                    'type': msg['type'],
                    'summary': db.get_message_summary(msg),
                    'created_at': msg.get('created_at', '')
                } for msg in messages]
                self.send_json(simplified)
            else:
                self.send_json({'error': 'No conversation specified'}, 400)
        
        else:
            self.send_error(404)
    
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


def run_branch_picker(
    conversation_id: str = None,
    pick_conversation: bool = False,
    shelley_ui_base: str = None,
    port: int = None
) -> str:
    if port is None:
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
    
    print(f"Branch picker: {url}", file=sys.stderr)
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
    parser.add_argument('--port', type=int, help='Port to listen on')
    parser.add_argument('--shelley-ui', help='Shelley UI base URL')
    
    args = parser.parse_args()
    run_branch_picker(
        conversation_id=args.conversation,
        pick_conversation=args.pick,
        shelley_ui_base=args.shelley_ui,
        port=args.port
    )
