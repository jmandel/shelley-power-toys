"""Checkpoint management for conversations."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from . import db

CHECKPOINT_FILE = os.environ.get(
    'SHELLEY_CHECKPOINT_FILE',
    str(Path.home() / '.config/shelley/power-toys-checkpoints.json')
)


def _load_checkpoints() -> Dict[str, Any]:
    """Load checkpoints from disk."""
    try:
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'checkpoints': {}}


def _save_checkpoints(data: Dict[str, Any]) -> None:
    """Save checkpoints to disk."""
    path = Path(CHECKPOINT_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def save_checkpoint(conversation_id: str, name: str, sequence_id: Optional[int] = None) -> Dict[str, Any]:
    """Save a checkpoint at the current or specified sequence.
    
    Args:
        conversation_id: The conversation to checkpoint
        name: Human-readable name for the checkpoint
        sequence_id: Specific sequence to checkpoint (default: latest)
    
    Returns:
        The checkpoint metadata
    """
    # Get conversation to verify it exists
    conv = db.get_conversation(conversation_id)
    if not conv:
        raise ValueError(f"Conversation {conversation_id} not found")
    
    # Get latest sequence if not specified
    if sequence_id is None:
        messages = db.get_messages(conversation_id)
        if not messages:
            raise ValueError(f"Conversation {conversation_id} has no messages")
        sequence_id = max(m['sequence_id'] for m in messages)
    
    # Get summary of the checkpoint point
    messages = db.get_messages(conversation_id, sequence_id)
    last_msg = messages[-1] if messages else None
    summary = db.get_message_summary(last_msg) if last_msg else "(empty)"
    
    checkpoint = {
        'conversation_id': conversation_id,
        'sequence_id': sequence_id,
        'name': name,
        'summary': summary,
        'slug': conv.get('slug'),
        'created_at': datetime.utcnow().isoformat()
    }
    
    data = _load_checkpoints()
    
    # Key by conversation_id:name
    key = f"{conversation_id}:{name}"
    data['checkpoints'][key] = checkpoint
    
    _save_checkpoints(data)
    return checkpoint


def get_checkpoint(conversation_id: str, name: str) -> Optional[Dict[str, Any]]:
    """Get a checkpoint by conversation and name."""
    data = _load_checkpoints()
    key = f"{conversation_id}:{name}"
    return data['checkpoints'].get(key)


def list_checkpoints(conversation_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List checkpoints, optionally filtered by conversation."""
    data = _load_checkpoints()
    checkpoints = list(data['checkpoints'].values())
    
    if conversation_id:
        checkpoints = [c for c in checkpoints if c['conversation_id'] == conversation_id]
    
    # Sort by created_at descending
    checkpoints.sort(key=lambda c: c.get('created_at', ''), reverse=True)
    return checkpoints


def restore_checkpoint(conversation_id: str, name: str) -> str:
    """Restore a checkpoint by branching from it.
    
    Returns:
        The new conversation ID
    """
    checkpoint = get_checkpoint(conversation_id, name)
    if not checkpoint:
        raise ValueError(f"Checkpoint '{name}' not found for conversation {conversation_id}")
    
    new_slug = f"{checkpoint.get('slug', 'conversation')}-from-{name}"
    
    return db.branch_conversation(
        checkpoint['conversation_id'],
        checkpoint['sequence_id'],
        new_slug
    )


def delete_checkpoint(conversation_id: str, name: str) -> bool:
    """Delete a checkpoint. Returns True if deleted."""
    data = _load_checkpoints()
    key = f"{conversation_id}:{name}"
    
    if key in data['checkpoints']:
        del data['checkpoints'][key]
        _save_checkpoints(data)
        return True
    return False
