from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.mcp.auth import resolve_mcp_user
from app.models.user import User


@dataclass(frozen=True)
class McpFinanceContext:
    db: Session
    user: User


@contextmanager
def mcp_finance_context():
    db = SessionLocal()
    try:
        user = resolve_mcp_user(db)
        yield McpFinanceContext(db=db, user=user)
    finally:
        db.close()
