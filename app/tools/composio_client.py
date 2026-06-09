"""
Composio tool-execution wrapper.

When COMPOSIO_API_KEY is set, delegates to the real Composio SDK.
When dry_run=True or the key is absent, returns realistic simulated responses.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


class ComposioClient:
    def __init__(self, dry_run: Optional[bool] = None):
        settings = get_settings()
        self.dry_run = dry_run if dry_run is not None else settings.dry_run
        self._api_key = settings.composio_api_key
        self._toolset = None

        if not self.dry_run and self._api_key:
            self._init_real_client()

    def _init_real_client(self) -> None:
        try:
            from composio import ComposioToolSet  # type: ignore

            self._toolset = ComposioToolSet(api_key=self._api_key)
            logger.info("Composio real client initialized.")
        except ImportError:
            logger.warning("composio-core not installed — falling back to dry-run mode.")
            self.dry_run = True
        except Exception as exc:
            logger.warning("Composio init failed (%s) — falling back to dry-run mode.", exc)
            self.dry_run = True

    def execute(
        self,
        action: str,
        params: dict[str, Any],
        entity_id: str = "default",
    ) -> dict[str, Any]:
        """Execute a Composio action, or simulate it in dry-run mode."""
        if self.dry_run or self._toolset is None:
            return self._simulate(action, params)
        return self._execute_real(action, params, entity_id)

    def _execute_real(
        self, action: str, params: dict[str, Any], entity_id: str
    ) -> dict[str, Any]:
        try:
            from composio import Action as ComposioAction  # type: ignore

            result = self._toolset.execute_action(
                action=getattr(ComposioAction, action),
                params=params,
                entity_id=entity_id,
            )
            return {"success": True, "data": result, "action": action}
        except Exception as exc:
            logger.error("Composio action %s failed: %s", action, exc)
            return {"success": False, "error": str(exc), "action": action}

    def _simulate(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        """Return a realistic mock response for a dry-run."""
        ts = datetime.now(timezone.utc).isoformat()
        fake_id = str(uuid.uuid4())[:8]

        simulated: dict[str, Any] = {
            "success": True,
            "simulated": True,
            "action": action,
            "timestamp": ts,
        }

        if "GITHUB" in action:
            simulated["data"] = {
                "issue_number": int(fake_id[:3], 16) % 500 + 1,
                "html_url": f"https://github.com/{params.get('owner', 'org')}/{params.get('repo', 'repo')}/issues/{int(fake_id[:3], 16) % 500 + 1}",
                "title": params.get("title", "Research Initiative"),
                "state": "open",
            }
        elif "SLACK" in action:
            simulated["data"] = {
                "ok": True,
                "ts": ts,
                "channel": params.get("channel", "C0000000000"),
                "message": params.get("text", "")[:80],
            }
        elif "NOTION" in action:
            simulated["data"] = {
                "id": fake_id,
                "url": f"https://notion.so/{fake_id}",
                "title": params.get("title", "Research Report"),
                "created_time": ts,
            }
        elif "LINEAR" in action:
            simulated["data"] = {
                "id": fake_id,
                "identifier": f"ENG-{int(fake_id, 16) % 999 + 1}",
                "title": params.get("title", "Task"),
                "url": f"https://linear.app/team/issue/ENG-{int(fake_id, 16) % 999 + 1}",
            }
        elif "GMAIL" in action:
            simulated["data"] = {
                "message_id": fake_id,
                "thread_id": f"thread-{fake_id}",
                "recipient": params.get("recipient_email", "team@example.com"),
                "subject": params.get("subject", "")[:60],
                "status": "sent",
            }
        else:
            simulated["data"] = {"result": "ok", "params": params}

        logger.info("[DRY RUN] Simulated %s → %s", action, simulated["data"])
        return simulated
