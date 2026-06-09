# Sample Prompt

Use this prompt directly with the `/run-research-workflow` endpoint:

```json
{
  "prompt": "Research MCP frameworks for enterprise adoption and create an execution plan.",
  "dry_run": true
}
```

## What the Agent Does

1. **PlannerAgent** breaks the prompt into 6 steps
2. **ResearchAgent** synthesizes a comprehensive analysis of MCP (Model Context Protocol) frameworks, their enterprise adoption landscape, key players, challenges, and recommendations
3. **MemoryAgent** stores the research summary and each key insight into the persistent ChromaDB vector store for future retrieval
4. **ExecutionAgent** fires Composio actions to:
   - Create a Notion research report page
   - Create 4 actionable Linear issues
   - Open a GitHub issue tracking the initiative
   - Post a rich Slack message with Block Kit blocks and artifact links
5. **TraceLogger** records every action, tool call, input, output, timestamp, and status

## Expected Response (dry_run=true)

```json
{
  "run_id": "abc123...",
  "status": "completed",
  "dry_run": true,
  "plan": {
    "topic": "MCP frameworks for enterprise adoption",
    "steps": [...]
  },
  "research": {
    "topic": "MCP (Model Context Protocol) Frameworks for Enterprise Adoption",
    "key_insights": [
      "MCP standardises AI-to-tool communication the way HTTP standardised web requests",
      "Security and access control are the #1 adoption barrier in regulated industries",
      ...
    ]
  },
  "memory": {
    "docs_stored": 7,
    "prior_context_retrieved": 0
  },
  "execution_results": {
    "notion": { "success": true, "simulated": true, "data": { "url": "https://notion.so/..." } },
    "linear": [ ... ],
    "github": { "success": true, "simulated": true, "data": { "html_url": "https://github.com/..." } },
    "slack":  { "success": true, "simulated": true, "data": { "ok": true } }
  },
  "trace_summary": { "total_actions": 9, "success": 9, "simulated": 4, "error": 0 },
  "trace": [...]
}
```

## Other Prompts to Try

```json
{ "prompt": "Research vector databases for enterprise AI workloads and create tasks.", "dry_run": true }
```

```json
{ "prompt": "Analyse LLM gateway patterns for Fortune 500 deployment and build an action plan.", "dry_run": true }
```

```json
{ "prompt": "Compare RAG architectures for compliance-heavy industries and produce deliverables.", "dry_run": false }
```
