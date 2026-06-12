from unittest.mock import AsyncMock, patch

import pytest

from app.ai.graph.agent import fetch_finance, fetch_rag, generate_reply


@pytest.mark.asyncio
async def test_fetch_finance_skips_unrelated_message() -> None:
    state = {
        "message": "Salut!",
        "locale": "ro",
        "user_id": 1,
        "user_email": "test@example.com",
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
