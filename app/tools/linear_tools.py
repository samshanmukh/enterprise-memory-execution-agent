from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.tools.composio_client import ComposioClient


def create_linear_issue(
    title: str,
    description: str,
    priority: int = 2,
    team_id: str | None = None,
    dry_run: bool | None = None,
    client: ComposioClient | None = None,
) -> dict[str, Any]:
    """
    priority: 0=No priority, 1=Urgent, 2=High, 3=Medium, 4=Low
    """
    settings = get_settings()
    c = client or ComposioClient(dry_run=dry_run)
    tid = team_id or settings.linear_team_id

    return c.execute(
        "LINEAR_CREATE_LINEAR_ISSUE",
        {
            "teamId": tid,
            "title": title,
            "description": description,
            "priority": priority,
        },
    )


def create_linear_issues_bulk(
    tasks: list[dict[str, str]],
    team_id: str | None = None,
    dry_run: bool | None = None,
    client: ComposioClient | None = None,
) -> list[dict[str, Any]]:
    """Create multiple Linear issues from a list of {title, description} dicts."""
    settings = get_settings()
    c = client or ComposioClient(dry_run=dry_run)
    tid = team_id or settings.linear_team_id
    results = []
    for task in tasks:
        result = create_linear_issue(
            title=task.get("title", "Untitled"),
            description=task.get("description", ""),
            team_id=tid,
            client=c,
        )
        results.append(result)
    return results
