---
name: shelley-power-toys
description: >
  Power tools for Shelley agent management on exe.dev VMs. Use when users want to:
  (1) Branch a conversation from a specific point to explore alternatives or unstick a stuck conversation,
  (2) Spawn sub-agents to handle isolated tasks without consuming context window,
  (3) Persist memory/notes across conversations,
  (4) Check context window usage and conversation health.
  Triggers on: "branch this conversation", "branch from earlier", "unstick", "spawn a sub-agent",
  "run this in background", "remember this", "what do you remember",
  "how much context", "context window status".
---

# Shelley Power Toys

Power tools for managing Shelley conversations and context on exe.dev.

## Setup

Before using these tools, set up the environment variables:

```bash
# Find Shelley's database from the running process
export SHELLEY_DB=$(ps aux | grep '[s]helley.*-db' | grep -oP '(?<=-db )\S+')

# Find Shelley's port and construct the UI base URL
SHELLEY_PORT=$(ss -tlnp | grep shelley | grep -oP ':\K[0-9]+(?=\s)')
export SHELLEY_UI="https://$(hostname).exe.xyz:$SHELLEY_PORT"
```

- `SHELLEY_DB` is required by: `branch`, `status`
- `SHELLEY_UI` is passed to `branch --shelley-ui` for redirect links

## Commands

| Script | Purpose |
|--------|--------|
| `branch` | Branch conversations with visual picker UI |
| `spawn` | Create sub-agents in separate context windows |
| `memory` | Persistent key-value and notes across conversations |
| `status` | Context window usage and conversation health |

## branch

Branch creates a new conversation from any point in an existing one.

**Requires:** `SHELLEY_DB` env var set (see Setup)

```bash
# Launch visual picker for a specific conversation
scripts/branch -c <conversation_id> --shelley-ui "$SHELLEY_UI"

# Browse all conversations first  
scripts/branch --shelley-ui "$SHELLEY_UI"

# Branch directly without UI (if you know the sequence)
scripts/branch -c <conversation_id> -s <sequence_number>
```

The `--shelley-ui` flag enables the picker to link to the new conversation in Shelley.

**Picker UI Keyboard Shortcuts:**
- `/` - Focus search
- `j`/`k` or ↑/↓ - Navigate
- `Enter` - Select / Confirm
- `Esc` - Back / Cancel
- `gg` - Jump to top
- `G` - Jump to bottom

## spawn

Spawn creates a sub-agent to handle a task in a separate context.

```bash
# Wait for result (synchronous)
scripts/spawn "Analyze the error logs in /var/log/app.log"

# Return immediately (asynchronous)
scripts/spawn "Build a web scraper" --async

# With specific working directory
scripts/spawn "Run tests" --cwd /path/to/project
```

## memory

Memory persists facts and notes across all conversations.

```bash
# Store facts
scripts/memory set "db-password" "stored in .env.local"
scripts/memory set "preferred-language" "TypeScript"

# Retrieve
scripts/memory get "db-password"

# Add freeform notes
scripts/memory note "User prefers minimal dependencies"

# Search
scripts/memory search "password"

# List all
scripts/memory list
```

Memories stored in `~/.config/shelley/power-toys-memory.json`.

## status

Status shows conversation health and context usage.

**Requires:** `SHELLEY_DB` env var set (see Setup)

```bash
# List recent conversations with usage
scripts/status

# Detailed view of specific conversation
scripts/status -c <conversation_id>

# JSON output
scripts/status --json
```
