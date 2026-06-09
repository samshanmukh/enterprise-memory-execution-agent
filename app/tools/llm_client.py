from __future__ import annotations

import logging
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


def chat(
    system: str,
    user: str,
    max_tokens: int = 2048,
    mock_response: Optional[str] = None,
) -> str:
    """Call the configured LLM. Falls back to mock_response when no API keys are set."""
    settings = get_settings()

    if not settings.has_llm:
        logger.warning("No LLM API key found — returning mock response.")
        return mock_response or "[MOCK] No LLM provider configured."

    try:
        if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
            return _call_anthropic(system, user, settings.llm_model, max_tokens)

        if settings.openai_api_key:
            return _call_openai(system, user, settings.llm_model, max_tokens)
    except _MockFallback:
        logger.warning("LLM unavailable — returning mock response.")
        return mock_response or "[MOCK] LLM unavailable."

    return mock_response or "[MOCK] No LLM provider configured."


def _call_anthropic(system: str, user: str, model: str, max_tokens: int) -> str:
    import anthropic  # type: ignore

    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text
    except anthropic.AuthenticationError:
        logger.warning("Anthropic key invalid — falling back to mock response.")
        raise _MockFallback()
    except Exception as exc:
        logger.warning("Anthropic call failed (%s) — falling back to mock response.", exc)
        raise _MockFallback()


def _call_openai(system: str, user: str, model: str, max_tokens: int) -> str:
    from openai import OpenAI  # type: ignore

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    try:
        resp = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""
    except Exception as exc:
        logger.warning("OpenAI call failed (%s) — falling back to mock response.", exc)
        raise _MockFallback()


class _MockFallback(Exception):
    """Sentinel to trigger mock fallback in chat()."""


def extract_json(text: str, fallback: dict) -> dict:
    """Pull the first JSON object out of an LLM response."""
    import json

    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return fallback
