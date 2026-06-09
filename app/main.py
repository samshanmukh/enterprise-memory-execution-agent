from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.memory import run_history
from app.workflows.research_to_execution import run_research_workflow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    run_history.init_db()
    settings = get_settings()
    logger.info(
        "Enterprise Memory Execution Agent  |  LLM=%s/%s  |  DRY_RUN=%s  |  Composio=%s",
        settings.llm_provider, settings.llm_model,
        settings.dry_run,
        "real" if settings.has_composio else "mock",
    )
    yield


app = FastAPI(
    title="Enterprise Memory Execution Agent",
    description=(
        "Multi-agent enterprise research assistant with persistent memory and "
        "autonomous execution across Notion, Linear, GitHub, Slack, and Gmail via Composio."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────

class WorkflowRequest(BaseModel):
    prompt: str = Field(
        min_length=10,
        examples=["Research MCP frameworks for enterprise adoption and create an execution plan."],
    )
    dry_run: bool = Field(default=True)
    run_id: str | None = Field(default=None)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
@app.get("/", tags=["Health"])
async def health() -> dict[str, Any]:
    """Service health, configuration summary, and database stats."""
    settings = get_settings()
    stats = run_history.runs_stats()
    mem_count = run_history.memory_count()
    return {
        "service": "Enterprise Memory Execution Agent",
        "version": "2.0.0",
        "status": "running",
        "config": {
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
            "llm_configured": settings.has_llm,
            "composio_configured": settings.has_composio,
            "dry_run_default": settings.dry_run,
            "max_retries": settings.max_retries,
            "critic_threshold": settings.critic_approval_threshold,
        },
        "stats": {
            "runs": stats,
            "memory_records": mem_count,
        },
        "agents": ["PlannerAgent", "ResearchAgent", "CriticAgent", "MemoryAgent", "ExecutionAgent"],
        "apps": ["notion", "linear", "github", "slack", "gmail"],
        "endpoints": {
            "POST /run-research-workflow": "Execute full multi-agent pipeline",
            "GET /runs": "List workflow runs",
            "GET /runs/{run_id}": "Run details + full trace",
            "GET /memory": "List memory documents",
            "GET /memory/search": "Semantic/keyword memory search",
            "GET /health": "This endpoint",
        },
    }


@app.post("/run-research-workflow", tags=["Workflow"])
async def run_workflow(body: WorkflowRequest) -> Any:
    """
    Execute the full multi-agent research-to-execution pipeline.

    **Agent pipeline:**
    1. PlannerAgent — decomposes prompt into steps
    2. MemoryAgent — retrieves prior context
    3. ResearchAgent — synthesises topic with LLM
    4. CriticAgent — validates quality, scores confidence (0-100), triggers retry if needed
    5. MemoryAgent — stores findings (vector + SQLite)
    6. ExecutionAgent — creates artifacts in **5 apps** via Composio

    Set `dry_run=true` to simulate all Composio actions without real API calls.
    """
    run_id = body.run_id or str(uuid.uuid4())
    try:
        return run_research_workflow(prompt=body.prompt, dry_run=body.dry_run, run_id=run_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/runs", tags=["History"])
async def list_runs(limit: int = Query(default=20, le=100)) -> list[dict[str, Any]]:
    """List all past workflow runs, most recent first."""
    return run_history.list_runs(limit=limit)


@app.get("/runs/{run_id}", tags=["History"])
async def get_run(run_id: str) -> dict[str, Any]:
    """Get full run details including plan, research, critique, and execution trace."""
    run = run_history.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    run["execution_logs"] = run_history.get_execution_logs(run_id)
    run["agent_outputs"] = run_history.get_agent_outputs(run_id)
    return run


@app.get("/memory", tags=["Memory"])
async def list_memory(limit: int = Query(default=20, le=200)) -> dict[str, Any]:
    """List structured knowledge records from SQLite memory store."""
    from app.memory.vector_memory import get_memory
    records = run_history.get_memory_records(limit=limit)
    mem = get_memory()
    return {
        "total_knowledge_records": run_history.memory_count(),
        "total_vector_docs": mem.count(),
        "records": records,
    }


@app.get("/memory/search", tags=["Memory"])
async def search_memory(
    q: str = Query(min_length=2, description="Search query"),
    limit: int = Query(default=10, le=50),
    mode: str = Query(default="hybrid", description="hybrid | vector | keyword"),
) -> dict[str, Any]:
    """
    Search persistent memory.
    - **hybrid**: combines vector similarity + keyword SQL search
    - **vector**: ChromaDB semantic similarity only
    - **keyword**: SQLite LIKE search only
    """
    from app.memory.vector_memory import get_memory
    mem = get_memory()

    vector_results: list[dict] = []
    keyword_results: list[dict] = []

    if mode in ("hybrid", "vector"):
        vector_results = mem.retrieve(query=q, n_results=limit)

    if mode in ("hybrid", "keyword"):
        keyword_results = run_history.search_memory_records(query=q, limit=limit)

    return {
        "query": q,
        "mode": mode,
        "vector_results": vector_results,
        "knowledge_records": keyword_results,
    }


@app.get("/stats", tags=["Health"])
async def stats() -> dict[str, Any]:
    """Aggregate statistics for the dashboard."""
    run_stats = run_history.runs_stats()
    runs = run_history.list_runs(limit=100)
    total_actions = sum(
        len(r.get("trace_entries") or []) for r in runs if isinstance(r.get("trace_entries"), list)
    )
    return {
        "runs": run_stats,
        "memory_records": run_history.memory_count(),
        "total_traced_actions": total_actions,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Any, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": str(exc)})
