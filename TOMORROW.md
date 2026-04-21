# AgentMemory — Context & Tomorrow's Roadmap

> This file was auto-generated to preserve context across sessions.
> Date: 2026-04-21
> GitHub: https://github.com/Vish150988/agentmemory

---

## What We Built Today

AgentMemory — an open-source cross-agent memory layer for AI coding agents.

### Sprints Completed

| Sprint | Status | Deliverable |
|--------|--------|-------------|
| Sprint 0 | ✅ | Project setup & architecture |
| Sprint 1 | ✅ | Core SQLite memory engine + CLI |
| Sprint 2 | ✅ | Cross-agent integration (CLAUDE.md sync, git hooks) |
| Sprint 3 | ✅ | Semantic recall, auto-summarization, confidence decay |
| Sprint 4 | ✅ | Polish, tests, docs & launch |

### Key Features Shipped

- **Local-first SQLite storage** — no cloud, no API keys
- **Cross-agent compatibility** — Claude Code, Codex, Cursor, Gemini CLI
- **Structured memory categories** — fact, decision, action, preference, error
- **Semantic search backends** — TF-IDF (default) or optional sentence-transformers
- **Embedding cache** — ST embeddings stored in SQLite, never recompute
- **Auto-summarization** — project & session summaries with keyword extraction
- **Confidence decay + reinforcement** — old memories fade, validated ones stick
- **CLAUDE.md auto-generation** — Claude Code reads context automatically
- **Git hooks** — auto-sync on commit
- **Full CLI** — init, capture, recall, search, related, summarize, reinforce, decay, sync, export

### Stats

| Metric | Value |
|--------|-------|
| Lines of code | ~1,800 |
| Python modules | 9 |
| Tests | 18 (all passing) |
| CI | Ubuntu, macOS, Windows × Python 3.10/3.11/3.12 |
| Git commits | 10 |
| GitHub stars | Just launched |

### Launch Status

| Platform | Status |
|----------|--------|
| GitHub | ✅ Live |
| Twitter/X | ✅ Posted |
| Reddit | 📝 Ready to post |
| Hacker News | 📝 Ready to post |

---

## Tomorrow's Roadmap

### Feature 1: Auto-Capture from Agent Sessions
**Problem:** Users have to manually type `agentmemory capture "..."` after every decision.
**Solution:** Automatically capture agent session output.
**Approaches:**
- Parse Claude Code / Codex session logs
- Hook into shell history
- Monitor file changes and infer decisions
- Optional: background daemon that watches terminal output

### Feature 2: Team Sync (Shared Memory via Git)
**Problem:** Teams can't share agent memory. Each dev has isolated SQLite db.
**Solution:** Sync memory across team members via git.
**Approaches:**
- `.agent-memory/` folder committed to repo
- Merge strategies for conflicting memories
- Shared CLAUDE.md in repo root
- Per-branch memory

### Feature 3: MCP Server Integration
**Problem:** Agents can't natively query AgentMemory.
**Solution:** Expose AgentMemory as an MCP (Model Context Protocol) server.
**Approaches:**
- Implement MCP server with `memory/recall`, `memory/capture`, `memory/search` tools
- Agents call memory via MCP instead of reading files
- Register with `mcporter`

### Feature 4: Web Dashboard
**Problem:** Browsing memories in terminal is limited.
**Solution:** Lightweight web UI to browse, search, and manage memories.
**Approaches:**
- Flask/FastAPI backend serving SQLite data
- Simple HTML/JS frontend
- Search + filter + visualize memory graph
- Run via `agentmemory dashboard` command

---

## Technical Architecture

```
agentmemory/
├── agentmemory/
│   ├── __init__.py
│   ├── cli.py              # Click CLI (all commands)
│   ├── core.py             # SQLite engine + embedding storage
│   ├── semantic.py         # Pluggable backends (TF-IDF / ST)
│   ├── decay.py            # Confidence decay + reinforcement
│   ├── summarize.py        # Extractive summarization
│   ├── sync.py             # CLAUDE.md generation
│   ├── export.py           # Markdown export
│   ├── hooks.py            # Git hooks install/uninstall
│   └── (tomorrow: mcp.py, dashboard.py, auto_capture.py)
├── tests/
│   ├── test_core.py
│   ├── test_semantic.py
│   ├── test_decay.py
│   ├── test_summarize.py
│   └── test_backends.py
├── .github/workflows/ci.yml
├── pyproject.toml
├── README.md
├── LAUNCH.md               # Launch post templates
└── TOMORROW.md             # This file
```

### Dependencies

**Core:** click, rich, numpy
**Optional:** sentence-transformers (for embeddings backend)
**Dev:** pytest, pytest-cov, ruff

### Database Schema

```sql
memories (id, project, session_id, timestamp, category, content, confidence, source, tags, metadata)
projects (name, description, created_at, updated_at, context)
embeddings (memory_id, model_name, embedding_json, created_at)
```

---

## Problems AgentMemory Solves

1. **Session amnesia** — Agents forget everything between sessions
2. **Re-explaining code** — Users waste time re-teaching agents
3. **Token waste** — Re-reading files burns money
4. **Tool lock-in** — Memory trapped in one agent (Claude-only, etc.)
5. **Cloud dependency** — Other solutions require APIs/SaaS
6. **Shallow context** — No semantic relationships between memories
7. **Static docs** — CLAUDE.md gets stale
8. **No learning** — Agents don't improve over time

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python | Universal, pip-installable, agents love it |
| Storage | SQLite | Single file, portable, no daemon needed |
| CLI framework | Click | Standard, generates `--help` automatically |
| Semantic search default | TF-IDF + numpy | No heavy deps, works everywhere |
| Semantic search optional | sentence-transformers | Better quality when installed |
| Config location | `~/.agent-memory/` | Follows Unix conventions |
| Project detection | Git remote + cwd name | Auto-detects project context |
| Agent integration | CLAUDE.md file | Any agent that reads text works |

---

## How to Resume Tomorrow

```bash
cd C:\Users\vishn\projects\agentmemory

# Check status
agentmemory stats

# Run tests
python -m pytest tests/ -v

# Check linting
python -m ruff check agentmemory/ tests/

# View this file
cat TOMORROW.md
```

---

## Context for AI Assistant

> **Note to future assistant:** This project is a side project by a developer who wants to build an open-source product that helps everyone. The user is technical and follows agile development. We've completed 4 sprints and are planning 4 more. The user prefers English. The project is at https://github.com/Vish150988/agentmemory.
>
> **Tomorrow's priorities:**
> 1. Auto-capture from agent sessions
> 2. Team sync (shared memory via git)
> 3. MCP server integration
> 4. Web dashboard
>
> **Current state:** 18 tests passing, CI green, launched on Twitter, ready for Reddit/HN.
