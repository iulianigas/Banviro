import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport
from fastmcp.exceptions import AuthorizationError

from app.main import app
from app.mcp.auth import resolve_access_token, resolve_mcp_user
from app.mcp.server import mcp
from app.database import SessionLocal

client = TestClient(app)


def _register_and_login(email: str | None = None, password: str = "Test1234") -> str:
    email = email or f"mcp-{uuid.uuid4().hex[:8]}@test.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "MCP Tester"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return response.json()["access_token"]


def test_resolve_access_token_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BANVIRO_ACCESS_TOKEN", "test-token-value")
    assert resolve_access_token() == "test-token-value"


def test_resolve_mcp_user_rejects_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BANVIRO_ACCESS_TOKEN", raising=False)
    db = SessionLocal()
    try:
        with pytest.raises(AuthorizationError):
            resolve_mcp_user(db)
    finally:
        db.close()


@pytest.mark.asyncio
async def test_mcp_lists_finance_tools() -> None:
    async with Client(transport=FastMCPTransport(mcp)) as mcp_client:
        tools = await mcp_client.list_tools()

    assert {tool.name for tool in tools} == {
        "get_summary",
        "list_transactions",
        "get_budgets",
        "get_spending_by_category",
    }


@pytest.mark.asyncio
async def test_mcp_get_summary_returns_user_data(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _register_and_login()
    monkeypatch.setenv("BANVIRO_ACCESS_TOKEN", token)

    categories = client.get(
        "/api/v1/finance/categories?type=expense",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    category_id = categories[0]["id"]

    client.post(
        "/api/v1/finance/transactions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "category_id": category_id,
            "amount": "42.00",
            "type": "expense",
            "transaction_date": date.today().isoformat(),
            "description": "MCP test",
        },
    )

    async with Client(transport=FastMCPTransport(mcp)) as mcp_client:
        result = await mcp_client.call_tool("get_summary", {"locale": "ro"})

    text = result.content[0].text
    assert "42.00" in text or "Cheltuieli" in text
