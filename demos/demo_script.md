# Demo Script — Enterprise Memory Execution Agent

**Target audience:** Hackathon judges / technical evaluators  
**Duration:** ~5 minutes  
**Prerequisites:** App running at `http://localhost:8000` (see README setup)

---

## 1. Health Check (30 sec)

Open a browser or terminal and hit the root endpoint:

```bash
curl http://localhost:8000/
```

Expected: JSON showing LLM provider, Composio status, dry_run setting, and available endpoints.

**Talking point:** "The agent is fully configurable — swap LLM provider, enable real Composio execution, or run in dry-run mode for demos."

---

## 2. Run the Core Workflow (2 min)

```bash
curl -X POST http://localhost:8000/run-research-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Research MCP frameworks for enterprise adoption and create an execution plan.",
    "dry_run": true
  }'
```

Walk through the response live, highlighting each section:

| Section | Highlights |
|---------|-----------|
| `plan` | Show the 6-step decomposition from PlannerAgent |
| `research.key_insights` | 6 distilled enterprise insights |
| `memory.docs_stored` | 7 documents stored to ChromaDB |
| `execution_results.notion` | Simulated Notion page URL |
| `execution_results.linear` | 4 Linear issues created |
| `execution_results.github` | GitHub issue number + URL |
| `execution_results.slack` | Slack message with Block Kit |
| `trace_summary` | 9 total actions, all logged |

**Talking point:** "In 5 seconds, 5 agents collaborated — planner decomposed the request, researcher synthesised knowledge, memory stored findings, and the execution agent fired 4 simultaneous Composio actions across apps."

---

## 3. Show Persistent Memory (1 min)

```bash
# Query memory for prior context
curl "http://localhost:8000/memory?query=MCP+enterprise&limit=5"
```

Then run a second workflow referencing the same topic:

```bash
curl -X POST http://localhost:8000/run-research-workflow \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Deep dive into MCP security patterns for financial services.",
    "dry_run": true
  }'
```

Show `memory.prior_context_retrieved: 3` — the agent recalled prior research.

**Talking point:** "This is what makes it an *enterprise* agent — it builds a persistent knowledge base across runs. The memory persists between restarts."

---

## 4. Execution History (30 sec)

```bash
# List all runs
curl http://localhost:8000/runs

# Get a specific run by ID
curl http://localhost:8000/runs/<run_id_from_previous_response>
```

**Talking point:** "Every run is logged to SQLite with full trace data — you get an audit trail of every agent action, tool call, and API response."

---

## 5. Switch to Real Execution (30 sec — if credentials set)

Update `.env`:
```
COMPOSIO_API_KEY=real_key
DRY_RUN=false
```

Restart, re-run workflow with `"dry_run": false`. Show real Notion page, Slack message, Linear issue.

**Talking point:** "Flipping one flag switches from simulation to real execution. The same code path runs — Composio handles auth and API normalisation across all four apps."

---

## Key Differentiators to Emphasise

1. **Multi-agent architecture** — 5 specialised agents, not one monolithic LLM call
2. **Persistent memory** — ChromaDB vector store survives restarts, builds context over time
3. **4+ apps via Composio** — Notion, Linear, GitHub, Slack from a single API key
4. **Full audit trail** — every action logged with run_id, agent, tool, input, output, timestamp
5. **Dual mode** — dry_run for demos, real execution with a config change

---

## Trace Log Location

```bash
cat logs/execution_traces.jsonl | python3 -m json.tool | head -80
```

Shows timestamped JSONL records proving autonomous API calls happened.
