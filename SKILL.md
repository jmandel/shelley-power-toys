---
name: shelley-power-toys
description: >
  Power tools for Shelley agent management on exe.dev VMs. Use when users want to:
  (1) Branch a conversation from a specific point to explore alternatives or unstick a stuck conversation,
  (2) Spawn sub-agents to handle isolated tasks without consuming context window,
  (3) Save and restore checkpoints within a conversation,
  (4) Persist memory/notes across conversations,
  (5) Check context window usage and conversation health.
  Triggers on: "branch this conversation", "branch from earlier", "unstick", "spawn a sub-agent",
  "run this in background", "save checkpoint", "remember this", "what do you remember",
  "how much context", "context window status".
---

# Shelley Power Toys

Power tools for managing Shelley conversations and context on exe.dev.

## Commands

| Script | Purpose |
|--------|--------|
| `branch` | Branch conversations with visual picker UI |
| `spawn` | Create sub-agents in separate context windows |
| `checkpoint` | Named savepoints within conversations |
| `memory` | Persistent key-value and notes across conversations |
| `status` | Context window usage and conversation health |

## branch

Branch creates a new conversation from a specific point.

```bash
# Launch visual picker for current conversation
./scripts/branch

# Launch picker for a specific conversation (unstick use case)
./scripts/branch -c cXYZ789

# Browse all conversations first
./scripts/branch --pick

# Branch directly without UI (if you know the sequence)
./scripts/branch -c cXYZ789 -s 50
```

**Picker UI Keyboard Shortcuts:**
- `/` - Focus search
- `j`/`k` or ↑/↓ - Navigate
- `Enter` - Select / Confirm
- `Esc` - Back / Cancel
- `gg` - Jump to top
- `G` - Jump to bottom

Return the picker URL to the user:
> "Visit {URL} to select where to branch from"

## spawn

Spawn creates a sub-agent to handle a task in a separate context.

```bash
# Wait for result (synchronous)
./scripts/spawn "Analyze the error logs in /var/log/app.log"

# Return immediately (asynchronous)
./scripts/spawn "Build a web scraper" --async

# With specific working directory
./scripts/spawn "Run tests" --cwd /home/exedev/myproject
```

## checkpoint

Checkpoints are named savepoints within a conversation.

```bash
# Save current turn as checkpoint
./scripts/checkpoint save "before-refactor"

# List all checkpoints
./scripts/checkpoint list

# Restore (creates a branch from that point)
./scripts/checkpoint restore "before-refactor"

# Delete a checkpoint
./scripts/checkpoint delete "before-refactor"
```

## memory

Memory persists facts and notes across all conversations.

```bash
# Store facts
./scripts/memory set "db-password" "stored in .env.local"
./scripts/memory set "preferred-language" "TypeScript"

# Retrieve
./scripts/memory get "db-password"

# Add freeform notes
./scripts/memory note "User prefers minimal dependencies"

# Search
./scripts/memory search "password"

# List all
./scripts/memory list
```

Memories stored in `~/.config/shelley/power-toys-memory.json`.

## status

Status shows conversation health and context usage.

```bash
# List recent conversations with usage
./scripts/status

# Detailed view of specific conversation
./scripts/status -c cXYZ789

# JSON output
./scripts/status --json
```

## Environment Variables

- `SHELLEY_DB` - Path to shelley.db (default: `~/.config/shelley/shelley.db`)
- `SHELLEY_API` - Shelley API base URL (default: `http://localhost:9999/api`)
- `SHELLEY_CONVERSATION_ID` - Current conversation ID
- `SHELLEY_CWD` - Current working directory

## Installation

```bash
git clone https://github.com/anthropics/shelley-power-toys ~/.shelley-power-toys
export PATH="$PATH:$HOME/.shelley-power-toys/scripts"
```

Or add to `~/.config/shelley/AGENTS.md`:

```markdown
## Power Toys
Available at ~/.shelley-power-toys/scripts/
See ~/.shelley-power-toys/SKILL.md for usage.
```

