from sqlalchemy.orm import Session

from app.ai.graph.agent import run_agent
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

    return await run_agent(db, user_id, user_email, message, locale)
