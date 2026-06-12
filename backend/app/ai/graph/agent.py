from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.ai.llm.ollama import ollama_client
from app.ai.logging import ai_logger
from app.ai.orchestrator import should_use_rag
from app.ai.rag.retriever import qdrant_retriever
from app.ai.types import ChatResult
from app.config import settings
from app.mcp.tools.finance import execute_finance_tool, finance_tools_for_message

SYSTEM_PROMPT_RO = """Ești Banviro AI. Răspunde în română, scurt (max 3-4 propoziții).
Folosește DOAR cifrele din context. Nu inventa date."""

SYSTEM_PROMPT_EN = """You are Banviro AI. Reply in English, briefly (max 3-4 sentences).
Use ONLY figures from the context. Do not invent data."""


class AgentState(TypedDict):
    message: str
    locale: str
    user_id: int
    user_email: str
    summary_text: str
    recent_transactions: str
    budget_text: str
    rag_snippets: list[str]
    tools_used: list[str]
    used_rag: bool
    reply: str
    model: str
    error: str | None


def _get_db(config: RunnableConfig) -> Session:
    db = config.get("configurable", {}).get("db")
    if db is None:
        raise RuntimeError("Database session missing from graph config")
    return db


async def fetch_finance(state: AgentState, config: RunnableConfig) -> dict[str, object]:
    tool_names = finance_tools_for_message(state["message"])
    if not tool_names:
        return {}

    db = _get_db(config)
    tools_used = list(state.get("tools_used", []))
    summary_text = state.get("summary_text", "")
    recent_transactions = state.get("recent_transactions", "")
    budget_text = state.get("budget_text", "")

    for tool_name in tool_names:
        result = execute_finance_tool(tool_name, db, state["user_id"], state["locale"])
        tools_used.append(f"mcp:{tool_name}")
        if tool_name == "get_summary":
            summary_text = result
        elif tool_name == "list_transactions":
            recent_transactions = result
        elif tool_name == "get_budgets":
            budget_text = result

    ai_logger.info(
        "langgraph fetch_finance user_id=%s tools=%s",
        state["user_id"],
        tool_names,
    )
    return {
        "summary_text": summary_text,
        "recent_transactions": recent_transactions,
        "budget_text": budget_text,
        "tools_used": tools_used,
    }


async def fetch_rag(state: AgentState, config: RunnableConfig) -> dict[str, object]:
    _ = config
    if not should_use_rag(state["message"]):
        return {}

    snippets = await qdrant_retriever.search(state["message"], user_id=state["user_id"])
    if not snippets:
        return {}

    tools_used = list(state.get("tools_used", []))
    tools_used.append("qdrant_rag")
    ai_logger.info(
        "langgraph fetch_rag user_id=%s snippets=%d",
        state["user_id"],
        len(snippets),
    )
    return {
        "rag_snippets": snippets,
        "tools_used": tools_used,
        "used_rag": True,
    }


async def generate_reply(state: AgentState, config: RunnableConfig) -> dict[str, object]:
    _ = config
    if not await ollama_client.is_available():
        ai_logger.warning("ollama unavailable for user_id=%s", state["user_id"])
        return {
            "reply": (
                "Ollama nu rulează. Pornește: ollama serve\n"
                "Apoi: ollama pull llama3.2:1b"
            ),
            "model": "unavailable",
        }

    user_prompt = f"""Întrebare utilizator: {state["message"]}

Date financiare:
{state.get("summary_text") or "N/A"}

Tranzacții recente:
{state.get("recent_transactions") or "N/A"}

Bugete:
{state.get("budget_text") or "N/A"}

Context RAG:
{chr(10).join(state.get("rag_snippets", [])) or "N/A"}
"""
    system_prompt = SYSTEM_PROMPT_EN if state["locale"] == "en" else SYSTEM_PROMPT_RO

    try:
        reply = await ollama_client.generate(system_prompt, user_prompt)
    except (TimeoutError, RuntimeError) as exc:
        ai_logger.error("langgraph generate failed user_id=%s: %s", state["user_id"], exc)
        return {"reply": str(exc), "model": "error", "error": str(exc)}

    return {"reply": reply, "model": settings.ollama_model}


def build_agent_graph():
    builder = StateGraph(AgentState)
    builder.add_node("fetch_finance", fetch_finance)
    builder.add_node("fetch_rag", fetch_rag)
    builder.add_node("generate", generate_reply)
    builder.add_edge(START, "fetch_finance")
    builder.add_edge("fetch_finance", "fetch_rag")
    builder.add_edge("fetch_rag", "generate")
    builder.add_edge("generate", END)
    return builder.compile()


agent_graph = build_agent_graph()


def _initial_state(
    user_id: int,
    user_email: str,
    message: str,
    locale: str,
) -> AgentState:
    return AgentState(
        message=message,
        locale=locale,
        user_id=user_id,
        user_email=user_email,
        summary_text="",
        recent_transactions="",
        budget_text="",
        rag_snippets=[],
        tools_used=[],
        used_rag=False,
        reply="",
        model="",
        error=None,
    )


async def run_agent(
    db: Session,
    user_id: int,
    user_email: str,
    message: str,
    locale: str = "ro",
) -> ChatResult:
    final_state = await agent_graph.ainvoke(
        _initial_state(user_id, user_email, message, locale),
        config={"configurable": {"db": db}},
    )
    return ChatResult(
        reply=final_state["reply"],
        used_tools=final_state.get("tools_used", []),
        used_rag=final_state.get("used_rag", False),
        model=final_state.get("model", settings.ollama_model),
    )
