from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BankConnection(Base):
    __tablename__ = "bank_connections"
    __table_args__ = (
        UniqueConstraint("user_id", "bank", name="uq_bank_connections_user_bank"),
        UniqueConstraint("provider", "connection_id", name="uq_bank_connections_provider_connection"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    # e.g. "saltedge"
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="saltedge")
    # e.g. "revolut"
    bank: Mapped[str] = mapped_column(String(32), nullable=False, default="revolut")

    customer_id: Mapped[str] = mapped_column(String(64), nullable=False)
    connection_id: Mapped[str] = mapped_column(String(64), nullable=False)

    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

