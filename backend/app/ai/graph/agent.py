from collections.abc import AsyncIterator
from typing import TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.ai.graph.router import route_message
from app.ai.llm.ollama import ollama_client
from app.ai.logging import ai_logger
from app.ai.rag.retriever import qdrant_retriever
from app.ai.tracing import record_io, span_kind, trace_span
from app.ai.types import ChatResult
from app.config import settings
from app.mcp.tools.finance import execute_finance_tool

SYSTEM_PROMPT_RO = """Ești Banviro AI, un advisor financiar personal.
Răspunde în română, clar și concis (max 3-4 propoziții).

Reguli stricte:
- Folosește DOAR cifrele care apar explicit în secțiunile de context de mai jos.
- Nu inventa, nu estima și nu recalcula sume care nu sunt în context.
- Dacă informația lipsește, spune că nu ai datele respective.
- Răspunde direct la întrebare; evită filler-ul."""

SYSTEM_PROMPT_EN = """You are Banviro AI, a personal finance advisor.
Reply in English, clearly and concisely (max 3-4 sentences).

Strict rules:
- Use ONLY numbers explicitly present in the context sections below.
- Do not invent, estimate, or recalculate figures not in the context.
- If information is missing, say you do not have that data.
- Answer the question directly; avoid filler."""


class AgentState(TypedDict):
    message: str
    locale: str
    user_id: int
    user_email: str
    planned_tools: list[str]
    plan_rag: bool
    summary_text: str
    recent_transactions: str
    budget_text: str
    category_spending_text: str
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


async def route_intent(state: AgentState, config: RunnableConfig) -> dict[str, object]:
    _ = config
    with trace_span(
        "agent.route_intent",
        **span_kind("chain"),
        user_id=state["user_id"],
    ) as span:
        record_io(span, input_value=state["message"])
        tools, use_rag = await route_message(state["message"], state["locale"])
        record_io(span, output_value=f"tools={tools}, rag={use_rag}")
        return {"planned_tools": tools, "plan_rag": use_rag}


async def fetch_finance(state: AgentState, config: RunnableConfig) -> dict[str, object]:
    tool_names = state.get("planned_tools", [])
    if not tool_names:
        return {}

    with trace_span(
        "agent.fetch_finance",
        **span_kind("tool"),
        user_id=state["user_id"],
        tools=",".join(tool_names),
    ) as span:
        db = _get_db(config)
        tools_used = list(state.get("tools_used", []))
        summary_text = state.get("summary_text", "")
        recent_transactions = state.get("recent_transactions", "")
        budget_text = state.get("budget_text", "")
        category_spending_text = state.get("category_spending_text", "")

        for tool_name in tool_names:
            result = execute_finance_tool(tool_name, db, state["user_id"], state["locale"])
            tools_used.append(f"mcp:{tool_name}")
            if tool_name == "get_summary":
                summary_text = result
            elif tool_name == "list_transactions":
                recent_transactions = result
            elif tool_name == "get_budgets":
                budget_text = result
            elif tool_name == "get_spending_by_category":
                category_spending_text = result

        ai_logger.info(
            "langgraph fetch_finance user_id=%s tools=%s",
            state["user_id"],
            tool_names,
        )
        record_io(
            span,
            output_value=summary_text or recent_transactions or budget_text or category_spending_text,
        )
        return {
            "summary_text": summary_text,
            "recent_transactions": recent_transactions,
            "budget_text": budget_text,
            "category_spending_text": category_spending_text,
            "tools_used": tools_used,
        }


async def fetch_rag(state: AgentState, config: RunnableConfig) -> dict[str, object]:
    _ = config
    if not state.get("plan_rag", False):
        return {}

    with trace_span(
        "agent.fetch_rag",
        **span_kind("retriever"),
        user_id=state["user_id"],
    ) as span:
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
        record_io(span, output_value="\n".join(snippets))
        return {
            "rag_snippets": snippets,
            "tools_used": tools_used,
            "used_rag": True,
        }


def _build_user_prompt(state: AgentState) -> str:
    rag_block = "\n".join(f"- {snippet}" for snippet in state.get("rag_snippets", []))
    question_label = "User question" if state["locale"] == "en" else "Întrebare utilizator"
    category_label = "Category spending" if state["locale"] == "en" else "Cheltuieli pe categorii"
    return f"""## Rezumat financiar
{state.get("summary_text") or "N/A"}

## {category_label}
{state.get("category_spending_text") or "N/A"}

## Tranzacții recente
{state.get("recent_transactions") or "N/A"}

## Bugete
{state.get("budget_text") or "N/A"}

## Context semantic (tranzacții relevante)
{rag_block or "N/A"}

## {question_label}
{state["message"]}"""


def _system_prompt(locale: str) -> str:
    return SYSTEM_PROMPT_EN if locale == "en" else SYSTEM_PROMPT_RO


async def generate_reply(state: AgentState, config: RunnableConfig) -> dict[str, object]:
    _ = config
    with trace_span(
        "agent.generate",
        **span_kind("agent"),
        user_id=state["user_id"],
        locale=state["locale"],
    ) as span:
        if not await ollama_client.is_available():
            ai_logger.warning("ollama unavailable for user_id=%s", state["user_id"])
            reply = (
                "Ollama nu rulează. Pornește: ollama serve\n"
                f"Apoi: ollama pull {settings.ollama_model}"
            )
            record_io(span, output_value=reply)
            return {"reply": reply, "model": "unavailable"}

        user_prompt = _build_user_prompt(state)
        system_prompt = _system_prompt(state["locale"])
        record_io(span, input_value=user_prompt)

        try:
            reply = await ollama_client.generate(system_prompt, user_prompt)
        except (TimeoutError, RuntimeError) as exc:
            ai_logger.error("langgraph generate failed user_id=%s: %s", state["user_id"], exc)
            return {"reply": str(exc), "model": "error", "error": str(exc)}

        record_io(span, output_value=reply)
        return {"reply": reply, "model": settings.ollama_model}


async def generate_reply_stream(state: AgentState) -> AsyncIterator[str]:
    user_prompt = _build_user_prompt(state)
    system_prompt = _system_prompt(state["locale"])
    async for chunk in ollama_client.generate_stream(system_prompt, user_prompt):
        yield chunk


def build_agent_graph():
    builder = StateGraph(AgentState)
    builder.add_node("route_intent", route_intent)
    builder.add_node("fetch_finance", fetch_finance)
    builder.add_node("fetch_rag", fetch_rag)
    builder.add_node("generate", generate_reply)
    builder.add_edge(START, "route_intent")
    builder.add_edge("route_intent", "fetch_finance")
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
        planned_tools=[],
        plan_rag=False,
        summary_text="",
        recent_transactions="",
        budget_text="",
        category_spending_text="",
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


async def prepare_agent_state(
    db: Session,
    user_id: int,
    user_email: str,
    message: str,
    locale: str = "ro",
) -> AgentState:
    state = _initial_state(user_id, user_email, message, locale)
    config: RunnableConfig = {"configurable": {"db": db}}
    state = {**state, **await route_intent(state, config)}
    state = {**state, **await fetch_finance(state, config)}
    state = {**state, **await fetch_rag(state, config)}
    return state


async def run_agent_stream(
    db: Session,
    user_id: int,
    user_email: str,
    message: str,
    locale: str = "ro",
) -> tuple[AgentState, AsyncIterator[str]]:
    state = await prepare_agent_state(db, user_id, user_email, message, locale)

    if not await ollama_client.is_available():
        state["reply"] = (
            "Ollama nu rulează. Pornește: ollama serve\n"
            f"Apoi: ollama pull {settings.ollama_model}"
        )
        state["model"] = "unavailable"

        async def unavailable_stream() -> AsyncIterator[str]:
            yield state["reply"]

        return state, unavailable_stream()

    return state, generate_reply_stream(state)
