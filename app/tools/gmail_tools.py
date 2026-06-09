from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.tools.composio_client import ComposioClient


def send_gmail_summary(
    subject: str,
    body: str,
    to_email: str | None = None,
    dry_run: bool | None = None,
    client: ComposioClient | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    c = client or ComposioClient(dry_run=dry_run)
    recipient = to_email or settings.gmail_recipient

    return c.execute(
        "GMAIL_SEND_EMAIL",
        {
            "recipient_email": recipient,
            "subject": subject,
            "body": body,
        },
    )


def build_email_body(
    topic: str,
    summary_excerpt: str,
    insights: list[str],
    notion_url: str = "",
    github_url: str = "",
    linear_url: str = "",
) -> str:
    insight_lines = "\n".join(f"  • {i}" for i in insights[:6])
    links = []
    if notion_url:
        links.append(f"  - Notion Report: {notion_url}")
    if github_url:
        links.append(f"  - GitHub Issue: {github_url}")
    if linear_url:
        links.append(f"  - Linear Tasks: {linear_url}")
    link_block = "\n".join(links) if links else "  (see Slack for links)"

    return f"""Enterprise Research Summary
{'=' * 50}

Topic: {topic}

Key Insights:
{insight_lines}

Artifacts Created:
{link_block}

Summary Excerpt:
{summary_excerpt[:800]}...

---
Sent by Enterprise Memory Execution Agent
"""
