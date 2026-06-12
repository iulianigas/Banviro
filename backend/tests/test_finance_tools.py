from app.mcp.tools.finance import finance_tools_for_message


def test_finance_tools_for_message_includes_summary_for_spending() -> None:
    tools = finance_tools_for_message("Cât am cheltuit luna asta?")
    assert "get_summary" in tools
    assert "list_transactions" in tools
    assert "get_spending_by_category" in tools
    assert "get_budgets" not in tools


def test_finance_tools_for_message_includes_category_spending() -> None:
    tools = finance_tools_for_message("Cât am cheltuit pe transport?")
    assert "get_spending_by_category" in tools
    assert "list_transactions" in tools


def test_finance_tools_for_message_includes_budgets() -> None:
    tools = finance_tools_for_message("Cum stau bugetele mele?")
    assert "get_budgets" in tools


def test_finance_tools_for_message_empty_for_unrelated() -> None:
    tools = finance_tools_for_message("Salut!")
    assert tools == []
