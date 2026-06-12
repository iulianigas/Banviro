from unittest.mock import AsyncMock, patch

import pytest

from app.ai.graph.agent import fetch_finance, fetch_rag, generate_reply, route_intent
from app.ai.graph.router import route_message


@pytest.mark.asyncio
async def test_route_intent_sets_planned_tools() -> None:
    state = {
        "message": "Cat am cheltuit?",
        "locale": "ro",
        "user_id": 1,
        "user_email": "test@example.com",
        "planned_tools": [],
        "plan_rag": False,
        "summary_text": "",
        "recent_transactions": "",
        "budget_text": "",
        "rag_snippets": [],
        "tools_used": [],
        "used_rag": False,
        "reply": "",
        "model": "",
        "error": None,
    }

    with patch(
        "app.ai.graph.agent.route_message",
        new=AsyncMock(return_value=(["get_summary"], False)),
    ):
        result = await route_intent(state, {"configurable": {}})

    assert result["planned_tools"] == ["get_summary"]
    assert result["plan_rag"] is False


@pytest.mark.asyncio
async def test_fetch_finance_skips_when_no_planned_tools() -> None:
    state = {
        "message": "Salut!",
        "locale": "ro",
        "user_id": 1,
        "user_email": "test@example.com",
        "planned_tools": [],
        "plan_rag": False,
        "summary_text": "",
        "recent_transactions": "",
        "budget_text": "",
        "rag_snippets": [],
        "tools_used": [],
        "used_rag": False,
        "reply": "",
        "model": "",
        "error": None,
    }

    result = await fetch_finance(state, {"configurable": {"db": object()}})

    assert result == {}


@pytest.mark.asyncio
async def test_fetch_rag_marks_used_rag() -> None:
    state = {
        "message": "Explică-mi tendința cheltuielilor",
        "locale": "ro",
        "user_id": 1,
        "user_email": "test@example.com",
        "planned_tools": [],
        "plan_rag": True,
        "summary_text": "",
        "recent_transactions": "",
        "budget_text": "",
        "rag_snippets": [],
        "tools_used": [],
        "used_rag": False,
        "reply": "",
        "model": "",
        "error": None,
    }

    with patch(
        "app.ai.graph.agent.qdrant_retriever.search",
        new=AsyncMock(return_value=["tx: food 120 RON"]),
    ):
        result = await fetch_rag(state, {"configurable": {}})

    assert result["used_rag"] is True
    assert result["rag_snippets"] == ["tx: food 120 RON"]
    assert "qdrant_rag" in result["tools_used"]


@pytest.mark.asyncio
async def test_generate_reply_uses_ollama() -> None:
    state = {
        "message": "Salut",
        "locale": "en",
        "user_id": 1,
        "user_email": "test@example.com",
        "planned_tools": [],
        "plan_rag": False,
        "summary_text": "Total balance: 100 RON.",
        "recent_transactions": "",
        "budget_text": "",
        "rag_snippets": [],
        "tools_used": [],
        "used_rag": False,
        "reply": "",
        "model": "",
        "error": None,
    }

    with (
        patch(
            "app.ai.graph.agent.ollama_client.is_available",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.ai.graph.agent.ollama_client.generate",
            new=AsyncMock(return_value="Your balance is 100 RON."),
        ),
    ):
        result = await generate_reply(state, {"configurable": {}})

    assert result["reply"] == "Your balance is 100 RON."
    assert result["model"]


@pytest.mark.asyncio
async def test_route_message_parses_llm_json() -> None:
    with (
        patch(
            "app.ai.graph.router.ollama_client.is_available",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.ai.graph.router.ollama_client.generate",
            new=AsyncMock(return_value='{"tools": ["get_budgets"], "use_rag": true}'),
        ),
    ):
        tools, use_rag = await route_message("How are my budgets?", "en")

    assert tools == ["get_budgets"]
    assert use_rag is True


@pytest.mark.asyncio
async def test_route_message_falls_back_to_keywords() -> None:
    with patch(
        "app.ai.graph.router.ollama_client.is_available",
        new=AsyncMock(return_value=False),
    ):
        tools, use_rag = await route_message("Cât am cheltuit luna asta?", "ro")

    assert "get_summary" in tools
    assert use_rag is False
