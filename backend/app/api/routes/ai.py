from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.logging import ai_logger
from app.ai.service import run_chat
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


@router.get("/status")
async def ai_status() -> dict[str, object]:
    from app.ai.llm.ollama import ollama_client
    from app.ai.rag.retriever import qdrant_retriever
    from app.config import settings

    return {
        "ai_enabled": settings.ai_enabled,
        "ollama_available": await ollama_client.is_available(),
        "qdrant_available": await qdrant_retriever.is_available(),
        "model": settings.ollama_model,
    }
