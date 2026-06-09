"""Unit tests for PlannerAgent."""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from app.agents.planner_agent import PlannerAgent, _MOCK_PLAN
from app.logs.execution_trace import TraceLogger


def _trace() -> TraceLogger:
    import uuid
    return TraceLogger(run_id=str(uuid.uuid4()))


class TestPlannerAgent(unittest.TestCase):
    def _make_agent(self) -> PlannerAgent:
        return PlannerAgent(trace=_trace())

    def test_plan_returns_dict(self):
        agent = self._make_agent()
        result = agent.plan("Research MCP frameworks for enterprise adoption.")
        self.assertIsInstance(result, dict)

    def test_plan_has_required_keys(self):
        agent = self._make_agent()
        result = agent.plan("Research vector databases for enterprise AI workloads.")
        self.assertIn("topic", result)
        self.assertIn("steps", result)

    def test_plan_steps_is_list(self):
        agent = self._make_agent()
        result = agent.plan("Analyse LLM gateway patterns.")
        self.assertIsInstance(result.get("steps"), list)
        self.assertGreater(len(result["steps"]), 0)

    def test_plan_step_schema(self):
        agent = self._make_agent()
        result = agent.plan("Evaluate RAG architectures.")
        for step in result["steps"]:
            self.assertIn("step", step)
            self.assertIn("agent", step)
            self.assertIn("action", step)
            self.assertIn("description", step)

    def test_plan_logs_trace(self):
        trace = _trace()
        agent = PlannerAgent(trace=trace)
        agent.plan("Research something.")
        self.assertEqual(len(trace.get_all()), 1)
        entry = trace.get_all()[0]
        self.assertEqual(entry["agent_name"], "PlannerAgent")
        self.assertEqual(entry["status"], "success")

    def test_plan_with_mock_response(self):
        """When no LLM key is set, should fall back to mock plan."""
        with patch("app.tools.llm_client.get_settings") as mock_settings:
            mock_settings.return_value.has_llm = False
            mock_settings.return_value.llm_provider = "anthropic"
            mock_settings.return_value.anthropic_api_key = None
            mock_settings.return_value.openai_api_key = None
            agent = self._make_agent()
            result = agent.plan("Test prompt that is long enough.")
        self.assertIn("topic", result)


if __name__ == "__main__":
    unittest.main()
