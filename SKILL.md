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

## Quick Reference

| Command | What it does |
|---------|-------------|
| `power-toy branch` | Launch picker UI to branch current conversation |
| `power-toy branch -c <id>` | Branch a specific conversation (unstick) |
| `power-toy spawn "<task>"` | Spawn sub-agent, wait for result |
| `power-toy spawn "<task>" --async` | Spawn and return conversation ID |
| `power-toy checkpoint save <name>` | Save current turn as named checkpoint |
| `power-toy checkpoint restore <name>` | Branch from a checkpoint |
| `power-toy memory set <key> <value>` | Store a persistent fact |
| `power-toy memory note "<text>"` | Store a freeform note |
| `power-toy memory search <query>` | Search memories |
| `power-toy status` | Show context window usage |

## Branch

Branch creates a new conversation from a specific point in an existing one.

**Branch current conversation:**
```bash
./scripts/power-toy branch
```
This launches a picker UI. Return the URL to the user:
> "Visit {URL} to select where to branch from"

The user clicks on a turn, the branch is created, and they're redirected to the new conversation.

**Unstick a stuck conversation:**
```bash
./scripts/power-toy branch --conversation cXYZ789
```
Same flow, but for a different conversation that may have hit context limits.

**Browse all conversations:**
```bash
./scripts/power-toy branch --pick
```
Shows conversation list first, then branch point picker.

## Spawn

Spawn creates a sub-agent to handle a task in a separate context window.

**Synchronous (wait for result):**
```bash
./scripts/power-toy spawn "Analyze the error logs in /var/log/app.log and summarize issues"
```
Blocks until complete, returns the sub-agent's final response.

**Asynchronous (fire and forget):**
```bash
./scripts/power-toy spawn "Build a web scraper for news.ycombinator.com" --async
```
Returns immediately with the conversation ID. Check status later or let it run.

**With working directory:**
```bash
./scripts/power-toy spawn "Run the test suite" --cwd /home/exedev/myproject
```

## Checkpoint

Checkpoints are named savepoints within a conversation.

**Save a checkpoint:**
```bash
./scripts/power-toy checkpoint save "before-refactor"
```
Marks the current turn with a name for later reference.

**List checkpoints:**
```bash
./scripts/power-toy checkpoint list
```

**Restore (branch from checkpoint):**
```bash
./scripts/power-toy checkpoint restore "before-refactor"
```
Creates a new conversation branched from that checkpoint.

## Memory

Memory persists facts and notes across all conversations.

**Store a key-value fact:**
```bash
./scripts/power-toy memory set "db-password" "stored in .env.local"
./scripts/power-toy memory set "preferred-language" "TypeScript"
```

**Store a freeform note:**
```bash
./scripts/power-toy memory note "User prefers dark mode and minimal dependencies"
```

**Retrieve:**
```bash
./scripts/power-toy memory get "db-password"
./scripts/power-toy memory search "password"
./scripts/power-toy memory list
```

Memories are stored in `~/.config/shelley/power-toys-memory.json`.

## Status

Status shows conversation health and context window usage.

```bash
./scripts/power-toy status
```

Output:
```
Conversation: cABC123 (my-project-refactor)
Turns: 47 (24 user, 23 agent)
Estimated tokens: ~45,000
Context usage: ████████░░ 78%
Status: Healthy (room for ~12,000 more tokens)
```

**Check another conversation:**
```bash
./scripts/power-toy status --conversation cXYZ789
```

## Environment

The power-toy script expects these environment variables (auto-detected on exe.dev):

- `SHELLEY_DB` - Path to shelley.db (default: `~/.config/shelley/shelley.db`)
- `SHELLEY_API` - Shelley API base URL (default: `http://localhost:9999/api`)
- `SHELLEY_CONVERSATION_ID` - Current conversation ID (set by Shelley)
- `SHELLEY_CWD` - Current working directory

## Installation

Clone the repository and add to your path:

```bash
git clone https://github.com/anthropics/shelley-power-toys ~/.shelley-power-toys
echo 'export PATH="$PATH:$HOME/.shelley-power-toys/scripts"' >> ~/.bashrc
```

Or reference directly in your `~/.config/shelley/AGENTS.md`:

```markdown
## Power Toys

Power tools are available at ~/.shelley-power-toys/scripts/power-toy
See ~/.shelley-power-toys/SKILL.md for usage.
```
