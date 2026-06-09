from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    # Composio
    composio_api_key: str | None = os.getenv("COMPOSIO_API_KEY")

    # GitHub
    github_repo_owner: str = os.getenv("GITHUB_REPO_OWNER", "example-org")
    github_repo_name: str = os.getenv("GITHUB_REPO_NAME", "enterprise-research")

    # Slack
    slack_channel_id: str = os.getenv("SLACK_CHANNEL_ID", "C0000000000")
    slack_bot_token: str | None = os.getenv("SLACK_BOT_TOKEN")

    # Notion
    notion_database_id: str = os.getenv("NOTION_DATABASE_ID", "00000000-0000-0000-0000-000000000000")
    notion_token: str | None = os.getenv("NOTION_TOKEN")

    # Linear
    linear_team_id: str = os.getenv("LINEAR_TEAM_ID", "TEAM-001")
    linear_api_key: str | None = os.getenv("LINEAR_API_KEY")

    # Gmail
    gmail_recipient: str = os.getenv("GMAIL_RECIPIENT", "team@example.com")

    # App
    dry_run: bool = os.getenv("DRY_RUN", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    critic_approval_threshold: int = int(os.getenv("CRITIC_APPROVAL_THRESHOLD", "70"))

    # Paths
    db_path: Path = Path("data/run_history.db")
    trace_log_path: Path = Path("logs/execution_traces.jsonl")
    chroma_persist_path: Path = Path("data/chroma")

    @property
    def has_llm(self) -> bool:
        return bool(self.anthropic_api_key or self.openai_api_key)

    @property
    def has_composio(self) -> bool:
        return bool(self.composio_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
