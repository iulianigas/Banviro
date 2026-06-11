from sqlalchemy.orm import Session

from app.ai.logging import ai_logger
from app.ai.llm.ollama import ollama_client
from app.ai.orchestrator import build_context, should_use_rag
from app.ai.rag.retriever import qdrant_retriever
from app.ai.types import ChatResult
from app.config import settings

SYSTEM_PROMPT_RO = """Ești Banviro AI. Răspunde în română, scurt (max 3-4 propoziții).
Folosește DOAR cifrele din context. Nu inventa date."""

SYSTEM_PROMPT_EN = """You are Banviro AI. Reply in English, briefly (max 3-4 sentences).
Use ONLY figures from the context. Do not invent data."""


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

    context, tools_used = await build_context(db, user_id, user_email, message, locale)
    used_rag = False

    if should_use_rag(message):
        snippets = await qdrant_retriever.search(message)
        if snippets:
            context.rag_snippets = snippets
            used_rag = True
            tools_used.append("qdrant_rag")

    user_prompt = f"""Întrebare utilizator: {message}

Date financiare:
{context.summary_text or 'N/A'}

Tranzacții recente:
{context.recent_transactions or 'N/A'}

Context RAG:
{chr(10).join(context.rag_snippets) if context.rag_snippets else 'N/A'}
"""

    if not await ollama_client.is_available():
        ai_logger.warning("ollama unavailable for user_id=%s", user_id)
        return ChatResult(
            reply=(
                "Ollama nu rulează. Pornește: ollama serve\n"
                "Apoi: ollama pull llama3.2:1b"
            ),
            used_tools=tools_used,
            used_rag=used_rag,
            model="unavailable",
        )

    system_prompt = SYSTEM_PROMPT_EN if locale == "en" else SYSTEM_PROMPT_RO

    try:
        reply = await ollama_client.generate(system_prompt, user_prompt)
    except (TimeoutError, RuntimeError) as exc:
        ai_logger.error("chat failed user_id=%s: %s", user_id, exc)
        return ChatResult(
            reply=str(exc),
            used_tools=tools_used,
            used_rag=used_rag,
            model="error",
        )

    return ChatResult(
        reply=reply,
        used_tools=tools_used,
        used_rag=used_rag,
        model=settings.ollama_model,
    )
