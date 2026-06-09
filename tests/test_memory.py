"""Unit tests for VectorMemory and run_history."""
from __future__ import annotations

import os
import tempfile
import unittest
import uuid

from app.memory.vector_memory import VectorMemory


class TestVectorMemory(unittest.TestCase):
    def setUp(self):
        self.memory = VectorMemory(collection_name=f"test_{uuid.uuid4().hex[:8]}")

    def test_store_returns_id(self):
        doc_id = self.memory.store("MCP frameworks enable secure AI tool integration.")
        self.assertIsInstance(doc_id, str)
        self.assertTrue(len(doc_id) > 0)

    def test_count_increments(self):
        initial = self.memory.count()
        self.memory.store("First document about enterprise AI.")
        self.memory.store("Second document about MCP security.")
        self.assertEqual(self.memory.count(), initial + 2)

    def test_retrieve_returns_list(self):
        self.memory.store("MCP security best practices for enterprise.")
        self.memory.store("LLM gateway patterns for Fortune 500.")
        results = self.memory.retrieve("MCP enterprise", n_results=5)
        self.assertIsInstance(results, list)

    def test_retrieve_returns_content(self):
        self.memory.store("Vector databases power semantic search at scale.")
        results = self.memory.retrieve("vector database", n_results=1)
        if results:
            self.assertIn("content", results[0])
            self.assertIn("metadata", results[0])

    def test_store_with_metadata(self):
        doc_id = self.memory.store(
            "Composio provides managed MCP connectors.",
            metadata={"source": "test", "run_id": "abc123"},
        )
        self.assertIsNotNone(doc_id)

    def test_list_all_returns_stored(self):
        self.memory.store("Document one about AI agents.")
        self.memory.store("Document two about memory systems.")
        docs = self.memory.list_all()
        self.assertGreaterEqual(len(docs), 2)

    def test_retrieve_empty_store(self):
        fresh = VectorMemory(collection_name=f"empty_{uuid.uuid4().hex[:8]}")
        results = fresh.retrieve("anything", n_results=5)
        self.assertEqual(results, [])


class TestRunHistory(unittest.TestCase):
    def setUp(self):
        # Use in-memory (temp) DB for tests
        import app.memory.run_history as rh
        self._orig_db_path = rh._db_path

        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_file = tmp.name
        tmp.close()

        from app.config import get_settings
        settings = get_settings()
        from pathlib import Path
        settings.db_path = Path(self.db_file)

        rh.init_db()

    def test_create_and_get_run(self):
        import app.memory.run_history as rh
        run_id = str(uuid.uuid4())
        rh.create_run(run_id, "Test prompt", dry_run=True)
        run = rh.get_run(run_id)
        self.assertIsNotNone(run)
        self.assertEqual(run["id"], run_id)
        self.assertEqual(run["status"], "running")
        self.assertTrue(run["dry_run"])

    def test_update_run_status(self):
        import app.memory.run_history as rh
        run_id = str(uuid.uuid4())
        rh.create_run(run_id, "Test prompt", dry_run=False)
        rh.update_run(run_id, status="completed")
        run = rh.get_run(run_id)
        self.assertEqual(run["status"], "completed")

    def test_store_and_search_memory_record(self):
        import app.memory.run_history as rh
        run_id = str(uuid.uuid4())
        rh.create_run(run_id, "Memory test prompt", dry_run=True)
        record_id = rh.store_memory_record(
            run_id=run_id,
            topic="MCP Enterprise Security",
            summary="MCP requires careful access control for enterprise deployments.",
            confidence=0.88,
        )
        self.assertIsNotNone(record_id)
        results = rh.search_memory_records("MCP")
        self.assertGreater(len(results), 0)


if __name__ == "__main__":
    unittest.main()
