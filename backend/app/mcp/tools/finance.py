def get_finance_tool_definitions() -> list[dict[str, str]]:
    return [
        {
            "name": "get_summary",
            "description": "Returnează sold, venituri, cheltuieli și economii pentru luna curentă.",
        },
        {
            "name": "list_transactions",
            "description": "Listează tranzacțiile recente ale utilizatorului.",
        },
        {
            "name": "get_budgets",
            "description": "Returnează progresul bugetelor lunare pe categorii.",
        },
    ]
