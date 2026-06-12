import json
import re

from app.ai.llm.ollama import ollama_client
from app.ai.logging import ai_logger
from app.ai.orchestrator import should_use_rag
from app.mcp.tools.finance import FINANCE_TOOL_NAMES, finance_tools_for_message

ROUTE_SYSTEM = """You route finance chat messages. Reply with JSON only, no markdown.
Schema: {"tools": ["get_summary"|"list_transactions"|"get_budgets"], "use_rag": boolean}

Tools:
- get_summary: balance, income, expenses, savings for the current month
- list_transactions: recent transaction list
- get_budgets: monthly budget progress by category
- use_rag: true for analysis, trends, explanations, comparisons, advice, patterns, "why"

If the message is a greeting or unrelated to finance, return {"tools": [], "use_rag": false}."""

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


async def route_message(message: str, locale: str) -> tuple[list[str], bool]:
    if not await ollama_client.is_available():
        tools, use_rag = _keyword_fallback(message)
        ai_logger.info("route fallback (ollama offline) tools=%s rag=%s", tools, use_rag)
        return tools, use_rag

    user_prompt = f"Locale: {locale}\nUser message: {message}"
    try:
        raw = await ollama_client.generate(ROUTE_SYSTEM, user_prompt, num_predict=80, temperature=0.0)
        parsed = _parse_route_response(raw)
        if parsed is not None:
            tools, use_rag = parsed
            ai_logger.info("route llm tools=%s rag=%s", tools, use_rag)
            return tools, use_rag
    except (TimeoutError, RuntimeError) as exc:
        ai_logger.warning("route llm failed: %s", exc)

    tools, use_rag = _keyword_fallback(message)
    ai_logger.info("route fallback (parse error) tools=%s rag=%s", tools, use_rag)
    return tools, use_rag
