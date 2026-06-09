from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

from app.config import get_settings

logger = logging.getLogger(__name__)


class TraceLogger:
    """Records every agent action with timing, status, input, and output."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.entries: list[dict[str, Any]] = []
        settings = get_settings()
        self._log_path = settings.trace_log_path
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        agent_name: str,
        action_type: str,
        target_app: str,
        input_data: Any,
        output_data: Any,
        status: str,
        duration_ms: int = 0,
    ) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "run_id": self.run_id,
            "agent_name": agent_name,
            "action_type": action_type,
            "target_app": target_app,
            "input": input_data,
            "output": output_data,
            "status": status,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.entries.append(entry)
        self._persist(entry)
        logger.info(
            "[%s] %s → %s::%s (%s) %dms",
            self.run_id[:8],
            agent_name,
            target_app,
            action_type,
            status,
            duration_ms,
        )
        return entry

    @contextmanager
    def timed(
        self,
        agent_name: str,
        action_type: str,
        target_app: str,
        input_data: Any,
    ) -> Generator[dict[str, Any], None, None]:
        """Context manager that auto-times and logs an action block."""
        result_holder: dict[str, Any] = {}
        start = time.perf_counter()
        try:
            yield result_holder
            duration_ms = int((time.perf_counter() - start) * 1000)
            self.log(
                agent_name=agent_name,
                action_type=action_type,
                target_app=target_app,
                input_data=input_data,
                output_data=result_holder.get("output"),
                status=result_holder.get("status", "success"),
                duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            self.log(
                agent_name=agent_name,
                action_type=action_type,
                target_app=target_app,
                input_data=input_data,
                output_data={"error": str(exc)},
                status="error",
                duration_ms=duration_ms,
            )
            raise

    def _persist(self, entry: dict[str, Any]) -> None:
        try:
            with open(self._log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, default=str) + "\n")
        except OSError as exc:
            logger.warning("Could not write trace log: %s", exc)

    def get_all(self) -> list[dict[str, Any]]:
        return self.entries

    def summary(self) -> dict[str, Any]:
        statuses = [e["status"] for e in self.entries]
        total_duration = sum(e.get("duration_ms", 0) for e in self.entries)
        return {
            "run_id": self.run_id,
            "total_actions": len(self.entries),
            "success": statuses.count("success"),
            "simulated": statuses.count("simulated"),
            "error": statuses.count("error"),
            "total_duration_ms": total_duration,
        }
