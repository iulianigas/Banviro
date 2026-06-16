from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BankCustomer(Base):
    __tablename__ = "bank_customers"
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_bank_customers_user_provider"),
        UniqueConstraint("provider", "customer_id", name="uq_bank_customers_provider_customer"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="saltedge")
    customer_id: Mapped[str] = mapped_column(String(64), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

