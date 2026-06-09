"""Unit tests for CriticAgent."""
from __future__ import annotations

import unittest
import uuid

from app.agents.critic_agent import CriticAgent, APPROVAL_THRESHOLD
from app.logs.execution_trace import TraceLogger

_SAMPLE_RESEARCH = {
    "topic": "MCP Frameworks for Enterprise",
    "summary": "MCP is an open protocol for AI tool integration. It standardises how LLMs connect to tools.",
    "key_insights": [
        "MCP standardises AI-to-tool communication",
        "Security is the top adoption barrier",
        "Python ecosystem is most mature",
    ],
    "sources": ["Anthropic docs", "GitHub"],
}


def _trace() -> TraceLogger:
    return TraceLogger(run_id=str(uuid.uuid4()))


class TestCriticAgent(unittest.TestCase):
    def _make_agent(self) -> CriticAgent:
        return CriticAgent(trace=_trace())

    def test_review_returns_dict(self):
        agent = self._make_agent()
        result = agent.review(_SAMPLE_RESEARCH)
        self.assertIsInstance(result, dict)

    def test_review_has_required_keys(self):
        agent = self._make_agent()
        result = agent.review(_SAMPLE_RESEARCH)
        for key in ("confidence_score", "quality_rating", "strengths", "weaknesses", "improvements", "approved"):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_confidence_score_in_range(self):
        agent = self._make_agent()
        result = agent.review(_SAMPLE_RESEARCH)
        score = result["confidence_score"]
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_approved_consistent_with_score(self):
        agent = self._make_agent()
        result = agent.review(_SAMPLE_RESEARCH)
        expected_approved = result["confidence_score"] >= APPROVAL_THRESHOLD
        self.assertEqual(result["approved"], expected_approved)

    def test_quality_rating_valid(self):
        agent = self._make_agent()
        result = agent.review(_SAMPLE_RESEARCH)
        self.assertIn(result["quality_rating"], ("low", "medium", "high"))

    def test_review_logs_trace(self):
        trace = _trace()
        agent = CriticAgent(trace=trace)
        agent.review(_SAMPLE_RESEARCH)
        entries = trace.get_all()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["agent_name"], "CriticAgent")
        self.assertEqual(entries[0]["action_type"], "validate_research")

    def test_strengths_and_weaknesses_are_lists(self):
        agent = self._make_agent()
        result = agent.review(_SAMPLE_RESEARCH)
        self.assertIsInstance(result["strengths"], list)
        self.assertIsInstance(result["weaknesses"], list)
        self.assertIsInstance(result["improvements"], list)


if __name__ == "__main__":
    unittest.main()
