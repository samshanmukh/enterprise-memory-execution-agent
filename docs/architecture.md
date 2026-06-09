# Architecture — Enterprise Memory Execution Agent

## Overview

A multi-agent pipeline that accepts a natural language research prompt and autonomously produces deliverables across Notion, Linear, GitHub, and Slack, while maintaining a persistent memory layer across runs.

```
User Prompt
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI  /run-research-workflow        │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │     PlannerAgent      │  LLM → structured step plan
              └───────────┬───────────┘
                          │ plan (6 steps)
                          ▼
              ┌───────────────────────┐
              │     MemoryAgent       │  retrieve prior context
              │   (ChromaDB query)    │
              └───────────┬───────────┘
                          │ prior context docs
                          ▼
              ┌───────────────────────┐
              │    ResearchAgent      │  LLM → structured research JSON
              └───────────┬───────────┘
                          │ research output
                          ▼
              ┌───────────────────────┐
              │     MemoryAgent       │  store summary + insights
              │   (ChromaDB write)    │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │    ExecutionAgent     │
              │  (Composio ToolSet)   │
              └──┬────┬────┬────┬────┘
                 │    │    │    │
         Notion  │    │    │    │  Slack
                 ▼    │    │    ▼
            Page      │    │   Message
         created      │    │  (Block Kit)
                       │    │
                Linear  │    │  GitHub
                Issues   ▼    ▼
                created  Issue created

                          │
                          ▼
              ┌───────────────────────┐
              │     TraceLogger       │  JSONL + SQLite audit trail
              └───────────────────────┘
```

## Components

### Agents

| Agent | Responsibility | LLM? | External Call? |
|-------|---------------|------|---------------|
| PlannerAgent | Decomposes prompt into ordered steps | Yes | No |
| ResearchAgent | Synthesises topic into structured research | Yes | No |
| MemoryAgent | Stores/retrieves persistent context | No | ChromaDB |
| ExecutionAgent | Fires Composio actions across apps | No | Composio API |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| API Server | FastAPI + Uvicorn | HTTP endpoints |
| LLM Client | Anthropic / OpenAI | Language model calls |
| Vector Store | ChromaDB (in-memory) | Semantic memory retrieval |
| Run History | SQLite | Audit log and run persistence |
| Tool Executor | Composio | Unified API for 200+ app integrations |
| Trace Logger | JSONL file | Per-action audit trail |

### Composio Actions Used

| App | Action | Composio Action ID |
|-----|--------|-------------------|
| Notion | Create page in database | `NOTION_CREATE_PAGE` |
| Linear | Create issue | `LINEAR_CREATE_LINEAR_ISSUE` |
| GitHub | Create issue | `GITHUB_CREATE_AN_ISSUE` |
| Slack | Send channel message | `SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL` |

## Data Flow

1. `POST /run-research-workflow` creates a run record in SQLite
2. PlannerAgent calls LLM → returns `{ topic, steps[] }`
3. MemoryAgent queries ChromaDB for prior context on the topic
4. ResearchAgent calls LLM with topic + prior context → structured research JSON
5. MemoryAgent stores research summary and each key insight as separate ChromaDB documents
6. ExecutionAgent instantiates a `ComposioClient` (real or mock) and fires 4 actions
7. TraceLogger writes each action to `logs/execution_traces.jsonl` and to SQLite
8. API returns the full result including trace

## Dry-Run Mode

When `dry_run=true` (or `COMPOSIO_API_KEY` is absent):
- `ComposioClient._simulate()` generates realistic mock responses
- Notion, Linear, GitHub, Slack return fake IDs, URLs, and timestamps
- All trace entries are marked `"status": "simulated"`
- Full workflow runs exactly as in production — only the final API calls differ

## Persistence

- **Memory** — ChromaDB collection `enterprise_memory` (in-memory; extend to persistent with `chromadb.PersistentClient(path="./chroma_data")`)
- **Run history** — `data/run_history.db` (SQLite)
- **Trace log** — `logs/execution_traces.jsonl` (append-only JSONL)

## Configuration

All configuration is via environment variables (`.env` file):

```
LLM_PROVIDER=anthropic          # anthropic | openai
LLM_MODEL=claude-sonnet-4-6     # or gpt-4o, etc.
ANTHROPIC_API_KEY=...
COMPOSIO_API_KEY=...
GITHUB_REPO_OWNER=...
SLACK_CHANNEL_ID=...
NOTION_DATABASE_ID=...
LINEAR_TEAM_ID=...
DRY_RUN=true
```

## Extension Points

- Add a **SchedulerAgent** to run research on a cron schedule
- Swap ChromaDB for a **persistent vector store** (Pinecone, Weaviate, pgvector)
- Add **streaming** to the API for live trace events via Server-Sent Events
- Integrate **more Composio apps** (Jira, Confluence, HubSpot) by adding tool files
- Add a **feedback loop** where Linear issue comments get stored back to memory
