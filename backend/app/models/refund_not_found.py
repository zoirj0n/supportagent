from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, text, String
from ..db import Base

class RefundNotFound(Base):
    __tablename__ = "refund_requests_not_found"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    gmail_account_id: Mapped[str] = mapped_column(ForeignKey("gmail_account.id", ondelete="CASCADE"))
    thread_id: Mapped[str | None]
    email_msg_id: Mapped[str | None]
    provided_text: Mapped[str | None]
    created_at: Mapped[str] = mapped_column(server_default=text("now()"))
