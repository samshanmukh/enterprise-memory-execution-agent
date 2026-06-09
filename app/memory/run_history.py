from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.config import get_settings


def _db_path() -> Path:
    path = get_settings().db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = _connect()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id               TEXT PRIMARY KEY,
            prompt           TEXT NOT NULL,
            status           TEXT NOT NULL,
            dry_run          INTEGER NOT NULL DEFAULT 1,
            plan             TEXT,
            research_summary TEXT,
            execution_results TEXT,
            trace_entries    TEXT,
            error_message    TEXT,
            created_at       TEXT NOT NULL,
            completed_at     TEXT
        );

        CREATE TABLE IF NOT EXISTS execution_logs (
            id          TEXT PRIMARY KEY,
            run_id      TEXT NOT NULL,
            agent_name  TEXT NOT NULL,
            action      TEXT NOT NULL,
            tool        TEXT,
            target_app  TEXT,
            input_data  TEXT,
            output_data TEXT,
            status      TEXT NOT NULL,
            duration_ms INTEGER DEFAULT 0,
            timestamp   TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        );

        CREATE TABLE IF NOT EXISTS memory_records (
            id             TEXT PRIMARY KEY,
            topic          TEXT NOT NULL,
            summary        TEXT NOT NULL,
            recommendation TEXT,
            sources        TEXT,
            confidence     REAL DEFAULT 0.0,
            run_id         TEXT,
            version        INTEGER DEFAULT 1,
            created_at     TEXT NOT NULL,
            updated_at     TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS agent_outputs (
            id          TEXT PRIMARY KEY,
            run_id      TEXT NOT NULL,
            agent_name  TEXT NOT NULL,
            output_type TEXT NOT NULL,
            output_data TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        );
    """)
    conn.commit()
    conn.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deserialize_run(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    for field in ("plan", "research_summary", "execution_results", "trace_entries"):
        if d.get(field):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                pass
    d["dry_run"] = bool(d.get("dry_run", 1))
    return d


def _deserialize_row(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    for field in ("input_data", "output_data", "output_data", "sources"):
        if field in d and d[field]:
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


# ── Runs ──────────────────────────────────────────────────────────────────────

def create_run(run_id: str, prompt: str, dry_run: bool) -> dict[str, Any]:
    now = _now()
    conn = _connect()
    conn.execute(
        "INSERT INTO runs (id, prompt, status, dry_run, created_at) VALUES (?, ?, ?, ?, ?)",
        (run_id, prompt, "running", int(dry_run), now),
    )
    conn.commit()
    conn.close()
    return {"id": run_id, "prompt": prompt, "status": "running", "dry_run": dry_run, "created_at": now}


def update_run(run_id: str, **kwargs: Any) -> None:
    if not kwargs:
        return
    serialized = {
        k: json.dumps(v, default=str) if isinstance(v, (dict, list)) else v
        for k, v in kwargs.items()
    }
    fields = ", ".join(f"{k} = ?" for k in serialized)
    conn = _connect()
    conn.execute(f"UPDATE runs SET {fields} WHERE id = ?", [*serialized.values(), run_id])
    conn.commit()
    conn.close()


def get_run(run_id: str) -> Optional[dict[str, Any]]:
    conn = _connect()
    row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    conn.close()
    return _deserialize_run(row) if row else None


def list_runs(limit: int = 50) -> list[dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [_deserialize_run(r) for r in rows]


def runs_stats() -> dict[str, Any]:
    conn = _connect()
    total = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    completed = conn.execute("SELECT COUNT(*) FROM runs WHERE status='completed'").fetchone()[0]
    failed = conn.execute("SELECT COUNT(*) FROM runs WHERE status='failed'").fetchone()[0]
    conn.close()
    success_rate = round(completed / total * 100, 1) if total else 0.0
    return {"total": total, "completed": completed, "failed": failed, "success_rate": success_rate}


# ── Execution Logs ────────────────────────────────────────────────────────────

def log_execution(
    run_id: str,
    agent_name: str,
    action: str,
    target_app: str,
    input_data: Any,
    output_data: Any,
    status: str,
    tool: str | None = None,
    duration_ms: int = 0,
) -> str:
    log_id = str(uuid.uuid4())
    conn = _connect()
    conn.execute(
        """INSERT INTO execution_logs
           (id, run_id, agent_name, action, tool, target_app, input_data, output_data, status, duration_ms, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            log_id, run_id, agent_name, action,
            tool, target_app,
            json.dumps(input_data, default=str),
            json.dumps(output_data, default=str),
            status, duration_ms, _now(),
        ),
    )
    conn.commit()
    conn.close()
    return log_id


def get_execution_logs(run_id: str) -> list[dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM execution_logs WHERE run_id = ? ORDER BY timestamp", (run_id,)
    ).fetchall()
    conn.close()
    return [_deserialize_row(r) for r in rows]


# ── Memory Records ────────────────────────────────────────────────────────────

def store_memory_record(
    run_id: str,
    topic: str,
    summary: str,
    recommendation: str = "",
    sources: list[str] | None = None,
    confidence: float = 0.0,
) -> str:
    record_id = str(uuid.uuid4())
    now = _now()
    conn = _connect()

    # Versioning: find latest version for this topic
    existing = conn.execute(
        "SELECT version FROM memory_records WHERE topic = ? ORDER BY version DESC LIMIT 1",
        (topic,),
    ).fetchone()
    version = (existing["version"] + 1) if existing else 1

    conn.execute(
        """INSERT INTO memory_records
           (id, topic, summary, recommendation, sources, confidence, run_id, version, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            record_id, topic, summary[:4000], recommendation,
            json.dumps(sources or []), confidence, run_id, version, now, now,
        ),
    )
    conn.commit()
    conn.close()
    return record_id


def get_memory_records(limit: int = 50) -> list[dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM memory_records ORDER BY updated_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [_deserialize_row(r) for r in rows]


def search_memory_records(query: str, limit: int = 20) -> list[dict[str, Any]]:
    conn = _connect()
    like = f"%{query}%"
    rows = conn.execute(
        """SELECT * FROM memory_records
           WHERE topic LIKE ? OR summary LIKE ? OR recommendation LIKE ?
           ORDER BY confidence DESC, updated_at DESC LIMIT ?""",
        (like, like, like, limit),
    ).fetchall()
    conn.close()
    return [_deserialize_row(r) for r in rows]


def memory_count() -> int:
    conn = _connect()
    n = conn.execute("SELECT COUNT(*) FROM memory_records").fetchone()[0]
    conn.close()
    return n


# ── Agent Outputs ─────────────────────────────────────────────────────────────

def store_agent_output(
    run_id: str, agent_name: str, output_type: str, output_data: Any
) -> str:
    output_id = str(uuid.uuid4())
    conn = _connect()
    conn.execute(
        """INSERT INTO agent_outputs (id, run_id, agent_name, output_type, output_data, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (output_id, run_id, agent_name, output_type, json.dumps(output_data, default=str), _now()),
    )
    conn.commit()
    conn.close()
    return output_id


def get_agent_outputs(run_id: str) -> list[dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM agent_outputs WHERE run_id = ? ORDER BY created_at", (run_id,)
    ).fetchall()
    conn.close()
    return [_deserialize_row(r) for r in rows]
