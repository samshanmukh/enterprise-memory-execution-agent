# Enterprise Memory Execution Agent

> **Hackathon submission** — an autonomous, multi-agent enterprise research assistant that **remembers** previous work, **validates** its own output, and **executes** deliverables across five real business apps — all from a single natural language prompt.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-2.0-green.svg)](https://fastapi.tiangolo.com)
[![Composio](https://img.shields.io/badge/Composio-powered-purple.svg)](https://composio.dev)
[![Tests](https://img.shields.io/badge/tests-41%20passing-brightgreen.svg)](#tests)

---

## The Problem

Enterprise teams waste **2–4 hours per research cycle** manually writing reports, filing tickets, and notifying stakeholders across disconnected tools. Today's AI assistants either only *talk* (no actions) or only *act* (no reasoning) — and none of them *remember* across sessions.

## The Solution

One natural language prompt → five specialised agents → five real-world deliverables in under 10 seconds.

```
"Research MCP frameworks for enterprise adoption and create an execution plan."
                                    ↓
              ┌─────────────────────────────────────┐
              │  Planner  →  Research  →  Critic    │
              │      ↑ retry if confidence < 70      │
              │  Memory (store) → Executor (5 apps) │
              └─────────────────────────────────────┘
                                    ↓
   Notion report · Linear tasks · GitHub issue · Slack summary · Gmail email
                                    ↓
              All findings stored in persistent vector + SQL memory
```

---

## Architecture

### Five Specialised Agents

| Agent | Role | LLM? |
|-------|------|------|
| **PlannerAgent** | Decomposes the prompt into an ordered execution plan | ✅ |
| **ResearchAgent** | Synthesises a structured analysis — accepts critic feedback for retries | ✅ |
| **CriticAgent** | Scores research quality (0–100), approves or triggers a research retry | ✅ |
| **MemoryAgent** | Reads/writes ChromaDB (semantic) + SQLite (structured, versioned) | — |
| **ExecutionAgent** | Fires Composio actions across 5 apps with retry + exponential backoff | — |

### Critic Feedback Loop

```
research = ResearchAgent.research(topic)
critique = CriticAgent.review(research)      # confidence score 0-100

if confidence < 70:
    research = ResearchAgent.research(topic, feedback=critique.improvements)
    critique  = CriticAgent.review(research)  # re-score
```

### Five App Integrations (via Composio)

| App | What Gets Created |
|-----|-----------------|
| **Notion** | Research report page in your database |
| **Linear** | 4 actionable engineering issues |
| **GitHub** | Issue tracking the research initiative |
| **Slack** | Block Kit summary with artifact links |
| **Gmail** | Stakeholder email with full summary |

### Persistent Memory

| Layer | Technology | What's Stored |
|-------|-----------|--------------|
| Vector store | ChromaDB | Research summaries + key insights (semantic search) |
| Structured store | SQLite | Knowledge records with confidence, version, sources |

Memory **survives between runs** and is retrieved automatically on related queries.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API Server | FastAPI + Uvicorn |
| LLM | Anthropic Claude (or any OpenAI-compatible endpoint) |
| Tool Execution | Composio |
| Vector Memory | ChromaDB |
| Run History | SQLite (4 tables) |
| Dashboard | Streamlit |
| Tests | pytest (41 tests) |
| Config | python-dotenv |

---

## Project Structure

```
enterprise-memory-execution-agent/
├── app/
│   ├── main.py                         # FastAPI app (6 endpoints)
│   ├── config.py                       # All env var settings
│   ├── agents/
│   │   ├── planner_agent.py            # LLM plan decomposition
│   │   ├── research_agent.py           # LLM synthesis + feedback loop
│   │   ├── critic_agent.py             # Quality validation + confidence score
│   │   ├── memory_agent.py             # ChromaDB + SQLite read/write
│   │   └── execution_agent.py          # Composio orchestration + retry
│   ├── tools/
│   │   ├── llm_client.py               # Anthropic / OpenAI abstraction
│   │   ├── composio_client.py          # Composio wrapper + dry-run mock
│   │   ├── github_tools.py
│   │   ├── slack_tools.py
│   │   ├── notion_tools.py
│   │   ├── linear_tools.py
│   │   └── gmail_tools.py
│   ├── memory/
│   │   ├── vector_memory.py            # ChromaDB with keyword fallback
│   │   └── run_history.py              # SQLite CRUD (4 tables)
│   ├── models/
│   │   └── agents.py                   # Pydantic models for all I/O
│   ├── workflows/
│   │   └── research_to_execution.py    # Main orchestration pipeline
│   └── logs/
│       └── execution_trace.py          # Per-action trace logger + timer
├── dashboard/
│   └── app.py                          # Streamlit dashboard (4 pages)
├── tests/
│   ├── test_planner.py                 # 6 tests
│   ├── test_research.py                # 8 tests
│   ├── test_critic.py                  # 7 tests
│   ├── test_memory.py                  # 9 tests
│   └── test_composio.py               # 11 tests
├── docs/
│   ├── architecture.md
│   ├── system-design.md
│   ├── demo-script.md
│   └── pitch.md
├── demos/
│   ├── sample_prompt.md
│   └── demo_script.md
├── .env.example
└── requirements.txt
```

---

## Setup

### 1. Clone & install

```bash
git clone https://github.com/your-org/enterprise-memory-execution-agent
cd enterprise-memory-execution-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
```

Minimum config to run in mock mode (no real API calls):

```env
# Even a placeholder key triggers mock fallback if invalid
ANTHROPIC_API_KEY=your_key_here
DRY_RUN=true
```

Full config for real execution:

```env
ANTHROPIC_API_KEY=sk-ant-...
COMPOSIO_API_KEY=your_composio_key
GITHUB_REPO_OWNER=your-org
GITHUB_REPO_NAME=your-repo
SLACK_CHANNEL_ID=C1234567890
NOTION_DATABASE_ID=your-db-id
LINEAR_TEAM_ID=your-team-id
GMAIL_RECIPIENT=team@yourcompany.com
DRY_RUN=false
```

### 3. Run

```bash
# API server
uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)

# Dashboard (separate terminal)
streamlit run dashboard/app.py
# → http://localhost:8501

# Tests
python -m pytest tests/ -v
```

Or use the Makefile:

```bash
make run        # start API server
make dashboard  # start Streamlit
make test       # run all 41 tests
make demo       # run full demo via curl
```

---

## API Reference

### `GET /health`

Returns service status, all configured agents and apps, and live database stats.

### `POST /run-research-workflow`

```bash
curl -X POST http://localhost:8000/run-research-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Research MCP frameworks for enterprise adoption and create an execution plan.",
    "dry_run": true
  }'
```

**Request:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `prompt` | string | required | Research question |
| `dry_run` | bool | `true` | Simulate Composio (no real API calls) |
| `run_id` | string | auto UUID | Optional custom run ID |

**Response includes:**
- `plan` — 6-step decomposed plan
- `research` — topic, key insights, summary excerpt, sources
- `critique` — confidence score, quality rating, approved, strengths, weaknesses
- `memory` — docs stored, prior context retrieved, knowledge record ID
- `execution_results` — per-app results (notion, linear, github, slack, gmail)
- `trace` — every agent action with input, output, status, duration
- `trace_summary` — totals and duration

### `GET /runs` · `GET /runs/{run_id}`

List all runs or get a specific run with full trace, execution logs, and agent outputs.

### `GET /memory`

List structured knowledge records from SQLite.

### `GET /memory/search?q=...&mode=hybrid|vector|keyword`

Search persistent memory across both ChromaDB and SQLite.

---

## Demo Flow

### Step 1 — Run the core workflow

```bash
curl -X POST http://localhost:8000/run-research-workflow \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Research MCP frameworks for enterprise adoption and create an execution plan.", "dry_run": true}'
```

Response highlights:
- `critique.confidence_score: 88` — CriticAgent validated the research
- `memory.docs_stored: 7` — ChromaDB has 7 new documents
- `execution_results` — 5 apps, all `success: true, simulated: true`
- `trace_summary.total_actions: 17`

### Step 2 — Verify persistent memory

```bash
curl "http://localhost:8000/memory/search?q=MCP+enterprise&mode=hybrid"
```

### Step 3 — Run a second related workflow

```bash
curl -X POST http://localhost:8000/run-research-workflow \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Deep dive on MCP security and compliance for financial services.", "dry_run": true}'
```

Check `memory.prior_context_retrieved: 3` — it recalled context from Run 1.

### Step 4 — Browse the dashboard

```bash
streamlit run dashboard/app.py
```

Open `http://localhost:8501` and explore:
- **Dashboard** — metrics, recent runs table, agent/app architecture
- **New Run** — submit a prompt, see live results with confidence bar
- **Run Details** — expandable agent timeline per trace entry
- **Memory Explorer** — search and browse the knowledge base

### Step 5 — Real execution

Set `DRY_RUN=false` and add real credentials. Same code, same agents, same trace — Composio handles auth across all five apps.

---

## Execution Trace

Every action is logged with:

```json
{
  "run_id": "abc-123",
  "agent_name": "ExecutionAgent",
  "action_type": "create_github_issue",
  "target_app": "github",
  "input":  { "title": "[Research] MCP Frameworks for Enterprise Adoption" },
  "output": { "issue_number": 42, "html_url": "https://github.com/org/repo/issues/42" },
  "status": "simulated",
  "duration_ms": 14,
  "timestamp": "2026-06-08T10:23:45.123456+00:00"
}
```

Stored in:
- `logs/execution_traces.jsonl` — append-only JSONL audit trail
- `data/run_history.db` → `execution_logs` table

---

## Tests

```
tests/test_planner.py    6 tests  — plan schema, steps, trace logging
tests/test_research.py   8 tests  — research output, context, feedback loop
tests/test_critic.py     7 tests  — confidence scoring, approval logic, trace
tests/test_memory.py     9 tests  — ChromaDB store/retrieve, SQLite CRUD
tests/test_composio.py  11 tests  — dry-run simulation for all 5 apps

Total: 41 tests, 0 failures
```

```bash
python -m pytest tests/ -v
```

---

## Hackathon Alignment

| Requirement | Implementation |
|-------------|---------------|
| Execute across 3+ apps | **5 apps**: Notion, Linear, GitHub, Slack, Gmail |
| Composio as execution layer | `ComposioClient` wraps every tool call |
| Multi-agent architecture | **5 specialised agents** with single responsibilities |
| Persistent memory | ChromaDB (semantic) + SQLite (versioned knowledge records) |
| Full audit trail | JSONL + SQLite — every action logged |
| Runnable MVP | `uvicorn app.main:app --reload` |
| Dry-run mode | `"dry_run": true` — no credentials needed |
| Research quality gate | CriticAgent confidence scoring + retry loop |
| Dashboard | Streamlit — 4 pages, real-time data from API |
| Unit tests | 41 tests across all core services |

---

## Future Roadmap

1. **Streaming API** — SSE endpoint for live trace events during execution
2. **Persistent ChromaDB** — survive restarts with `PersistentClient` or Pinecone
3. **More Composio apps** — Confluence, Jira, HubSpot, Salesforce
4. **Feedback loops** — Linear issue comments flow back into memory
5. **Scheduled research** — cron-triggered runs with delta detection
6. **Multi-tenant** — per-org memory namespacing and RBAC
7. **Streaming dashboard** — React frontend with real-time trace visualisation

---

## License

MIT
