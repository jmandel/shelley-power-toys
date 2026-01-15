---
name: shelley-power-toys
description: >
  Power tools for Shelley agent management on exe.dev VMs. Use when users want to:
  (1) Branch a conversation from a specific point to explore alternatives or unstick a stuck conversation,
  (2) Spawn sub-agents to handle isolated tasks without consuming context window,
  (3) Check context window usage and conversation health.
  Triggers on: "branch this conversation", "branch from earlier", "unstick", "spawn a sub-agent",
  "run this in background", "how much context", "context window status".
---

# Shelley Power Toys

Power tools for managing Shelley conversations and context on exe.dev.

## Setup

Required values for the tools:

- **Database path**: In your system prompt
- **Shelley UI base URL**: May be in your system prompt. Otherwise construct from hostname (in system prompt) + port from `ss -tlnp | grep shelley` → `https://<hostname>.exe.xyz:<port>`

## Commands

| Script | Purpose |
|--------|--------|
| `branch` | Branch conversations with visual picker UI |
| `spawn` | Create sub-agents in separate context windows |
| `status` | Context window usage and conversation health |

## branch

Branch creates a new conversation from any point in an existing one.

```bash
# Launch visual picker for a specific conversation
scripts/branch --db "$SHELLEY_DB" --shelley-ui "$SHELLEY_UI" -c <conversation_id>

# Browse all conversations first  
scripts/branch --db "$SHELLEY_DB" --shelley-ui "$SHELLEY_UI"

# Branch directly without UI (if you know the sequence)
scripts/branch --db "$SHELLEY_DB" -c <conversation_id> -s <sequence_number>
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

## status

Status shows conversation health and context usage.

```bash
# List recent conversations with usage
scripts/status --db "$SHELLEY_DB"

# Detailed view of specific conversation
scripts/status --db "$SHELLEY_DB" -c <conversation_id>

# JSON output
scripts/status --db "$SHELLEY_DB" --json
```
