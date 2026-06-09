# System Design — Enterprise Memory Execution Agent

## 1. Design Goals

| Goal | Approach |
|------|---------|
| Autonomous cross-app execution | Composio unified API — one SDK, 5+ apps |
| Persistent enterprise memory | ChromaDB (vector) + SQLite (structured) |
| Multi-agent specialisation | 5 agents with single responsibilities |
| Production observability | Per-action trace log (JSONL + SQLite) |
| Safe demo mode | Dry-run simulation — no real API credentials needed |
| Research quality assurance | CriticAgent with confidence scoring + retry loop |

---

## 2. Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI  HTTP Layer                       │
│  POST /run-research-workflow   GET /runs   GET /memory/search│
└──────────────────────────────┬──────────────────────────────┘
                               │
              ┌────────────────▼────────────────┐
              │   research_to_execution.py       │
              │   (Orchestration Workflow)       │
              └────┬────┬────┬────┬────┬────────┘
                   │    │    │    │    │
          Planner  │    │    │    │    │  Executor
                   ▼    │    │    │    ▼
            PlannerAgent│    │    │ExecutionAgent
                        │    │    │    │
                 Memory │    │    │    ├─ NOTION_CREATE_PAGE
                        ▼    │    │    ├─ LINEAR_CREATE_ISSUE
               MemoryAgent   │    │    ├─ GITHUB_CREATE_ISSUE
               ┌──────────┐  │    │    ├─ SLACK_SEND_MESSAGE
               │ChromaDB  │  │    │    └─ GMAIL_SEND_EMAIL
               │SQLite    │  │    │         │
               └──────────┘  │    │    ComposioClient
                        Research   │    ┌────────────┐
                             ▼    │    │ dry_run=True│
                     ResearchAgent│    │  simulate() │
                                  │    │ dry_run=False│
                             Critic    │  execute()  │
                                  ▼    └────────────┘
                          CriticAgent
                          (confidence score,
                           retry trigger)
```

---

## 3. Data Model

### SQLite Tables

```sql
runs
  id TEXT PK
  prompt TEXT
  status TEXT          -- running | completed | failed
  dry_run INTEGER
  plan TEXT (JSON)
  research_summary TEXT (JSON)
  execution_results TEXT (JSON)
  trace_entries TEXT (JSON)
  error_message TEXT
  created_at TEXT
  completed_at TEXT

execution_logs
  id TEXT PK
  run_id TEXT FK → runs.id
  agent_name TEXT
  action TEXT
  tool TEXT
  target_app TEXT
  input_data TEXT (JSON)
  output_data TEXT (JSON)
  status TEXT
  duration_ms INTEGER
  timestamp TEXT

memory_records
  id TEXT PK
  topic TEXT
  summary TEXT
  recommendation TEXT
  sources TEXT (JSON)
  confidence REAL       -- 0.0–1.0 (from critic score / 100)
  run_id TEXT
  version INTEGER       -- increments on topic re-research
  created_at TEXT
  updated_at TEXT

agent_outputs
  id TEXT PK
  run_id TEXT FK → runs.id
  agent_name TEXT
  output_type TEXT
  output_data TEXT (JSON)
  created_at TEXT
```

### ChromaDB Collection: `enterprise_memory`

Documents stored:
- Full research summaries (type=`research_summary`)
- Individual key insights (type=`key_insight`)

Queried via cosine similarity for prior context retrieval.

---

## 4. Agent Contracts

### PlannerAgent
- **Input**: `prompt: str`
- **Output**: `{ topic: str, steps: [{step, agent, action, description}] }`
- **LLM**: Yes
- **Side effects**: TraceLogger entry

### ResearchAgent
- **Input**: `topic: str, context?: list[dict], feedback?: list[str]`
- **Output**: `{ topic, summary, key_insights, linear_tasks, sources }`
- **LLM**: Yes
- **Side effects**: TraceLogger entry

### CriticAgent
- **Input**: `research: dict`
- **Output**: `{ confidence_score, quality_rating, strengths, weaknesses, improvements, approved }`
- **LLM**: Yes
- **Side effects**: TraceLogger entry
- **Retry trigger**: if `approved=False`, ResearchAgent re-runs with `feedback`

### MemoryAgent
- **Input**: `content, metadata` / `query, n_results` / `research, critique, run_id`
- **Output**: `doc_id` / `list[{content, metadata, distance}]` / `record_id`
- **LLM**: No
- **Storage**: ChromaDB + SQLite

### ExecutionAgent
- **Input**: `research: dict`
- **Output**: `{ notion, linear[], github, slack, gmail }` results
- **LLM**: No
- **Tool calls**: Composio (5 actions)
- **Retry**: up to `MAX_RETRIES` (default 3) with exponential backoff

---

## 5. Retry and Failure Recovery

```
ExecutionAgent._execute_with_retry(fn, label, **kwargs):
  for attempt in 1..MAX_RETRIES:
    result = fn(**kwargs)
    if result.success: return result, attempt
    if not dry_run:
      sleep(2^(attempt-1))   # 1s, 2s, 4s
  return last_result, MAX_RETRIES
```

In `dry_run=True` mode, simulated results always return `success=True` on the first attempt, so retry logic is effectively a no-op.

---

## 6. Memory Versioning

Every time the same topic is researched, `memory_records.version` increments:

```
Run 1: topic="MCP Frameworks" → version=1, confidence=0.88
Run 2: topic="MCP Frameworks" → version=2, confidence=0.91
```

`GET /memory/search?q=MCP` returns all versions ordered by confidence DESC.

---

## 7. Critic Feedback Loop

```
research = ResearchAgent.research(topic)
critique = CriticAgent.review(research)

if not critique.approved:
    improvements = critique.improvements   # list of specific suggestions
    research = ResearchAgent.research(topic, feedback=improvements)
    critique = CriticAgent.review(research)   # re-score
```

The retry happens at most once (to avoid infinite loops). Final confidence score is stored in `memory_records.confidence`.

---

## 8. Trace Schema

Every agent action produces a TraceEntry:

```json
{
  "run_id": "abc-123",
  "agent_name": "ExecutionAgent",
  "action_type": "create_github_issue",
  "target_app": "github",
  "input":  { "title": "[Research] MCP..." },
  "output": { "issue_number": 42, "html_url": "..." },
  "status": "simulated",
  "duration_ms": 12,
  "timestamp": "2026-06-08T10:23:45.123456+00:00"
}
```

Persisted to:
1. `logs/execution_traces.jsonl` — append-only JSONL (human-readable audit trail)
2. `data/run_history.db` → `execution_logs` table (queryable)
3. In-memory list on `TraceLogger` (returned in API response)

---

## 9. API Design

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service status + config + DB stats |
| POST | `/run-research-workflow` | Execute full pipeline |
| GET | `/runs` | List all runs (paginated) |
| GET | `/runs/{run_id}` | Full run + trace + agent outputs |
| GET | `/memory` | List knowledge records |
| GET | `/memory/search` | Hybrid/vector/keyword search |
| GET | `/stats` | Aggregate stats for dashboard |

---

## 10. Scalability Path

| Concern | Current | Production Path |
|---------|---------|----------------|
| Memory persistence | In-process ChromaDB | Persistent ChromaDB or Pinecone |
| Run storage | SQLite | PostgreSQL |
| Concurrency | Single-process | FastAPI + Uvicorn workers + task queue |
| LLM calls | Sync | Async with httpx |
| Streaming | Not implemented | SSE endpoint for live trace events |
| Multi-tenant | Single namespace | Per-org ChromaDB collections |
