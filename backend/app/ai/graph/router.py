import json
import re

from app.ai.llm.ollama import ollama_client
from app.ai.logging import ai_logger
from app.ai.orchestrator import should_use_rag
from app.mcp.tools.finance import FINANCE_TOOL_NAMES, finance_tools_for_message

ROUTE_SYSTEM = """You route finance chat messages. Reply with JSON only, no markdown.
Schema: {"tools": ["get_summary"|"list_transactions"|"get_budgets"|"get_spending_by_category"], "use_rag": boolean}

Tools:
- get_summary: balance, income, expenses, savings for the current month
- list_transactions: recent transactions for the current month
- get_spending_by_category: spending totals grouped by category this month
- get_budgets: monthly budget progress by category
- use_rag: true for analysis, trends, explanations, comparisons, advice, patterns, "why"

Rules:
- Any question about spending, income, balance, categories, or amounts MUST include at least one tool.
- Category questions (e.g. transport, food, rent) MUST include get_spending_by_category and list_transactions.
- Only return empty tools for greetings or clearly non-finance messages."""

VALID_TOOLS = set(FINANCE_TOOL_NAMES)


def _parse_route_response(text: str) -> tuple[list[str], bool] | None:
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if not match:
        return None

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return None

    raw_tools = data.get("tools", [])
    if not isinstance(raw_tools, list):
        return None

    tools = [tool for tool in raw_tools if isinstance(tool, str) and tool in VALID_TOOLS]
    use_rag = bool(data.get("use_rag", False))
    return tools, use_rag


def _keyword_fallback(message: str) -> tuple[list[str], bool]:
    return finance_tools_for_message(message), should_use_rag(message)


def _merge_routes(llm_tools: list[str], llm_rag: bool, message: str) -> tuple[list[str], bool]:
    keyword_tools, keyword_rag = _keyword_fallback(message)
    tools = list(dict.fromkeys(llm_tools + keyword_tools))
    use_rag = llm_rag or keyword_rag

    if keyword_tools and not llm_tools:
        ai_logger.info("route keyword supplement tools=%s rag=%s", tools, use_rag)
    elif keyword_tools:
        added = [tool for tool in keyword_tools if tool not in llm_tools]
        if added:
            ai_logger.info("route keyword merge added=%s", added)

    return tools, use_rag


async def route_message(message: str, locale: str) -> tuple[list[str], bool]:
    keyword_tools, keyword_rag = _keyword_fallback(message)

    if not await ollama_client.is_available():
        ai_logger.info("route fallback (ollama offline) tools=%s rag=%s", keyword_tools, keyword_rag)
        return keyword_tools, keyword_rag

    user_prompt = f"Locale: {locale}\nUser message: {message}"
    try:
        raw = await ollama_client.generate(ROUTE_SYSTEM, user_prompt, num_predict=80, temperature=0.0)
        parsed = _parse_route_response(raw)
        if parsed is not None:
            llm_tools, llm_rag = parsed
            tools, use_rag = _merge_routes(llm_tools, llm_rag, message)
            ai_logger.info("route llm tools=%s rag=%s", tools, use_rag)
            return tools, use_rag
    except (TimeoutError, RuntimeError) as exc:
        ai_logger.warning("route llm failed: %s", exc)

    ai_logger.info("route fallback (parse error) tools=%s rag=%s", keyword_tools, keyword_rag)
    return keyword_tools, keyword_rag
