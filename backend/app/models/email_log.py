from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, text, String, Boolean, DateTime
from ..db import Base


class EmailLog(Base):
    __tablename__ = "email_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    gmail_account_id: Mapped[str] = mapped_column(
        ForeignKey("gmail_account.id", ondelete="CASCADE")
    )
    gmail_msg_id: Mapped[str]
    thread_id: Mapped[str | None]
    from_email: Mapped[str | None]
    to_email: Mapped[str | None]
    subject: Mapped[str | None]
    snippet: Mapped[str | None]
    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    category: Mapped[str | None]
    order_id: Mapped[str | None]
    is_handled: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
