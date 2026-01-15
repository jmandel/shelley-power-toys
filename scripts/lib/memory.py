"""Persistent memory storage for power toys."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

MEMORY_FILE = os.environ.get(
    'SHELLEY_MEMORY_FILE',
    str(Path.home() / '.config/shelley/power-toys-memory.json')
)


def _load_memory() -> Dict[str, Any]:
    """Load memory from disk."""
    try:
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {'facts': {}, 'notes': []}


def _save_memory(data: Dict[str, Any]) -> None:
    """Save memory to disk."""
    path = Path(MEMORY_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def set_fact(key: str, value: str) -> None:
    """Store a key-value fact."""
    data = _load_memory()
    data['facts'][key] = {
        'value': value,
        'updated_at': datetime.utcnow().isoformat()
    }
    _save_memory(data)


def get_fact(key: str) -> Optional[str]:
    """Retrieve a fact by key."""
    data = _load_memory()
    fact = data.get('facts', {}).get(key)
    return fact['value'] if fact else None


def delete_fact(key: str) -> bool:
    """Delete a fact by key. Returns True if deleted."""
    data = _load_memory()
    if key in data.get('facts', {}):
        del data['facts'][key]
        _save_memory(data)
        return True
    return False


def add_note(text: str) -> None:
    """Add a freeform note."""
    data = _load_memory()
    data['notes'].append({
        'text': text,
        'created_at': datetime.utcnow().isoformat()
    })
    _save_memory(data)


def list_facts() -> Dict[str, str]:
    """List all facts."""
    data = _load_memory()
    return {k: v['value'] for k, v in data.get('facts', {}).items()}


def list_notes() -> List[Dict[str, str]]:
    """List all notes."""
    data = _load_memory()
    return data.get('notes', [])


def search(query: str) -> Dict[str, Any]:
    """Search facts and notes for a query string."""
    query_lower = query.lower()
    data = _load_memory()
    
    matching_facts = {
        k: v['value']
        for k, v in data.get('facts', {}).items()
        if query_lower in k.lower() or query_lower in v['value'].lower()
    }
    
    matching_notes = [
        note for note in data.get('notes', [])
        if query_lower in note['text'].lower()
    ]
    
    return {
        'facts': matching_facts,
        'notes': matching_notes
    }


def clear_all() -> None:
    """Clear all memory (use with caution)."""
    _save_memory({'facts': {}, 'notes': []})
