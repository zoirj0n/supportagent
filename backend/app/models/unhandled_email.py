from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, text, String
from ..db import Base


class UnhandledEmail(Base):
    __tablename__ = "unhandled_emails"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    gmail_account_id: Mapped[str] = mapped_column(
        ForeignKey("gmail_account.id", ondelete="CASCADE")
    )
    email_msg_id: Mapped[str | None]
    thread_id: Mapped[str | None]
    reason: Mapped[str | None]
    importance: Mapped[str | None]
    created_at: Mapped[str] = mapped_column(server_default=text("now()"))
