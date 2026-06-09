"""Pydantic models for all agent inputs, outputs, and domain entities."""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Planner ───────────────────────────────────────────────────────────────────

class PlanStep(BaseModel):
    step: int
    agent: str
    action: str
    description: str


class PlanOutput(BaseModel):
    topic: str
    steps: list[PlanStep]


# ── Research ──────────────────────────────────────────────────────────────────

class LinearTask(BaseModel):
    title: str
    description: str


class ResearchOutput(BaseModel):
    topic: str
    summary: str
    key_insights: list[str]
    linear_tasks: list[LinearTask] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


# ── Critic ────────────────────────────────────────────────────────────────────

class CriticOutput(BaseModel):
    confidence_score: int = Field(ge=0, le=100)
    quality_rating: str  # low | medium | high
    strengths: list[str]
    weaknesses: list[str]
    improvements: list[str]
    recommendation_validity: str  # valid | questionable | invalid
    approved: bool


# ── Memory ────────────────────────────────────────────────────────────────────

class KnowledgeRecord(BaseModel):
    id: str
    topic: str
    summary: str
    recommendation: Optional[str] = None
    sources: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    run_id: str
    version: int = 1
    created_at: str
    updated_at: str


# ── Execution ─────────────────────────────────────────────────────────────────

class AppResult(BaseModel):
    success: bool
    simulated: bool = False
    action: str
    data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    attempts: int = 1
    duration_ms: int = 0


class ExecutionResults(BaseModel):
    notion: Optional[AppResult] = None
    linear: list[AppResult] = Field(default_factory=list)
    github: Optional[AppResult] = None
    slack: Optional[AppResult] = None
    gmail: Optional[AppResult] = None


# ── Trace ─────────────────────────────────────────────────────────────────────

class TraceEntry(BaseModel):
    run_id: str
    agent_name: str
    action_type: str
    target_app: str
    input: Any
    output: Any
    status: str  # success | simulated | error
    duration_ms: int = 0
    timestamp: str


# ── API ───────────────────────────────────────────────────────────────────────

class WorkflowRequest(BaseModel):
    prompt: str = Field(
        min_length=10,
        examples=["Research MCP frameworks for enterprise adoption and create an execution plan."],
    )
    dry_run: bool = True
    run_id: Optional[str] = None


class TraceSummary(BaseModel):
    run_id: str
    total_actions: int
    success: int
    simulated: int
    error: int
    total_duration_ms: int = 0
