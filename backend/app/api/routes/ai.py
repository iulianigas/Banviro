import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.logging import ai_logger
from app.ai.service import run_chat, run_chat_stream
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    locale: str = Field(default="ro", pattern=r"^(ro|en)$")


class ChatResponse(BaseModel):
    reply: str
    model: str
    used_tools: list[str]
    used_rag: bool


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    ai_logger.info("chat request user_id=%s chars=%d", current_user.id, len(payload.message))
    result = await run_chat(
        db,
        current_user.id,
        current_user.email,
        payload.message,
        payload.locale,
    )
    ai_logger.info(
        "chat response user_id=%s model=%s tools=%s rag=%s reply_chars=%d",
        current_user.id,
        result.model,
        result.used_tools,
        result.used_rag,
        len(result.reply),
    )
    return ChatResponse(
        reply=result.reply,
        model=result.model,
        used_tools=result.used_tools,
        used_rag=result.used_rag,
    )


@router.post("/chat/stream")
async def chat_stream(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    ai_logger.info(
        "chat stream request user_id=%s chars=%d",
        current_user.id,
        len(payload.message),
    )

    if not settings.ai_enabled:
        disabled = ChatResponse(
            reply="Modulul AI este dezactivat. Setează AI_ENABLED=true în .env.",
            model="disabled",
            used_tools=[],
            used_rag=False,
        )

        async def disabled_stream() -> AsyncIterator[str]:
            yield _sse("meta", disabled.model_dump())
            yield _sse("token", {"content": disabled.reply})
            yield _sse("done", disabled.model_dump())

        return StreamingResponse(disabled_stream(), media_type="text/event-stream")

    meta, stream = await run_chat_stream(
        db,
        current_user.id,
        current_user.email,
        payload.message,
        payload.locale,
    )
    if meta is None or stream is None:
        raise RuntimeError("Streaming unavailable")

    async def event_stream() -> AsyncIterator[str]:
        yield _sse(
            "meta",
            {
                "model": meta.model,
                "used_tools": meta.used_tools,
                "used_rag": meta.used_rag,
            },
        )

        chunks: list[str] = []
        try:
            async for chunk in stream:
                chunks.append(chunk)
                yield _sse("token", {"content": chunk})
        except (TimeoutError, RuntimeError) as exc:
            ai_logger.error("chat stream failed user_id=%s: %s", current_user.id, exc)
            yield _sse("error", {"message": str(exc)})
            return

        reply = "".join(chunks)
        ai_logger.info(
            "chat stream done user_id=%s model=%s tools=%s rag=%s reply_chars=%d",
            current_user.id,
            meta.model,
            meta.used_tools,
            meta.used_rag,
            len(reply),
        )
        yield _sse(
            "done",
            {
                "reply": reply,
                "model": meta.model,
                "used_tools": meta.used_tools,
                "used_rag": meta.used_rag,
            },
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/status")
async def ai_status() -> dict[str, object]:
    from app.ai.llm.ollama import ollama_client
    from app.ai.rag.retriever import qdrant_retriever

    return {
        "ai_enabled": settings.ai_enabled,
        "ollama_available": await ollama_client.is_available(),
        "qdrant_available": await qdrant_retriever.is_available(),
        "model": settings.ollama_model,
        "embed_model": settings.ollama_embed_model,
        "agent": "langgraph",
        "streaming": True,
    }


class ReindexResponse(BaseModel):
    indexed: int


@router.post("/reindex", response_model=ReindexResponse)
async def reindex_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReindexResponse:
    from app.ai.rag.indexer import reindex_user_transactions

    if not settings.ai_enabled:
        return ReindexResponse(indexed=0)

    indexed = await reindex_user_transactions(db, current_user.id)
    return ReindexResponse(indexed=indexed)
