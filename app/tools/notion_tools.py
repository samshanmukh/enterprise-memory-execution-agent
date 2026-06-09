from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.tools.composio_client import ComposioClient


def create_notion_page(
    title: str,
    content: str,
    database_id: str | None = None,
    dry_run: bool | None = None,
    client: ComposioClient | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    c = client or ComposioClient(dry_run=dry_run)
    db_id = database_id or settings.notion_database_id

    params: dict[str, Any] = {
        "parent": {"database_id": db_id},
        "properties": {
            "title": {
                "title": [{"text": {"content": title}}]
            }
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content[:2000]}}]
                },
            }
        ],
    }

    return c.execute("NOTION_CREATE_PAGE", params)


def append_notion_blocks(
    page_id: str,
    markdown_content: str,
    dry_run: bool | None = None,
    client: ComposioClient | None = None,
) -> dict[str, Any]:
    c = client or ComposioClient(dry_run=dry_run)

    # Split into paragraphs for Notion block structure
    paragraphs = [p.strip() for p in markdown_content.split("\n\n") if p.strip()]
    blocks = []
    for para in paragraphs[:20]:  # Notion limits
        if para.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": para[3:]}}]},
            })
        elif para.startswith("### "):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": para[4:]}}]},
            })
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": para[:2000]}}]
                },
            })

    return c.execute("NOTION_APPEND_BLOCK_CHILDREN", {"block_id": page_id, "children": blocks})
