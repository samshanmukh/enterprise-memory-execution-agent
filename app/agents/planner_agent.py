from __future__ import annotations

import json
import logging
from typing import Any

from app.logs.execution_trace import TraceLogger
from app.tools.llm_client import chat, extract_json

logger = logging.getLogger(__name__)

_MOCK_PLAN: dict[str, Any] = {
    "topic": "MCP frameworks for enterprise adoption",
    "steps": [
        {
            "step": 1,
            "agent": "research",
            "action": "synthesize_topic",
            "description": "Research MCP frameworks and the enterprise AI adoption landscape, producing a structured analysis.",
        },
        {
            "step": 2,
            "agent": "memory",
            "action": "store_context",
            "description": "Persist key research findings and insights into the long-term vector memory store.",
        },
        {
            "step": 3,
            "agent": "execution",
            "action": "create_notion_report",
            "description": "Create a detailed, formatted research report page inside the Notion database.",
        },
        {
            "step": 4,
            "agent": "execution",
            "action": "create_linear_tasks",
            "description": "Break the research action items into Linear issues for the engineering team.",
        },
        {
            "step": 5,
            "agent": "execution",
            "action": "create_github_issue",
            "description": "Open a GitHub issue to track the enterprise MCP adoption initiative.",
        },
        {
            "step": 6,
            "agent": "execution",
            "action": "post_slack_summary",
            "description": "Post a concise summary with artifact links to the configured Slack channel.",
        },
    ],
}

_SYSTEM = """You are a senior planning agent for an enterprise AI research assistant.

Given a user request, decompose it into an ordered list of steps for these specialist agents:
  - research  : synthesizes information from its knowledge base
  - memory    : stores/retrieves context from the persistent vector store
  - execution : creates real-world artifacts (Notion pages, Linear issues, GitHub issues, Slack messages)

Return ONLY a JSON object — no markdown fences, no prose — matching this exact schema:
{
  "topic": "<short topic label>",
  "steps": [
    {
      "step": <integer starting at 1>,
      "agent": "<research|memory|execution>",
      "action": "<snake_case action name>",
      "description": "<one sentence describing what this step accomplishes>"
    }
  ]
}"""


class PlannerAgent:
    def __init__(self, trace: TraceLogger):
        self.trace = trace

    def plan(self, prompt: str) -> dict[str, Any]:
        logger.info("Planning workflow for: %s", prompt[:80])

        raw = chat(
            system=_SYSTEM,
            user=f"User request:\n\n{prompt}",
            max_tokens=1024,
            mock_response=json.dumps(_MOCK_PLAN),
        )
        plan = extract_json(raw, _MOCK_PLAN)

        self.trace.log(
            agent_name="PlannerAgent",
            action_type="decompose_request",
            target_app="internal",
            input_data={"prompt": prompt},
            output_data={"topic": plan.get("topic"), "steps": len(plan.get("steps", []))},
            status="success",
        )
        return plan
