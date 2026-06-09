from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.tools.composio_client import ComposioClient


def create_github_issue(
    title: str,
    body: str,
    labels: list[str] | None = None,
    dry_run: bool | None = None,
    client: ComposioClient | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    c = client or ComposioClient(dry_run=dry_run)

    params: dict[str, Any] = {
        "owner": settings.github_repo_owner,
        "repo": settings.github_repo_name,
        "title": title,
        "body": body,
    }
    if labels:
        params["labels"] = labels

    return c.execute("GITHUB_CREATE_AN_ISSUE", params)


def add_github_comment(
    issue_number: int,
    comment: str,
    dry_run: bool | None = None,
    client: ComposioClient | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    c = client or ComposioClient(dry_run=dry_run)

    return c.execute(
        "GITHUB_CREATE_ISSUE_COMMENT",
        {
            "owner": settings.github_repo_owner,
            "repo": settings.github_repo_name,
            "issue_number": issue_number,
            "body": comment,
        },
    )
