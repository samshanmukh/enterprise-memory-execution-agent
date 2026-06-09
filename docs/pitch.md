# Pitch — Enterprise Memory Execution Agent

## The Problem

Enterprise teams spend hours manually researching topics, writing reports, creating tickets, and notifying stakeholders — across fragmented tools. AI assistants today either:

1. **Only talk** — LLMs that produce output but don't act
2. **Only act** — automation tools that execute but don't reason
3. **Have no memory** — each conversation starts from zero

The result: high-value research gets lost in chat logs, action items never make it to JIRA/Linear, and knowledge isn't reused across teams or time.

## The Solution

**Enterprise Memory Execution Agent** is a multi-agent system that *researches, remembers, and executes* — all from a single natural language prompt.

```
"Research MCP frameworks for enterprise adoption and create an execution plan."
          ↓
  5 agents collaborate in under 10 seconds
          ↓
  Notion report  +  Linear tasks  +  GitHub issue  +  Slack summary
          ↓
  All findings stored in persistent memory for future runs
```

## How It Works

| Agent | Role |
|-------|------|
| **Planner** | Breaks the prompt into an ordered execution plan |
| **Researcher** | Synthesises a comprehensive, structured analysis using an LLM |
| **Memory** | Stores findings in ChromaDB; retrieves prior context for future runs |
| **Executor** | Fires Composio API calls to create real deliverables across 4 apps |
| **Trace Logger** | Records every action with full audit trail |

## Hackathon Requirements

✅ **Executes across 4+ apps** — Notion, Linear, GitHub, Slack  
✅ **Composio as primary execution layer** — unified API with 200+ integrations  
✅ **Persistent memory** — ChromaDB vector store survives across runs  
✅ **Structured multi-agent architecture** — 5 specialised agents  
✅ **Full audit trail** — every tool call logged with timestamp, input, output, status  
✅ **Dry-run mode** — demo safely without real API credentials  
✅ **Runnable MVP** — `uvicorn app.main:app --reload`

## Demo Flow

1. `POST /run-research-workflow` with a research prompt
2. Watch 5 agents execute in sequence (< 10 seconds in dry-run)
3. Receive JSON with Notion URL, Linear issue links, GitHub issue number, Slack confirmation
4. Run again — memory agent surfaces prior research context
5. `GET /runs` — full audit history in SQLite

## Why This Wins

- **Real enterprise problem** — saves 2-4 hours of manual work per research cycle
- **Genuinely agentic** — not a single LLM call; multiple agents with specialised roles
- **Composio-native** — demonstrates deep integration with the judging platform
- **Persistent memory** — the one capability that makes it enterprise-grade vs. toy
- **Production-ready structure** — clean architecture, type hints, proper error handling, audit trail

## Future Roadmap

1. **Streaming API** — live trace events via SSE for real-time UI
2. **Persistent ChromaDB** — survive process restarts with Pinecone/pgvector
3. **More apps** — Confluence, HubSpot, Salesforce, Jira via Composio
4. **Feedback loop** — Linear comments flow back into memory
5. **Scheduled runs** — cron-triggered research with delta detection
6. **Multi-user** — per-user memory namespacing and RBAC

## Team

Built for the Composio Hackathon — demonstrating that enterprise AI needs more than chat: it needs agents that **remember** and **act**.
