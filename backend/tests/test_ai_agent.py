"""Tests for AI agent — mock LLM so tests run without API key."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai_agent import run_ai_search


@pytest.mark.asyncio
async def test_run_ai_search_returns_message_when_provider_unavailable(db):
    provider_mock = MagicMock()
    provider_mock.is_available.return_value = False

    with patch("app.services.ai_agent.get_provider", return_value=provider_mock):
        result = await run_ai_search("мука", db)

    assert "недоступны" in result.lower()


@pytest.mark.asyncio
async def test_run_ai_search_returns_agent_output(db, supplier):
    provider_mock = MagicMock()
    provider_mock.is_available.return_value = True
    provider_mock.get_llm.return_value = MagicMock()

    executor_mock = MagicMock()
    executor_mock.ainvoke = AsyncMock(return_value={"output": "Рекомендую ООО МукоМол"})

    with (
        patch("app.services.ai_agent.get_provider", return_value=provider_mock),
        patch("app.services.ai_agent.make_agent", return_value=executor_mock),
    ):
        result = await run_ai_search("нужна мука", db)

    assert result == "Рекомендую ООО МукоМол"


@pytest.mark.asyncio
async def test_run_ai_search_handles_agent_exception(db):
    provider_mock = MagicMock()
    provider_mock.is_available.return_value = True

    executor_mock = MagicMock()
    executor_mock.ainvoke = AsyncMock(side_effect=Exception("LLM timeout"))

    with (
        patch("app.services.ai_agent.get_provider", return_value=provider_mock),
        patch("app.services.ai_agent.make_agent", return_value=executor_mock),
    ):
        result = await run_ai_search("мука", db)

    assert "ошибка" in result.lower()
