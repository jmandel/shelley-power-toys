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

Spawn and manage sub-agents running in separate contexts. Default model is `claude-opus-4-20250514`.

```bash
# Start a sub-agent (returns immediately with job ID)
scripts/spawn start "Analyze the error logs in /var/log/app.log"

# Start and wait for completion
scripts/spawn start "Run the test suite" --wait

# Start with specific model or working directory
scripts/spawn start "Quick task" --model claude-sonnet-4-20250514
scripts/spawn start "Build feature" --cwd /path/to/project

# List all spawned agents and their status
scripts/spawn list
scripts/spawn list --json

# Check status / get result of a specific job
scripts/spawn check <job_id>
scripts/spawn check <job_id> --json

# Wait for specific jobs to complete
scripts/spawn wait <job_id>
scripts/spawn wait <job_id1> <job_id2> <job_id3>   # wait for all listed
scripts/spawn wait <job_id1> <job_id2> --any       # return when first completes
scripts/spawn wait --all                           # wait for all running jobs
scripts/spawn wait --all --timeout 300
```

Job state is stored in `~/.cache/shelley-power-toys/spawn-state.json`.

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
