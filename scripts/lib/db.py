"""SQLite helpers for Shelley database operations."""

import json
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

SHELLEY_DB = os.environ.get('SHELLEY_DB', str(Path.home() / '.config/shelley/shelley.db'))


def get_connection() -> sqlite3.Connection:
    """Get a connection to the Shelley database."""
    conn = sqlite3.connect(SHELLEY_DB)
    conn.row_factory = sqlite3.Row
    return conn


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Get conversation metadata."""
    with get_connection() as conn:
        row = conn.execute(
            'SELECT * FROM conversations WHERE conversation_id = ?',
            (conversation_id,)
        ).fetchone()
        return dict(row) if row else None


def get_messages(conversation_id: str, max_sequence: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get messages for a conversation, optionally up to a max sequence."""
    with get_connection() as conn:
        if max_sequence is not None:
            rows = conn.execute(
                'SELECT * FROM messages WHERE conversation_id = ? AND sequence_id <= ? ORDER BY sequence_id',
                (conversation_id, max_sequence)
            ).fetchall()
        else:
            rows = conn.execute(
                'SELECT * FROM messages WHERE conversation_id = ? ORDER BY sequence_id',
                (conversation_id,)
            ).fetchall()
        return [dict(row) for row in rows]


def get_message_summary(msg: Dict[str, Any]) -> str:
    """Get a short summary of a message for display."""
    msg_type = msg.get('type', 'unknown')
    
    if msg_type == 'user':
        # Try to extract user text from llm_data
        llm_data = msg.get('llm_data')
        if llm_data:
            try:
                data = json.loads(llm_data)
                for content in data.get('Content', []):
                    if content.get('Type') == 2 and content.get('Text'):
                        text = content['Text'][:100]
                        return f"User: {text}{'...' if len(content['Text']) > 100 else ''}"
            except json.JSONDecodeError:
                pass
        return "User: (message)"
    
    elif msg_type == 'agent':
        llm_data = msg.get('llm_data')
        if llm_data:
            try:
                data = json.loads(llm_data)
                for content in data.get('Content', []):
                    if content.get('Type') == 2 and content.get('Text'):
                        text = content['Text'][:100]
                        return f"Agent: {text}{'...' if len(content['Text']) > 100 else ''}"
                    # Check for tool use
                    if content.get('Type') == 5 and content.get('ToolName'):
                        return f"Agent: [using {content['ToolName']}]"
            except json.JSONDecodeError:
                pass
        return "Agent: (response)"
    
    elif msg_type == 'tool':
        return "Tool: (result)"
    
    elif msg_type == 'system':
        return "System: (prompt)"
    
    return f"{msg_type}: (message)"


def generate_conversation_id() -> str:
    """Generate a new conversation ID in Shelley's format."""
    # Shelley uses 'c' prefix + 7 alphanumeric chars
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    import random
    suffix = ''.join(random.choices(chars, k=7))
    return f'c{suffix}'


def generate_message_id() -> str:
    """Generate a new message ID."""
    return str(uuid.uuid4())


def branch_conversation(
    source_conversation_id: str,
    branch_after_sequence: int,
    new_slug: Optional[str] = None
) -> str:
    """Create a new conversation branched from a specific point.
    
    Args:
        source_conversation_id: The conversation to branch from
        branch_after_sequence: Include messages up to and including this sequence
        new_slug: Optional slug for the new conversation
    
    Returns:
        The new conversation ID
    """
    source = get_conversation(source_conversation_id)
    if not source:
        raise ValueError(f"Conversation {source_conversation_id} not found")
    
    source_messages = get_messages(source_conversation_id, branch_after_sequence)
    if not source_messages:
        raise ValueError(f"No messages found up to sequence {branch_after_sequence}")
    
    new_id = generate_conversation_id()
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    if not new_slug:
        base_slug = source.get('slug') or 'conversation'
        new_slug = f"{base_slug}-branch"
    
    with get_connection() as conn:
        # Create new conversation
        conn.execute(
            '''INSERT INTO conversations 
               (conversation_id, slug, user_initiated, created_at, updated_at, cwd, archived)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (new_id, new_slug, True, now, now, source.get('cwd', '/home/exedev'), False)
        )
        
        # Copy messages with new IDs but same sequence numbers
        for msg in source_messages:
            new_msg_id = generate_message_id()
            conn.execute(
                '''INSERT INTO messages
                   (message_id, conversation_id, sequence_id, type, llm_data, user_data, usage_data, created_at, display_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    new_msg_id,
                    new_id,
                    msg['sequence_id'],
                    msg['type'],
                    msg.get('llm_data'),
                    msg.get('user_data'),
                    msg.get('usage_data'),
                    msg.get('created_at', now),
                    msg.get('display_data')
                )
            )
        
        conn.commit()
    
    return new_id


def estimate_tokens(conversation_id: str) -> Dict[str, int]:
    """Estimate token usage for a conversation."""
    messages = get_messages(conversation_id)
    
    total_input = 0
    total_output = 0
    
    for msg in messages:
        usage_data = msg.get('usage_data')
        if usage_data:
            try:
                usage = json.loads(usage_data)
                total_input += usage.get('input_tokens', 0)
                total_output += usage.get('output_tokens', 0)
            except json.JSONDecodeError:
                pass
    
    # Rough estimate if no usage data: ~4 chars per token
    if total_input == 0 and total_output == 0:
        for msg in messages:
            llm_data = msg.get('llm_data', '')
            # Very rough estimate
            total_input += len(llm_data) // 4 if msg.get('type') == 'user' else 0
            total_output += len(llm_data) // 4 if msg.get('type') == 'agent' else 0
    
    return {
        'input_tokens': total_input,
        'output_tokens': total_output,
        'total_tokens': total_input + total_output,
        'estimated': total_input == 0 and total_output == 0
    }


def list_conversations(limit: int = 20) -> List[Dict[str, Any]]:
    """List recent conversations."""
    with get_connection() as conn:
        rows = conn.execute(
            'SELECT * FROM conversations WHERE archived = 0 ORDER BY updated_at DESC LIMIT ?',
            (limit,)
        ).fetchall()
        return [dict(row) for row in rows]
