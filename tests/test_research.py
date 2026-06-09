"""Unit tests for ResearchAgent."""
from __future__ import annotations

import unittest
import uuid

from app.agents.research_agent import ResearchAgent
from app.logs.execution_trace import TraceLogger


def _trace() -> TraceLogger:
    return TraceLogger(run_id=str(uuid.uuid4()))


class TestResearchAgent(unittest.TestCase):
    def _make_agent(self) -> ResearchAgent:
        return ResearchAgent(trace=_trace())

    def test_research_returns_dict(self):
        agent = self._make_agent()
        result = agent.research("MCP frameworks for enterprise adoption")
        self.assertIsInstance(result, dict)

    def test_research_has_required_keys(self):
        agent = self._make_agent()
        result = agent.research("Vector databases for enterprise AI")
        for key in ("topic", "summary", "key_insights", "sources"):
            self.assertIn(key, result)

    def test_key_insights_is_list(self):
        agent = self._make_agent()
        result = agent.research("LLM gateway patterns")
        self.assertIsInstance(result.get("key_insights"), list)
        self.assertGreater(len(result["key_insights"]), 0)

    def test_linear_tasks_present(self):
        agent = self._make_agent()
        result = agent.research("Evaluate RAG architectures")
        tasks = result.get("linear_tasks", [])
        self.assertIsInstance(tasks, list)

    def test_research_with_context(self):
        agent = self._make_agent()
        context = [{"content": "MCP was created by Anthropic in 2024.", "metadata": {}}]
        result = agent.research("MCP enterprise adoption", context=context)
        self.assertIn("topic", result)

    def test_research_with_feedback(self):
        agent = self._make_agent()
        feedback = ["Add compliance section", "Include TCO analysis"]
        result = agent.research("MCP enterprise adoption", feedback=feedback)
        self.assertIn("summary", result)

    def test_research_logs_trace(self):
        trace = _trace()
        agent = ResearchAgent(trace=trace)
        agent.research("Test topic for logging")
        entries = trace.get_all()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["agent_name"], "ResearchAgent")
        self.assertEqual(entries[0]["action_type"], "synthesize_topic")

    def test_summary_is_non_empty_string(self):
        agent = self._make_agent()
        result = agent.research("AI observability")
        self.assertIsInstance(result.get("summary"), str)
        self.assertGreater(len(result["summary"]), 100)


if __name__ == "__main__":
    unittest.main()
