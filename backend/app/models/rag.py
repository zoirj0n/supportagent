from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import ARRAY
from ..db import Base


class RAGDocument(Base):
    __tablename__ = "rag_documents"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(String)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    created_at: Mapped[str] = mapped_column(server_default=text("now()"))
