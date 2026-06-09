from __future__ import annotations

import logging
from typing import Any

from app.logs.execution_trace import TraceLogger
from app.memory import run_history
from app.memory.vector_memory import get_memory

logger = logging.getLogger(__name__)


class MemoryAgent:
    def __init__(self, trace: TraceLogger):
        self.trace = trace
        self.memory = get_memory()

    def store(self, content: str, metadata: dict[str, Any] | None = None) -> str:
        doc_id = self.memory.store(content=content, metadata=metadata or {})
        self.trace.log(
            agent_name="MemoryAgent",
            action_type="store_context",
            target_app="vector_store",
            input_data={"content_length": len(content), "metadata": metadata},
            output_data={"doc_id": doc_id, "total_docs": self.memory.count()},
            status="success",
        )
        return doc_id

    def retrieve(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        results = self.memory.retrieve(query=query, n_results=n_results)
        self.trace.log(
            agent_name="MemoryAgent",
            action_type="retrieve_context",
            target_app="vector_store",
            input_data={"query": query, "n_results": n_results},
            output_data={"found": len(results)},
            status="success",
        )
        return results

    def store_research(self, research: dict[str, Any], run_id: str) -> list[str]:
        """Store research summary + each key insight as separate vector docs."""
        ids: list[str] = []
        base_meta = {"run_id": run_id, "topic": research.get("topic", "")}

        summary_id = self.store(
            content=research.get("summary", ""),
            metadata={**base_meta, "type": "research_summary"},
        )
        ids.append(summary_id)

        for i, insight in enumerate(research.get("key_insights", [])):
            iid = self.store(
                content=insight,
                metadata={**base_meta, "type": "key_insight", "index": str(i)},
            )
            ids.append(iid)

        logger.info("Stored %d vector docs for run %s", len(ids), run_id[:8])
        return ids

    def store_knowledge_record(
        self,
        research: dict[str, Any],
        critique: dict[str, Any],
        run_id: str,
    ) -> str:
        """
        Persist structured knowledge to SQLite memory_records table.
        Supports versioning: calling this twice for the same topic increments version.
        """
        topic = research.get("topic", "Unknown")
        summary = research.get("summary", "")
        recommendation = "\n".join(research.get("key_insights", [])[:3])
        sources = research.get("sources", [])
        confidence = critique.get("confidence_score", 0) / 100.0

        record_id = run_history.store_memory_record(
            run_id=run_id,
            topic=topic,
            summary=summary,
            recommendation=recommendation,
            sources=sources,
            confidence=confidence,
        )

        self.trace.log(
            agent_name="MemoryAgent",
            action_type="store_knowledge_record",
            target_app="sqlite",
            input_data={
                "topic": topic,
                "confidence": confidence,
                "sources": len(sources),
            },
            output_data={"record_id": record_id},
            status="success",
        )
        return record_id
