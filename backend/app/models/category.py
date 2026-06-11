import enum

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CategoryType(str, enum.Enum):
    income = "income"
    expense = "expense"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[CategoryType] = mapped_column(Enum(CategoryType), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#64748b")
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")


from app.models.transaction import Transaction  # noqa: E402
