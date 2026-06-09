from __future__ import annotations

import json
import logging
from typing import Any

from app.logs.execution_trace import TraceLogger
from app.tools.llm_client import chat, extract_json

logger = logging.getLogger(__name__)

_MOCK_RESEARCH: dict[str, Any] = {
    "topic": "MCP (Model Context Protocol) Frameworks for Enterprise Adoption",
    "summary": """## Executive Summary

The Model Context Protocol (MCP) is an open standard developed by Anthropic that defines how AI models securely connect to external data sources, tools, and services. As enterprises accelerate agentic AI deployments, MCP frameworks are fast becoming critical integration infrastructure.

## What is MCP?

MCP provides a universal interface between large language models and the tools they need to act in the world. Instead of every AI application building bespoke integrations, MCP standardises the protocol layer — similar to how HTTP standardised web communication.

**Core concepts:**
- **Hosts**: LLM applications (Claude, custom agents) that initiate connections
- **Servers**: Lightweight processes exposing tools, resources, and prompts
- **Clients**: Protocol clients inside the host managing server connections

## Enterprise Adoption Landscape (2025)

| Segment | Adoption Stage | Primary Use Case |
|---------|---------------|-----------------|
| Big Tech | Production | Internal developer tooling |
| Financial Services | Pilot | Compliance document retrieval |
| Healthcare | Evaluation | Clinical decision support |
| SaaS Vendors | Building | Product feature expansion |

**Growth drivers:**
1. Shift from chatbots to autonomous AI agents
2. Need for auditable, secure tool access
3. Vendor-neutral interoperability requirements

## Top MCP Frameworks & Tools

| Framework | Language | Strengths |
|-----------|----------|-----------|
| `@modelcontextprotocol/sdk` | TypeScript | Official, battle-tested |
| `mcp` (Python SDK) | Python | Async-native, rich typing |
| FastMCP | Python | Rapid server prototyping |
| Spring AI MCP | Java | Enterprise Spring integration |
| Composio | Multi | Managed connectors for 200+ apps |

## Key Adoption Challenges

1. **Security & access control** — MCP servers can expose sensitive systems; fine-grained auth is immature
2. **Observability** — Tracing multi-hop agent calls across MCP servers lacks standard tooling
3. **State management** — Long-running agentic sessions require durable context persistence
4. **Latency** — Round-trips through multiple MCP servers add measurable latency
5. **Discovery** — No standard registry for finding available MCP servers in an org

## Recommendations

1. Begin with read-only MCP servers for internal knowledge bases (low risk, high value)
2. Adopt an **MCP Gateway** pattern to centralise auth, rate-limiting, and logging
3. Instrument every MCP call with OpenTelemetry traces from day one
4. Evaluate Composio as a managed integration layer (reduces ops burden significantly)
5. Contribute to open standards: join the MCP Working Group

## Action Items

- [ ] Set up an internal MCP server registry (Confluence/Notion page)
- [ ] Draft security policy: what data can MCP servers expose?
- [ ] Prototype MCP integration with top 3 internal tools
- [ ] Evaluate Composio enterprise tier vs self-hosted MCP servers
- [ ] Define SLOs for MCP server response times""",
    "key_insights": [
        "MCP standardises AI-to-tool communication the way HTTP standardised web requests",
        "Security and access control are the #1 adoption barrier in regulated industries",
        "Composio reduces the operational burden of managing dozens of MCP connectors",
        "Python ecosystem has the most mature MCP tooling for rapid prototyping",
        "Enterprise adoption is accelerating in 2025, driven by autonomous agent use cases",
        "An MCP Gateway pattern is emerging as the best-practice architecture for large orgs",
    ],
    "linear_tasks": [
        {
            "title": "Set up internal MCP server registry",
            "description": "Create a central Notion/Confluence page listing all internal MCP servers, their capabilities, owners, and SLOs. This enables discoverability across teams.",
        },
        {
            "title": "Draft MCP security policy",
            "description": "Define what data categories MCP servers can expose, authentication requirements, audit logging standards, and incident response procedures.",
        },
        {
            "title": "Prototype MCP integration with top 3 internal tools",
            "description": "Build lightweight MCP server wrappers for our highest-value internal tools. Target: JIRA, Confluence, and Datadog. Measure latency and developer adoption.",
        },
        {
            "title": "Evaluate Composio enterprise tier",
            "description": "Run a 30-day pilot with Composio enterprise. Measure: integration coverage, reliability, cost vs self-hosted, and security audit results.",
        },
    ],
    "sources": [
        "Anthropic MCP Documentation — modelcontextprotocol.io",
        "GitHub: modelcontextprotocol/python-sdk",
        "Composio Platform Documentation — composio.dev/docs",
        "Enterprise AI Adoption Report 2025 — a16z",
        "OWASP LLM Top 10 — owasp.org",
    ],
}

_SYSTEM = """You are a senior enterprise technology research analyst with deep expertise in AI infrastructure, developer tooling, and enterprise software adoption patterns.

Produce a comprehensive, structured research report for enterprise decision-makers. Return ONLY a JSON object with this exact schema:

{
  "topic": "<full topic title>",
  "summary": "<rich markdown report — use ## headers, tables, bullet lists — minimum 600 words>",
  "key_insights": ["<concise insight>", ...],
  "linear_tasks": [
    {"title": "<task title>", "description": "<2-3 sentence task description>"},
    ...
  ],
  "sources": ["<source name and URL>", ...]
}

The summary must include: executive summary, current landscape, framework comparison table, adoption challenges, and concrete recommendations."""


class ResearchAgent:
    def __init__(self, trace: TraceLogger):
        self.trace = trace

    def research(
        self,
        topic: str,
        context: list[dict] | None = None,
        feedback: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Research a topic. Optionally accepts:
        - context: prior memory docs retrieved by MemoryAgent
        - feedback: improvement suggestions from CriticAgent for a retry pass
        """
        logger.info("ResearchAgent synthesising: %s", topic)

        context_block = ""
        if context:
            snippets = "\n".join(f"- {c['content'][:400]}" for c in context[:3])
            context_block = f"\n\nRelevant prior context from persistent memory:\n{snippets}"

        feedback_block = ""
        if feedback:
            items = "\n".join(f"- {f}" for f in feedback)
            feedback_block = f"\n\nCritic feedback — improve these areas in your analysis:\n{items}"

        raw = chat(
            system=_SYSTEM,
            user=f"Research topic: {topic}{context_block}{feedback_block}",
            max_tokens=4096,
            mock_response=json.dumps(_MOCK_RESEARCH),
        )
        research = extract_json(raw, _MOCK_RESEARCH)

        self.trace.log(
            agent_name="ResearchAgent",
            action_type="synthesize_topic",
            target_app="internal",
            input_data={
                "topic": topic,
                "context_docs": len(context or []),
                "feedback_items": len(feedback or []),
            },
            output_data={
                "topic": research.get("topic"),
                "insights_count": len(research.get("key_insights", [])),
                "tasks_count": len(research.get("linear_tasks", [])),
                "summary_length": len(research.get("summary", "")),
            },
            status="success",
        )
        return research
