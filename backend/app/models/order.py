from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import text
from ..db import Base


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(primary_key=True)
    user_email: Mapped[str | None]
    status: Mapped[str] = mapped_column(server_default=text("'placed'"))
    created_at: Mapped[str] = mapped_column(server_default=text("now()"))
	