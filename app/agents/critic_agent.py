"""
Critic Agent: validates research quality, assigns confidence score, flags improvements.

Runs after ResearchAgent. If confidence < APPROVAL_THRESHOLD, the orchestrator
can trigger a research retry with the critic's improvement suggestions.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.logs.execution_trace import TraceLogger
from app.tools.llm_client import chat, extract_json

logger = logging.getLogger(__name__)

APPROVAL_THRESHOLD = 70  # confidence score below this triggers a research retry

_MOCK_CRITIQUE: dict[str, Any] = {
    "confidence_score": 88,
    "quality_rating": "high",
    "strengths": [
        "Comprehensive MCP ecosystem coverage with actionable framework comparisons",
        "Enterprise framing aligned with decision-maker needs and risk tolerance",
        "Concrete recommendations mapped to identifiable implementation steps",
        "Diverse sourcing across vendor docs, OSS repos, and industry analyst reports",
    ],
    "weaknesses": [
        "Limited depth on MCP security audit tooling for regulated industries",
        "No total cost of ownership comparison between self-hosted and managed layers",
        "Migration path between MCP spec versions not addressed",
    ],
    "improvements": [
        "Add compliance alignment section covering SOC2, ISO 27001, and HIPAA requirements",
        "Include a TCO model comparing Composio enterprise tier vs self-hosted MCP gateway",
        "Reference the MCP spec versioning roadmap to address backward compatibility concerns",
    ],
    "recommendation_validity": "valid",
    "approved": True,
}

_SYSTEM = """You are a senior enterprise research quality analyst and expert technology critic.

Evaluate the provided research report against these quality dimensions:
1. Completeness — does it cover the topic breadth sufficiently?
2. Accuracy — are claims defensible and sourced?
3. Enterprise relevance — does it address real business constraints?
4. Actionability — do recommendations translate into executable steps?
5. Balance — does it represent both upside potential and adoption risks?

Return ONLY a JSON object — no prose, no markdown fences:
{
  "confidence_score": <integer 0-100>,
  "quality_rating": "<low|medium|high>",
  "strengths": ["<strength>", ...],
  "weaknesses": ["<weakness>", ...],
  "improvements": ["<concrete improvement suggestion>", ...],
  "recommendation_validity": "<valid|questionable|invalid>",
  "approved": <true if confidence_score >= 70, else false>
}"""


class CriticAgent:
    def __init__(self, trace: TraceLogger):
        self.trace = trace

    def review(self, research: dict[str, Any]) -> dict[str, Any]:
        topic = research.get("topic", "Unknown")
        summary_excerpt = research.get("summary", "")[:1500]
        insights = research.get("key_insights", [])

        logger.info("CriticAgent reviewing research: %s", topic)

        user = f"""Research Topic: {topic}

Summary Excerpt:
{summary_excerpt}

Key Insights ({len(insights)} total):
{json.dumps(insights, indent=2)}

Sources:
{json.dumps(research.get("sources", []), indent=2)}

Critically evaluate this research report for enterprise decision-making quality."""

        raw = chat(
            system=_SYSTEM,
            user=user,
            max_tokens=1024,
            mock_response=json.dumps(_MOCK_CRITIQUE),
        )
        critique = extract_json(raw, _MOCK_CRITIQUE)

        # Ensure approved field is consistent with score
        score = critique.get("confidence_score", 0)
        critique["approved"] = score >= APPROVAL_THRESHOLD

        self.trace.log(
            agent_name="CriticAgent",
            action_type="validate_research",
            target_app="internal",
            input_data={
                "topic": topic,
                "insights_count": len(insights),
                "summary_length": len(research.get("summary", "")),
            },
            output_data={
                "confidence_score": score,
                "quality_rating": critique.get("quality_rating"),
                "approved": critique.get("approved"),
                "weaknesses": len(critique.get("weaknesses", [])),
            },
            status="success",
        )
        return critique
