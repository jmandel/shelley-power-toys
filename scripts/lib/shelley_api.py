"""Shelley API client for power toys."""

import json
import os
import time
import urllib.request
import urllib.error
from typing import Optional

SHELLEY_API = os.environ.get('SHELLEY_API', 'http://localhost:9999/api')
SHELLEY_HEADERS = {
    'Content-Type': 'application/json',
    'X-Shelley-Request': '1',
    'X-Exedev-Userid': 'power-toys',
}


def _request(method: str, path: str, data: Optional[dict] = None) -> dict:
    """Make a request to the Shelley API."""
    url = f"{SHELLEY_API}{path}"
    body = json.dumps(data).encode() if data else None
    
    req = urllib.request.Request(url, data=body, headers=SHELLEY_HEADERS, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        raise RuntimeError(f"Shelley API error {e.code}: {error_body}")


def list_conversations(limit: int = 20) -> list:
    """List recent conversations."""
    return _request('GET', f'/conversations?limit={limit}')


def get_conversation(conversation_id: str) -> dict:
    """Get a conversation with its messages."""
    return _request('GET', f'/conversation/{conversation_id}')


def create_conversation(message: str, cwd: str, model: str = 'claude-opus-4.5') -> str:
    """Create a new conversation and return its ID."""
    result = _request('POST', '/conversations/new', {
        'message': message,
        'model': model,
        'cwd': cwd,
    })
    return result['conversation_id']


def send_message(conversation_id: str, message: str, model: str = 'claude-opus-4.5') -> None:
    """Send a message to an existing conversation."""
    _request('POST', f'/conversation/{conversation_id}/chat', {
        'message': message,
        'model': model,
    })


def wait_for_completion(conversation_id: str, timeout_seconds: int = 300, poll_interval: float = 1.0) -> dict:
    """Poll until the conversation is no longer processing."""
    start = time.time()
    
    while time.time() - start < timeout_seconds:
        response = get_conversation(conversation_id)
        
        if response.get('agent_working') is False:
            # Check for end_of_turn
            messages = response.get('messages', [])
            has_complete = any(
                m.get('type') == 'agent' and m.get('end_of_turn')
                for m in messages
            )
            if has_complete:
                return response
        
        time.sleep(poll_interval)
    
    raise TimeoutError(f"Conversation {conversation_id} did not complete within {timeout_seconds}s")


def extract_final_response(response: dict) -> Optional[str]:
    """Extract the final text response from a conversation."""
    messages = response.get('messages', [])
    
    for msg in reversed(messages):
        if msg.get('type') == 'agent' and msg.get('end_of_turn'):
            llm_data = msg.get('llm_data')
            if llm_data:
                try:
                    data = json.loads(llm_data)
                    for content in data.get('Content', []):
                        # Type 2 is text
                        if content.get('Type') == 2 and content.get('Text'):
                            return content['Text']
                except json.JSONDecodeError:
                    pass
    return None
