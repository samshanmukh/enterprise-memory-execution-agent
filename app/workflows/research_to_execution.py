"""
Main orchestration pipeline:

  Planner → Memory (retrieve) → Research → Critic
      ↓ (retry if low confidence)
  Memory (store) → Execution (5 apps) → Memory (knowledge record) → Trace

Returns a structured result stored in SQLite and returned by the API.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.agents.critic_agent import CriticAgent
from app.agents.execution_agent import ExecutionAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.planner_agent import PlannerAgent
from app.agents.research_agent import ResearchAgent
from app.config import get_settings
from app.logs.execution_trace import TraceLogger
from app.memory import run_history

logger = logging.getLogger(__name__)


def run_research_workflow(
    prompt: str,
    dry_run: bool = True,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Execute the full research-to-execution pipeline and return a structured result."""
    run_id = run_id or str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    settings = get_settings()
    trace = TraceLogger(run_id=run_id)

    logger.info("Workflow start  run_id=%s  dry_run=%s", run_id[:8], dry_run)
    run_history.create_run(run_id=run_id, prompt=prompt, dry_run=dry_run)

    try:
        # ── 1. Plan ───────────────────────────────────────────────────────────
        plan = PlannerAgent(trace=trace).plan(prompt)
        topic = plan.get("topic", prompt)
        run_history.store_agent_output(run_id, "PlannerAgent", "plan", plan)

        # ── 2. Retrieve prior memory context ──────────────────────────────────
        memory_agent = MemoryAgent(trace=trace)
        prior_context = memory_agent.retrieve(query=topic, n_results=3)

        # ── 3. Research ───────────────────────────────────────────────────────
        researcher = ResearchAgent(trace=trace)
        research = researcher.research(topic=topic, context=prior_context)

        # ── 4. Critic validates (with retry on low confidence) ─────────────────
        critic = CriticAgent(trace=trace)
        critique = critic.review(research)

        if not critique.get("approved") and settings.has_llm:
            logger.info(
                "Confidence %d < threshold — triggering research retry with critic feedback",
                critique.get("confidence_score", 0),
            )
            improvements = critique.get("improvements", [])
            research = researcher.research(topic=topic, context=prior_context, feedback=improvements)
            critique = critic.review(research)

        run_history.store_agent_output(run_id, "ResearchAgent", "research", research)
        run_history.store_agent_output(run_id, "CriticAgent", "critique", critique)

        # ── 5. Store findings in vector memory ────────────────────────────────
        memory_ids = memory_agent.store_research(research=research, run_id=run_id)

        # ── 6. Store structured knowledge record (SQLite, versioned) ──────────
        knowledge_record_id = memory_agent.store_knowledge_record(
            research=research, critique=critique, run_id=run_id
        )

        # ── 7. Execute across 5 apps ──────────────────────────────────────────
        executor = ExecutionAgent(trace=trace, dry_run=dry_run)
        execution_results = executor.run_all(research=research)

        # ── 8. Persist execution logs to DB ───────────────────────────────────
        for entry in trace.get_all():
            if entry.get("target_app") not in ("internal", "vector_store", "sqlite"):
                run_history.log_execution(
                    run_id=run_id,
                    agent_name=entry["agent_name"],
                    action=entry["action_type"],
                    target_app=entry["target_app"],
                    input_data=entry["input"],
                    output_data=entry["output"],
                    status=entry["status"],
                    duration_ms=entry.get("duration_ms", 0),
                )

        # ── Finalise ──────────────────────────────────────────────────────────
        completed_at = datetime.now(timezone.utc).isoformat()
        trace_summary = trace.summary()

        result: dict[str, Any] = {
            "run_id": run_id,
            "status": "completed",
            "dry_run": dry_run,
            "started_at": started_at,
            "completed_at": completed_at,
            "plan": plan,
            "research": {
                "topic": research.get("topic"),
                "key_insights": research.get("key_insights"),
                "summary_excerpt": (research.get("summary", "")[:600] + "…"),
                "sources": research.get("sources"),
            },
            "critique": {
                "confidence_score": critique.get("confidence_score"),
                "quality_rating": critique.get("quality_rating"),
                "approved": critique.get("approved"),
                "strengths": critique.get("strengths"),
                "weaknesses": critique.get("weaknesses"),
                "improvements": critique.get("improvements"),
            },
            "memory": {
                "docs_stored": len(memory_ids),
                "prior_context_retrieved": len(prior_context),
                "doc_ids": memory_ids,
                "knowledge_record_id": knowledge_record_id,
            },
            "execution_results": {
                "notion": _safe_result(execution_results.get("notion")),
                "linear": [_safe_result(r) for r in (execution_results.get("linear") or [])],
                "github": _safe_result(execution_results.get("github")),
                "slack": _safe_result(execution_results.get("slack")),
                "gmail": _safe_result(execution_results.get("gmail")),
            },
            "trace": trace.get_all(),
            "trace_summary": trace_summary,
        }

        run_history.update_run(
            run_id,
            status="completed",
            plan=json.dumps(plan, default=str),
            research_summary=json.dumps(research, default=str),
            execution_results=json.dumps(result["execution_results"], default=str),
            trace_entries=json.dumps(trace.get_all(), default=str),
            completed_at=completed_at,
        )

        logger.info(
            "Workflow complete  run_id=%s  actions=%d  duration=%dms",
            run_id[:8],
            trace_summary["total_actions"],
            trace_summary["total_duration_ms"],
        )
        return result

    except Exception as exc:
        logger.exception("Workflow failed  run_id=%s: %s", run_id[:8], exc)
        run_history.update_run(
            run_id,
            status="failed",
            error_message=str(exc),
            trace_entries=json.dumps(trace.get_all(), default=str),
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        trace.log(
            agent_name="Orchestrator",
            action_type="error",
            target_app="internal",
            input_data={"prompt": prompt},
            output_data={"error": str(exc)},
            status="error",
        )
        raise


def _safe_result(result: dict[str, Any] | None) -> dict[str, Any]:
    if not result:
        return {}
    return {
        "success": result.get("success", False),
        "simulated": result.get("simulated", False),
        "data": result.get("data"),
        "attempts": result.get("attempts", 1),
    }
