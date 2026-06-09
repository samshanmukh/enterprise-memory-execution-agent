# Demo Script — Enterprise Memory Execution Agent v2

**Audience:** Hackathon judges  
**Duration:** 5 minutes  
**Prerequisites:** Server running at `http://localhost:8000`, dashboard at `http://localhost:8501`

---

## Minute 0:30 — Open Dashboard

Navigate to `http://localhost:8501`.

Show the **Dashboard** page:
- "5 agents, 5 apps, persistent memory"
- Architecture diagram with Planner → Research → Critic → Memory → Executor
- App row: Notion · Linear · GitHub · Slack · Gmail

**Talking point:** *"This isn't a chatbot. It's an autonomous enterprise employee — it reasons, validates its own work, remembers across sessions, and executes across five real business apps."*

---

## Minute 1:00 — Trigger Workflow

Go to **New Run**. Enter:

```
Research MCP frameworks for enterprise adoption and create an execution plan.
```

Keep **Dry Run** checked. Click **Run Workflow**.

While it runs (~3–8 seconds), narrate the pipeline:

> "Planner decomposes the prompt. Memory retrieves prior context. Research synthesises a comprehensive analysis. The Critic validates it — assigns a confidence score. If confidence is too low, research retries with the critic's feedback. Then Execution fires five Composio actions simultaneously."

---

## Minute 2:00 — Walk the Response

Result appears. Highlight:

| Section | What to show |
|---------|-------------|
| **Confidence score** | "88/100 — high quality" with progress bar |
| **Key insights** | 6 enterprise-specific findings |
| **Execution results** | 5 green checkmarks: Notion · Linear · GitHub · Slack · Gmail |
| **Trace summary** | "16 actions · 0 errors · 340ms total" |

Expand the raw JSON to show the full `trace` array.

**Talking point:** *"Every single action is logged with agent name, target app, input, output, status, and duration. Full audit trail. This is what enterprise-grade observability looks like."*

---

## Minute 2:45 — Run Details Page

Switch to **Run Details**. Select the run just completed.

Expand the agent timeline:

1. `PlannerAgent → decompose_request → internal ✅`
2. `MemoryAgent → retrieve_context → vector_store ✅`
3. `ResearchAgent → synthesize_topic → internal ✅`
4. `CriticAgent → validate_research → internal ✅`
5. `MemoryAgent → store_knowledge_record → sqlite ✅`
6. `ExecutionAgent → create_notion_report → notion 🔵`
7. `ExecutionAgent → create_linear_tasks → linear 🔵`
8. `ExecutionAgent → create_github_issue → github 🔵`
9. `ExecutionAgent → post_slack_summary → slack 🔵`
10. `ExecutionAgent → send_gmail_summary → gmail 🔵`

**Talking point:** *"Every agent step is visible. In production mode, the blue 'simulated' badges become green 'success' with real Notion URLs, GitHub issue numbers, and Slack timestamps."*

---

## Minute 3:30 — Persistent Memory

Run a **second workflow** with a related topic:

```
Deep dive on MCP security and compliance for financial services.
```

Show `memory.prior_context_retrieved: 3` — the agent pulled context from Run 1.

Navigate to **Memory Explorer**. Search `MCP enterprise`.

Show:
- Vector results from ChromaDB similarity search
- Knowledge records from SQLite with version numbers (`v1`, `v2`)

**Talking point:** *"The second run automatically recalled context from the first. This is true enterprise memory — not session-scoped, not ephemeral. It accumulates knowledge over time."*

---

## Minute 4:30 — Switch to Real Execution (30 sec)

Show the `.env` file:

```env
COMPOSIO_API_KEY=real_key
DRY_RUN=false
```

**Talking point:** *"One environment variable flip switches from simulation to real execution across all five apps. Same code, same agents, same trace format — Composio handles auth and API normalisation."*

---

## Closing

Navigate to `http://localhost:8000/docs` (Swagger UI).

> "Full OpenAPI spec. Five endpoints. Production-ready. Built in 24 hours for this hackathon — and designed to run in production for real."

**Key numbers:**
- 5 specialised agents
- 5 Composio app integrations
- 4 database tables
- 16+ traced actions per run
- 1 environment variable to go live

---

## Backup: cURL Demo

If Streamlit is unavailable:

```bash
# Health
curl http://localhost:8000/health | python3 -m json.tool

# Run workflow
curl -X POST http://localhost:8000/run-research-workflow \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Research MCP frameworks for enterprise adoption and create an execution plan.", "dry_run": true}' \
  | python3 -m json.tool

# Memory search
curl "http://localhost:8000/memory/search?q=MCP+enterprise&mode=hybrid"

# Run history
curl http://localhost:8000/runs | python3 -m json.tool
```
