"""Unit tests for ComposioClient dry-run simulation."""
from __future__ import annotations

import unittest

from app.tools.composio_client import ComposioClient


class TestComposioClientDryRun(unittest.TestCase):
    def setUp(self):
        self.client = ComposioClient(dry_run=True)

    def test_always_returns_success_in_dry_run(self):
        result = self.client.execute("SOME_ACTION", {"key": "value"})
        self.assertTrue(result.get("success"))

    def test_dry_run_flag(self):
        result = self.client.execute("TEST_ACTION", {})
        self.assertTrue(result.get("simulated"))

    def test_github_simulation(self):
        result = self.client.execute(
            "GITHUB_CREATE_AN_ISSUE",
            {"owner": "test-org", "repo": "test-repo", "title": "Test Issue", "body": "Body"},
        )
        data = result.get("data", {})
        self.assertIn("issue_number", data)
        self.assertIn("html_url", data)
        self.assertIn("github.com", data["html_url"])

    def test_slack_simulation(self):
        result = self.client.execute(
            "SLACK_SENDS_A_MESSAGE_TO_A_SLACK_CHANNEL",
            {"channel": "C123", "text": "Hello world"},
        )
        data = result.get("data", {})
        self.assertIn("ok", data)
        self.assertTrue(data["ok"])

    def test_notion_simulation(self):
        result = self.client.execute(
            "NOTION_CREATE_PAGE",
            {"parent": {"database_id": "abc"}, "properties": {}, "children": []},
        )
        data = result.get("data", {})
        self.assertIn("url", data)
        self.assertIn("notion.so", data["url"])

    def test_linear_simulation(self):
        result = self.client.execute(
            "LINEAR_CREATE_LINEAR_ISSUE",
            {"teamId": "TEAM-1", "title": "Setup MCP registry", "description": "Track this."},
        )
        data = result.get("data", {})
        self.assertIn("identifier", data)
        self.assertTrue(data["identifier"].startswith("ENG-"))

    def test_gmail_simulation(self):
        result = self.client.execute(
            "GMAIL_SEND_EMAIL",
            {"recipient_email": "team@example.com", "subject": "Research ready", "body": "See Notion."},
        )
        data = result.get("data", {})
        self.assertIn("message_id", data)
        self.assertEqual(data.get("status"), "sent")

    def test_action_field_in_result(self):
        action = "GITHUB_CREATE_AN_ISSUE"
        result = self.client.execute(action, {})
        self.assertEqual(result.get("action"), action)

    def test_timestamp_in_result(self):
        result = self.client.execute("TEST_ACTION", {})
        self.assertIn("timestamp", result)


class TestComposioClientNoKey(unittest.TestCase):
    def test_falls_back_to_dry_run_without_key(self):
        client = ComposioClient(dry_run=False)
        # Without a real key composio_client init should flip to dry_run
        result = client.execute("GITHUB_CREATE_AN_ISSUE", {"title": "test"})
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success") or result.get("simulated"))


if __name__ == "__main__":
    unittest.main()
