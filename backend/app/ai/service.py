from collections.abc import AsyncIterator

from sqlalchemy.orm import Session

from app.ai.graph.agent import run_agent, run_agent_stream
from app.ai.tracing import chat_trace_context, span_kind, trace_span
from app.ai.types import ChatResult
from app.config import settings


async def run_chat(
    db: Session,
    user_id: int,
    user_email: str,
    message: str,
    locale: str = "ro",
) -> ChatResult:
    if not settings.ai_enabled:
        return ChatResult(
            reply="Modulul AI este dezactivat. Setează AI_ENABLED=true în .env.",
            model="disabled",
        )

    with chat_trace_context(user_id, locale, message):
        with trace_span("ai.chat", **span_kind("agent"), mode="sync"):
            return await run_agent(db, user_id, user_email, message, locale)


async def run_chat_stream(
    db: Session,
    user_id: int,
    user_email: str,
    message: str,
    locale: str = "ro",
) -> tuple[ChatResult, AsyncIterator[str]] | tuple[None, None]:
    if not settings.ai_enabled:
        return None, None

    state, stream = await run_agent_stream(db, user_id, user_email, message, locale)
    meta = ChatResult(
        reply="",
        used_tools=state.get("tools_used", []),
        used_rag=state.get("used_rag", False),
        model=settings.ollama_model if state.get("model") != "unavailable" else "unavailable",
    )
    return meta, stream
